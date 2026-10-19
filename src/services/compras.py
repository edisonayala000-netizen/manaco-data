"""Inventario administrativo, proveedores y órdenes de compra.

Este módulo no depende de Streamlit. Mantiene un stock paralelo al de
apertura/cierre (``Inventario``) pensado para alertar cuando un producto baja
de su punto de reorden y para automatizar el costo de reposición cuando llega
una orden de compra. ``sincronizar_stock_tras_venta`` se llama explícitamente
desde la página de Ventas tras ``inventario.registrar_venta`` — no se usan
eventos ORM, para mantener la lógica fácil de rastrear y probar.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import ESTADO_OC_APROBADA, ESTADO_OC_BORRADOR, ESTADO_OC_RECIBIDA, ORIGEN_OC_ALERTA, ORIGEN_OC_MANUAL
from src.models import AlertaStock, DetalleOrdenCompra, Inventario, OrdenCompra, Producto, Proveedor, Tienda, Venta
from src.services import contabilidad

#: Pares pedidos por defecto en una orden de compra automática: llevar el stock
#: al doble del punto de reorden.
FACTOR_PEDIDO_AUTOMATICO = 2


class ErrorNegocio(Exception):
    """Una regla de negocio impide la operación. El mensaje es apto para el usuario."""


@dataclass(frozen=True)
class LineaCompra:
    """Una línea de producto y cantidad dentro de una orden de compra."""

    producto_id: int
    cantidad: int
    costo_unitario_bs: float


# --- Proveedores ---------------------------------------------------------------

def crear_proveedor(
    sesion: Session, nombre: str, razon_social: str = "", nit: str = "", telefono: str = "",
    email: str = "", pais: str = "Bolivia",
) -> Proveedor:
    if not nombre.strip():
        raise ErrorNegocio("El proveedor necesita un nombre.")
    proveedor = Proveedor(nombre=nombre.strip(), razon_social=razon_social, nit=nit,
                          telefono=telefono, email=email, pais=pais)
    sesion.add(proveedor)
    sesion.flush()
    return proveedor


def tabla_proveedores(sesion: Session, solo_activos: bool = False) -> pd.DataFrame:
    consulta = select(Proveedor)
    if solo_activos:
        consulta = consulta.where(Proveedor.activo.is_(True))
    filas = sesion.scalars(consulta.order_by(Proveedor.nombre)).all()
    return pd.DataFrame([
        {"id": p.id, "Nombre": p.nombre, "Razón social": p.razon_social, "NIT": p.nit,
         "Teléfono": p.telefono, "Email": p.email, "País": p.pais, "Activo": p.activo}
        for p in filas
    ])


# --- Inventario (stock paralelo con punto de reorden) --------------------------

def obtener_o_crear_inventario(
    sesion: Session, producto_id: int, tienda_id: int, stock_inicial: int = 0,
    stock_minimo: int = 0, punto_reorden: int = 0, proveedor_predeterminado_id: int | None = None,
) -> Inventario:
    registro = sesion.scalar(
        select(Inventario).where(Inventario.producto_id == producto_id, Inventario.tienda_id == tienda_id))
    if registro is None:
        registro = Inventario(
            producto_id=producto_id, tienda_id=tienda_id, stock_actual=stock_inicial,
            stock_minimo=stock_minimo, punto_reorden=punto_reorden,
            proveedor_predeterminado_id=proveedor_predeterminado_id,
        )
        sesion.add(registro)
        sesion.flush()
    return registro


def tabla_inventario(sesion: Session, tienda_id: int | None = None) -> pd.DataFrame:
    consulta = select(Inventario).join(Producto).join(Tienda)
    if tienda_id is not None:
        consulta = consulta.where(Inventario.tienda_id == tienda_id)
    filas = sesion.scalars(consulta.order_by(Tienda.nombre, Producto.codigo_modelo)).all()
    return pd.DataFrame([
        {"id": i.id, "Tienda": i.tienda.nombre, "Código": i.producto.codigo_modelo,
         "Producto": i.producto.nombre, "Stock actual": i.stock_actual, "Stock mínimo": i.stock_minimo,
         "Punto de reorden": i.punto_reorden, "En alerta": i.stock_actual <= i.punto_reorden}
        for i in filas
    ])


def sincronizar_stock_tras_venta(sesion: Session, venta: Venta) -> AlertaStock | None:
    """Descuenta la venta del inventario administrativo y evalúa la alerta de reorden.

    Si el producto todavía no tiene fila en ``Inventario`` para esa tienda no
    hace nada: ese producto aún no está bajo control de reorden automático.
    """
    registro = sesion.scalar(
        select(Inventario).where(
            Inventario.producto_id == venta.producto_id, Inventario.tienda_id == venta.tienda_id))
    if registro is None:
        return None
    registro.stock_actual -= venta.cantidad
    sesion.flush()
    return evaluar_alerta_stock(sesion, registro)


def evaluar_alerta_stock(sesion: Session, registro: Inventario) -> AlertaStock | None:
    """Crea una alerta (y, si hay proveedor predeterminado, una orden de compra en borrador)
    cuando ``stock_actual <= punto_reorden`` y no existe ya una alerta pendiente."""
    if registro.stock_actual > registro.punto_reorden:
        return None
    pendiente = sesion.scalar(
        select(AlertaStock).where(
            AlertaStock.producto_id == registro.producto_id, AlertaStock.tienda_id == registro.tienda_id,
            AlertaStock.atendida.is_(False)))
    if pendiente is not None:
        return pendiente

    alerta = AlertaStock(
        producto_id=registro.producto_id, tienda_id=registro.tienda_id,
        stock_actual=registro.stock_actual, punto_reorden=registro.punto_reorden,
    )
    sesion.add(alerta)
    sesion.flush()

    if registro.proveedor_predeterminado_id is not None:
        producto = sesion.get(Producto, registro.producto_id)
        cantidad = max(registro.punto_reorden * FACTOR_PEDIDO_AUTOMATICO - registro.stock_actual, 1)
        orden = crear_orden_compra(
            sesion, registro.proveedor_predeterminado_id, registro.tienda_id, date.today(),
            [LineaCompra(registro.producto_id, cantidad, producto.costo_bs)],
            origen=ORIGEN_OC_ALERTA,
        )
        alerta.orden_compra_id = orden.id
        sesion.flush()
    return alerta


def alertas_pendientes(sesion: Session) -> pd.DataFrame:
    filas = sesion.scalars(
        select(AlertaStock).join(Producto).join(Tienda)
        .where(AlertaStock.atendida.is_(False)).order_by(AlertaStock.fecha.desc())
    ).all()
    return pd.DataFrame([
        {"id": a.id, "Fecha": a.fecha, "Tienda": a.tienda.nombre, "Código": a.producto.codigo_modelo,
         "Producto": a.producto.nombre, "Stock actual": a.stock_actual, "Punto de reorden": a.punto_reorden,
         "Orden de compra": a.orden_compra_id}
        for a in filas
    ])


# --- Órdenes de compra -----------------------------------------------------------

def crear_orden_compra(
    sesion: Session, proveedor_id: int, tienda_id: int, fecha_emision: date, lineas: list[LineaCompra],
    creado_por: int | None = None, origen: str = ORIGEN_OC_MANUAL,
) -> OrdenCompra:
    if not lineas:
        raise ErrorNegocio("La orden de compra necesita al menos una línea de producto.")
    subtotal = round(sum(l.cantidad * l.costo_unitario_bs for l in lineas), 2)
    orden = OrdenCompra(
        proveedor_id=proveedor_id, tienda_id=tienda_id, fecha_emision=fecha_emision,
        estado=ESTADO_OC_BORRADOR, origen=origen, subtotal_bs=subtotal, total_bs=subtotal,
        creado_por=creado_por,
    )
    sesion.add(orden)
    sesion.flush()
    for linea in lineas:
        sesion.add(DetalleOrdenCompra(
            orden_compra_id=orden.id, producto_id=linea.producto_id,
            cantidad=linea.cantidad, costo_unitario_bs=linea.costo_unitario_bs,
        ))
    sesion.flush()
    return orden


def aprobar_orden_compra(sesion: Session, orden_id: int) -> OrdenCompra:
    orden = sesion.get(OrdenCompra, orden_id)
    if orden is None:
        raise ErrorNegocio("La orden de compra no existe.")
    if orden.estado != ESTADO_OC_BORRADOR:
        raise ErrorNegocio(f"Solo se puede aprobar una orden en borrador (estado actual: {orden.estado}).")
    orden.estado = ESTADO_OC_APROBADA
    sesion.flush()
    return orden


def recibir_orden_compra(
    sesion: Session, orden_id: int, fecha_recepcion: date, flete_bs: float = 0.0, arancel_bs: float = 0.0,
) -> OrdenCompra:
    """Recibe la orden completa: recalcula el costo con flete y arancel prorrateados,
    aumenta el stock, actualiza el costo del producto y genera el asiento contable."""
    orden = sesion.get(OrdenCompra, orden_id)
    if orden is None:
        raise ErrorNegocio("La orden de compra no existe.")
    if orden.estado != ESTADO_OC_APROBADA:
        raise ErrorNegocio(f"Solo se puede recibir una orden aprobada (estado actual: {orden.estado}).")
    if flete_bs < 0 or arancel_bs < 0:
        raise ErrorNegocio("El flete y el arancel no pueden ser negativos.")

    subtotal = round(sum(d.cantidad * d.costo_unitario_bs for d in orden.detalles), 2)
    gastos_adicionales = round(flete_bs + arancel_bs, 2)
    for detalle in orden.detalles:
        peso = (detalle.cantidad * detalle.costo_unitario_bs / subtotal) if subtotal > 0 else 0.0
        costo_landed_unitario = detalle.costo_unitario_bs + (gastos_adicionales * peso / detalle.cantidad
                                                              if detalle.cantidad else 0.0)
        detalle.cantidad_recibida = detalle.cantidad
        producto = sesion.get(Producto, detalle.producto_id)
        producto.costo_bs = round(costo_landed_unitario, 2)

        registro = obtener_o_crear_inventario(sesion, detalle.producto_id, orden.tienda_id)
        registro.stock_actual += detalle.cantidad

    orden.fecha_recepcion = fecha_recepcion
    orden.flete_bs = flete_bs
    orden.arancel_bs = arancel_bs
    orden.subtotal_bs = subtotal
    orden.total_bs = round(subtotal + gastos_adicionales, 2)
    orden.estado = ESTADO_OC_RECIBIDA
    sesion.flush()

    alertas_relacionadas = sesion.scalars(
        select(AlertaStock).where(AlertaStock.orden_compra_id == orden.id, AlertaStock.atendida.is_(False))
    ).all()
    for alerta in alertas_relacionadas:
        alerta.atendida = True

    contabilidad.registrar_recepcion_compra(sesion, orden)
    sesion.flush()
    return orden


def tabla_ordenes_compra(sesion: Session, estado: str | None = None) -> pd.DataFrame:
    consulta = select(OrdenCompra).join(Proveedor).join(Tienda)
    if estado is not None:
        consulta = consulta.where(OrdenCompra.estado == estado)
    filas = sesion.scalars(consulta.order_by(OrdenCompra.fecha_emision.desc())).all()
    return pd.DataFrame([
        {"id": o.id, "Fecha emisión": o.fecha_emision, "Fecha recepción": o.fecha_recepcion,
         "Proveedor": o.proveedor.nombre, "Tienda": o.tienda.nombre, "Estado": o.estado, "Origen": o.origen,
         "Subtotal Bs": o.subtotal_bs, "Flete Bs": o.flete_bs, "Arancel Bs": o.arancel_bs, "Total Bs": o.total_bs}
        for o in filas
    ])


def detalle_orden_compra(sesion: Session, orden_id: int) -> pd.DataFrame:
    orden = sesion.get(OrdenCompra, orden_id)
    if orden is None:
        raise ErrorNegocio("La orden de compra no existe.")
    return pd.DataFrame([
        {"Código": d.producto.codigo_modelo, "Producto": d.producto.nombre, "Cantidad": d.cantidad,
         "Costo unitario Bs": d.costo_unitario_bs, "Cantidad recibida": d.cantidad_recibida}
        for d in orden.detalles
    ])
