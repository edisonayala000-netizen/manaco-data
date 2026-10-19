"""Pruebas de proveedores, inventario con punto de reorden y órdenes de compra."""

from __future__ import annotations

from datetime import time

import pytest

from src.config import ESTADO_OC_APROBADA, ESTADO_OC_BORRADOR, ESTADO_OC_RECIBIDA, ORIGEN_OC_ALERTA
from src.models import Producto, Venta
from src.services import compras, contabilidad
from src.services.compras import ErrorNegocio, LineaCompra


def test_crear_proveedor_exige_nombre(sesion):
    with pytest.raises(ErrorNegocio, match="nombre"):
        compras.crear_proveedor(sesion, "   ")


def test_crear_proveedor_y_tabla_proveedores(sesion):
    compras.crear_proveedor(sesion, "Calzados del Sur", nit="123")
    tabla = compras.tabla_proveedores(sesion)
    assert list(tabla["Nombre"]) == ["Calzados del Sur"]
    assert tabla.iloc[0]["NIT"] == "123"


def test_obtener_o_crear_inventario_es_idempotente(sesion):
    primero = compras.obtener_o_crear_inventario(sesion, 1, 1, stock_inicial=20, stock_minimo=5, punto_reorden=10)
    segundo = compras.obtener_o_crear_inventario(sesion, 1, 1, stock_inicial=99, stock_minimo=99, punto_reorden=99)
    assert primero.id == segundo.id
    assert segundo.stock_actual == 20


def test_tabla_inventario_marca_en_alerta(sesion):
    compras.obtener_o_crear_inventario(sesion, 1, 1, stock_inicial=5, stock_minimo=2, punto_reorden=10)
    tabla = compras.tabla_inventario(sesion)
    assert bool(tabla.iloc[0]["En alerta"]) is True


def test_evaluar_alerta_stock_no_crea_si_stock_sobra(sesion):
    registro = compras.obtener_o_crear_inventario(sesion, 1, 1, stock_inicial=50, stock_minimo=5, punto_reorden=10)
    assert compras.evaluar_alerta_stock(sesion, registro) is None


def test_evaluar_alerta_stock_crea_alerta_y_evita_duplicados(sesion):
    registro = compras.obtener_o_crear_inventario(sesion, 1, 1, stock_inicial=5, stock_minimo=2, punto_reorden=10)
    alerta = compras.evaluar_alerta_stock(sesion, registro)
    assert alerta is not None
    assert alerta.orden_compra_id is None
    otra = compras.evaluar_alerta_stock(sesion, registro)
    assert otra.id == alerta.id
    assert len(compras.alertas_pendientes(sesion)) == 1


def test_evaluar_alerta_stock_crea_orden_automatica_con_proveedor(sesion):
    proveedor = compras.crear_proveedor(sesion, "Importadora Andina")
    registro = compras.obtener_o_crear_inventario(
        sesion, 1, 1, stock_inicial=5, stock_minimo=2, punto_reorden=10,
        proveedor_predeterminado_id=proveedor.id)
    alerta = compras.evaluar_alerta_stock(sesion, registro)
    assert alerta.orden_compra_id is not None
    ordenes = compras.tabla_ordenes_compra(sesion)
    orden = ordenes.loc[ordenes["id"] == alerta.orden_compra_id].iloc[0]
    assert orden["Estado"] == ESTADO_OC_BORRADOR
    assert orden["Origen"] == ORIGEN_OC_ALERTA
    detalle = compras.detalle_orden_compra(sesion, alerta.orden_compra_id)
    assert detalle.iloc[0]["Cantidad"] == 15  # 10*2 - 5


def test_sincronizar_stock_tras_venta_sin_inventario_no_hace_nada(sesion, hoy):
    venta = Venta(fecha=hoy, hora=time(10, 0), producto_id=1, tienda_id=1, cantidad=3, precio_unitario_bs=389.0)
    sesion.add(venta)
    sesion.flush()
    assert compras.sincronizar_stock_tras_venta(sesion, venta) is None


def test_sincronizar_stock_tras_venta_descuenta_y_alerta(sesion, hoy):
    compras.obtener_o_crear_inventario(sesion, 1, 1, stock_inicial=12, stock_minimo=2, punto_reorden=10)
    venta = Venta(fecha=hoy, hora=time(10, 0), producto_id=1, tienda_id=1, cantidad=5, precio_unitario_bs=389.0)
    sesion.add(venta)
    sesion.flush()
    alerta = compras.sincronizar_stock_tras_venta(sesion, venta)
    assert alerta is not None
    registro = compras.obtener_o_crear_inventario(sesion, 1, 1)
    assert registro.stock_actual == 7


def test_crear_orden_compra_exige_lineas(sesion, hoy):
    proveedor = compras.crear_proveedor(sesion, "Cueros Illimani")
    with pytest.raises(ErrorNegocio, match="al menos una línea"):
        compras.crear_orden_compra(sesion, proveedor.id, 1, hoy, [])


def test_aprobar_orden_compra_requiere_existir_y_estado_borrador(sesion, hoy):
    with pytest.raises(ErrorNegocio, match="no existe"):
        compras.aprobar_orden_compra(sesion, 999)
    proveedor = compras.crear_proveedor(sesion, "Cueros Illimani")
    orden = compras.crear_orden_compra(sesion, proveedor.id, 1, hoy, [LineaCompra(1, 10, 20.0)])
    compras.aprobar_orden_compra(sesion, orden.id)
    with pytest.raises(ErrorNegocio, match="borrador"):
        compras.aprobar_orden_compra(sesion, orden.id)


def test_recibir_orden_compra_requiere_estado_aprobada(sesion, hoy):
    proveedor = compras.crear_proveedor(sesion, "Cueros Illimani")
    orden = compras.crear_orden_compra(sesion, proveedor.id, 1, hoy, [LineaCompra(1, 10, 20.0)])
    with pytest.raises(ErrorNegocio, match="aprobada"):
        compras.recibir_orden_compra(sesion, orden.id, hoy)


def test_recibir_orden_compra_rechaza_flete_o_arancel_negativos(sesion, hoy):
    contabilidad.sembrar_plan_cuentas(sesion)
    proveedor = compras.crear_proveedor(sesion, "Cueros Illimani")
    orden = compras.crear_orden_compra(sesion, proveedor.id, 1, hoy, [LineaCompra(1, 10, 20.0)])
    compras.aprobar_orden_compra(sesion, orden.id)
    with pytest.raises(ErrorNegocio, match="negativos"):
        compras.recibir_orden_compra(sesion, orden.id, hoy, flete_bs=-1.0)


def test_recibir_orden_compra_prorratea_flete_y_actualiza_costo_y_stock(sesion, hoy):
    contabilidad.sembrar_plan_cuentas(sesion)
    proveedor = compras.crear_proveedor(sesion, "Cueros Illimani")
    orden = compras.crear_orden_compra(sesion, proveedor.id, 1, hoy, [LineaCompra(1, 10, 20.0)])
    compras.aprobar_orden_compra(sesion, orden.id)
    recibida = compras.recibir_orden_compra(sesion, orden.id, hoy, flete_bs=20.0)

    assert recibida.estado == ESTADO_OC_RECIBIDA
    assert recibida.total_bs == 220.0

    producto = sesion.get(Producto, 1)
    assert producto.costo_bs == 22.0

    registro = compras.obtener_o_crear_inventario(sesion, 1, 1)
    assert registro.stock_actual == 10

    diario = contabilidad.libro_diario(sesion)
    assert float(diario["Debe Bs"].sum()) == 220.0
    assert float(diario["Haber Bs"].sum()) == 220.0


def test_recibir_orden_compra_marca_alertas_relacionadas_como_atendidas(sesion, hoy):
    contabilidad.sembrar_plan_cuentas(sesion)
    proveedor = compras.crear_proveedor(sesion, "Cueros Illimani")
    registro = compras.obtener_o_crear_inventario(
        sesion, 1, 1, stock_inicial=5, stock_minimo=2, punto_reorden=10,
        proveedor_predeterminado_id=proveedor.id)
    alerta = compras.evaluar_alerta_stock(sesion, registro)
    assert alerta.atendida is False

    compras.aprobar_orden_compra(sesion, alerta.orden_compra_id)
    compras.recibir_orden_compra(sesion, alerta.orden_compra_id, hoy)

    assert alerta.atendida is True


def test_detalle_orden_compra_no_encontrada(sesion):
    with pytest.raises(ErrorNegocio, match="no existe"):
        compras.detalle_orden_compra(sesion, 999)
