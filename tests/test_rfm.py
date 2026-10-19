"""Pruebas de segmentación RFM (Recencia, Frecuencia, Monto)."""

from __future__ import annotations

from datetime import time, timedelta

import pytest

from src.config import SEGMENTO_FRECUENTE, SEGMENTO_INACTIVO, SEGMENTO_NUEVO, SEGMENTO_RIESGO, SEGMENTO_VIP
from src.models import Cliente, Venta
from src.services import rfm


def _venta(fecha, cliente_id, cantidad=1, precio=100.0, descuento=0.0):
    return Venta(fecha=fecha, hora=time(10, 0), tienda_id=1, producto_id=1, cantidad=cantidad,
                 precio_unitario_bs=precio, descuento_bs=descuento, cliente_id=cliente_id)


@pytest.mark.parametrize(("score_r", "score_f", "score_m", "esperado"), [
    (5, 1, 3, SEGMENTO_NUEVO),
    (5, 5, 5, SEGMENTO_VIP),
    (1, 3, 1, SEGMENTO_RIESGO),
    (1, 1, 1, SEGMENTO_INACTIVO),
    (3, 3, 3, SEGMENTO_FRECUENTE),
])
def test_clasificar_segmento(score_r, score_f, score_m, esperado):
    assert rfm.clasificar_segmento(score_r, score_f, score_m) == esperado


def test_calcular_rfm_vacio_sin_ventas(sesion, hoy):
    resultado = rfm.calcular_rfm(sesion, hoy)
    assert resultado.empty
    assert list(resultado.columns) == [
        "cliente_id", "recencia_dias", "frecuencia", "monto_total_bs", "score_r", "score_f", "score_m", "segmento",
    ]


def test_calcular_rfm_ignora_ventas_sin_cliente(sesion, hoy):
    sesion.add(_venta(hoy, cliente_id=None))
    sesion.flush()
    assert rfm.calcular_rfm(sesion, hoy).empty


def test_calcular_rfm_metricas_basicas(sesion, hoy):
    cliente_a = Cliente(nombre="Cliente A")
    cliente_b = Cliente(nombre="Cliente B")
    sesion.add_all([cliente_a, cliente_b])
    sesion.flush()

    sesion.add_all([
        _venta(hoy - timedelta(days=10), cliente_a.id),
        _venta(hoy - timedelta(days=5), cliente_a.id),
        _venta(hoy - timedelta(days=1), cliente_a.id),
        _venta(hoy - timedelta(days=20), cliente_b.id, cantidad=2, precio=50.0),
    ])
    sesion.flush()

    resumen = rfm.calcular_rfm(sesion, hoy)
    fila_a = resumen.loc[resumen["cliente_id"] == cliente_a.id].iloc[0]
    fila_b = resumen.loc[resumen["cliente_id"] == cliente_b.id].iloc[0]

    assert fila_a["frecuencia"] == 3
    assert fila_a["monto_total_bs"] == 300.0
    assert fila_a["recencia_dias"] == 1
    assert fila_b["frecuencia"] == 1
    assert fila_b["monto_total_bs"] == 100.0
    assert fila_b["recencia_dias"] == 20

    # Cliente A compra más seguido, más reciente y gasta más: sus puntajes no
    # pueden ser peores que los de B (exactos son frágiles con solo 2 clientes).
    assert fila_a["score_r"] >= fila_b["score_r"]
    assert fila_a["score_f"] >= fila_b["score_f"]
    assert fila_a["score_m"] >= fila_b["score_m"]


def test_actualizar_perfiles_rfm_persiste_y_no_duplica(sesion, hoy):
    cliente = Cliente(nombre="Cliente A")
    sesion.add(cliente)
    sesion.flush()
    sesion.add(_venta(hoy, cliente.id))
    sesion.flush()

    rfm.actualizar_perfiles_rfm(sesion, hoy)
    tabla = rfm.tabla_segmentos(sesion)
    assert len(tabla) == 1

    rfm.actualizar_perfiles_rfm(sesion, hoy)
    tabla = rfm.tabla_segmentos(sesion)
    assert len(tabla) == 1


def test_tabla_segmentos_y_resumen_segmentos(sesion, hoy):
    cliente_a = Cliente(nombre="Cliente A")
    cliente_b = Cliente(nombre="Cliente B")
    sesion.add_all([cliente_a, cliente_b])
    sesion.flush()
    sesion.add_all([
        _venta(hoy, cliente_a.id, cantidad=5, precio=200.0),
        _venta(hoy - timedelta(days=60), cliente_b.id, cantidad=1, precio=10.0),
    ])
    sesion.flush()

    rfm.actualizar_perfiles_rfm(sesion, hoy)
    tabla = rfm.tabla_segmentos(sesion)
    assert set(tabla["Cliente"]) == {"Cliente A", "Cliente B"}
    assert {"Segmento", "Recencia (días)", "Frecuencia", "Monto total Bs", "R", "F", "M"}.issubset(tabla.columns)

    resumen = rfm.resumen_segmentos(sesion)
    assert resumen["Clientes"].sum() == 2
    assert float(resumen["Monto total Bs"].sum()) == 1010.0
