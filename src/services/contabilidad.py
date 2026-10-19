"""Contabilidad mínima: plan de cuentas y asientos de partida doble.

Este módulo no depende de Streamlit. Expone ``crear_asiento`` como único punto
de entrada para registrar movimientos — valida que debe y haber cuadren antes
de guardar, y lo usan las integraciones automáticas de compras (módulo de
inventario) y de descuentos promocionales (módulo de marketing).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import CUENTA_CAJA_BANCOS, CUENTA_CXP_PROVEEDORES, CUENTA_DESCUENTOS_VENTA, CUENTA_INVENTARIO, PLAN_CUENTAS_BASE
from src.models import AsientoContable, CuentaContable, DetalleAsiento, OrdenCompra

TOLERANCIA_CUADRE = 0.01


class ErrorNegocio(Exception):
    """Una regla contable impide la operación. El mensaje es apto para el usuario."""


@dataclass(frozen=True)
class LineaAsiento:
    """Un movimiento de debe o haber dentro de un asiento."""

    codigo_cuenta: str
    debe_bs: float = 0.0
    haber_bs: float = 0.0


def sembrar_plan_cuentas(sesion: Session) -> None:
    """Crea las cuentas de ``PLAN_CUENTAS_BASE`` que todavía no existen (idempotente)."""
    existentes = {c.codigo for c in sesion.scalars(select(CuentaContable))}
    for codigo, nombre, tipo, naturaleza in PLAN_CUENTAS_BASE:
        if codigo not in existentes:
            sesion.add(CuentaContable(codigo=codigo, nombre=nombre, tipo=tipo, naturaleza=naturaleza))
    sesion.flush()


def obtener_cuenta(sesion: Session, codigo: str) -> CuentaContable:
    """Busca una cuenta por código; falla si el plan de cuentas no fue sembrado."""
    cuenta = sesion.scalar(select(CuentaContable).where(CuentaContable.codigo == codigo))
    if cuenta is None:
        raise ErrorNegocio(f"La cuenta contable {codigo} no existe. Ejecute sembrar_plan_cuentas primero.")
    return cuenta


def crear_asiento(
    sesion: Session, fecha: date, glosa: str, origen: str, lineas: list[LineaAsiento],
    referencia_tipo: str = "", referencia_id: int | None = None,
) -> AsientoContable:
    """Registra un asiento del libro diario. Falla si debe y haber no cuadran.

    Ejemplo: recepción de una orden de compra por 1000 Bs →
    ``[LineaAsiento(CUENTA_INVENTARIO, debe_bs=1000), LineaAsiento(CUENTA_CXP_PROVEEDORES, haber_bs=1000)]``.
    """
    if not lineas:
        raise ErrorNegocio("Un asiento contable necesita al menos una línea de debe y una de haber.")
    total_debe = round(sum(l.debe_bs for l in lineas), 2)
    total_haber = round(sum(l.haber_bs for l in lineas), 2)
    if abs(total_debe - total_haber) > TOLERANCIA_CUADRE:
        raise ErrorNegocio(
            f"El asiento no cuadra: debe {total_debe:.2f} Bs ≠ haber {total_haber:.2f} Bs.")

    asiento = AsientoContable(
        fecha=fecha, glosa=glosa, origen=origen,
        referencia_tipo=referencia_tipo, referencia_id=referencia_id,
    )
    sesion.add(asiento)
    sesion.flush()
    for linea in lineas:
        cuenta = obtener_cuenta(sesion, linea.codigo_cuenta)
        sesion.add(DetalleAsiento(
            asiento_id=asiento.id, cuenta_id=cuenta.id, debe_bs=linea.debe_bs, haber_bs=linea.haber_bs,
        ))
    sesion.flush()
    return asiento


def registrar_recepcion_compra(sesion: Session, orden: OrdenCompra) -> AsientoContable:
    """Asiento automático al recibir una orden de compra: Debe Inventario, Haber Cuentas por pagar."""
    return crear_asiento(
        sesion, orden.fecha_recepcion or orden.fecha_emision,
        f"Recepción de orden de compra #{orden.id}", "COMPRA",
        [
            LineaAsiento(CUENTA_INVENTARIO, debe_bs=orden.total_bs),
            LineaAsiento(CUENTA_CXP_PROVEEDORES, haber_bs=orden.total_bs),
        ],
        referencia_tipo="orden_compra", referencia_id=orden.id,
    )


def registrar_descuento_promocion(
    sesion: Session, fecha: date, descuento_bs: float, referencia_id: int | None = None,
) -> AsientoContable | None:
    """Asiento automático de un descuento aplicado: Debe Descuentos sobre ventas, Haber Caja y bancos.

    Sin este asiento el descuento quedaría fuera del libro diario y el efectivo
    cobrado no explicaría la diferencia frente al precio de lista.
    """
    if descuento_bs <= 0:
        return None
    return crear_asiento(
        sesion, fecha, "Descuento aplicado por promoción", "PROMOCION",
        [
            LineaAsiento(CUENTA_DESCUENTOS_VENTA, debe_bs=descuento_bs),
            LineaAsiento(CUENTA_CAJA_BANCOS, haber_bs=descuento_bs),
        ],
        referencia_tipo="conversion_campana", referencia_id=referencia_id,
    )


def libro_diario(sesion: Session, desde: date | None = None, hasta: date | None = None) -> pd.DataFrame:
    """Tabla plana de asientos y sus líneas de debe/haber, para mostrar o exportar."""
    consulta = (
        select(
            AsientoContable.fecha, AsientoContable.glosa, AsientoContable.origen,
            CuentaContable.codigo, CuentaContable.nombre, DetalleAsiento.debe_bs, DetalleAsiento.haber_bs,
        )
        .join(DetalleAsiento, DetalleAsiento.asiento_id == AsientoContable.id)
        .join(CuentaContable, CuentaContable.id == DetalleAsiento.cuenta_id)
        .order_by(AsientoContable.fecha, AsientoContable.id)
    )
    if desde is not None:
        consulta = consulta.where(AsientoContable.fecha >= desde)
    if hasta is not None:
        consulta = consulta.where(AsientoContable.fecha <= hasta)
    filas = sesion.execute(consulta).all()
    return pd.DataFrame(
        filas, columns=["Fecha", "Glosa", "Origen", "Cuenta", "Nombre cuenta", "Debe Bs", "Haber Bs"],
    )


def balance_comprobacion(sesion: Session) -> pd.DataFrame:
    """Suma de debe y haber por cuenta, para verificar que el libro diario cuadra."""
    diario = libro_diario(sesion)
    if diario.empty:
        return pd.DataFrame(columns=["Cuenta", "Nombre cuenta", "Debe Bs", "Haber Bs", "Saldo Bs"])
    resumen = diario.groupby(["Cuenta", "Nombre cuenta"], as_index=False)[["Debe Bs", "Haber Bs"]].sum()
    resumen["Saldo Bs"] = resumen["Debe Bs"] - resumen["Haber Bs"]
    return resumen
