"""Pruebas del motor de recomendación (asociación de cestas + respaldo por atributos)."""

from __future__ import annotations

from datetime import time, timedelta

import pytest

from src.models import Producto, Venta
from src.services import recomendacion as reco
from src.services.recomendacion import METODO_ASOCIACION, METODO_ATRIBUTOS, TOP_N, ErrorNegocio, Recomendacion


def _venta(fecha, producto_id, tienda_id=1, cliente_id=None, cantidad=1, precio=100.0):
    return Venta(fecha=fecha, hora=time(10, 0), tienda_id=tienda_id, producto_id=producto_id,
                 cantidad=cantidad, precio_unitario_bs=precio, cliente_id=cliente_id)


def test_recomendar_producto_no_existe(sesion):
    with pytest.raises(ErrorNegocio, match="no existe"):
        reco.recomendar(sesion, 999)


def test_generar_reglas_vacio_si_pocas_cestas(sesion, hoy):
    sesion.add(_venta(hoy, 1))
    sesion.flush()
    assert reco.generar_reglas(sesion).empty


def test_recomendar_usa_respaldo_por_atributos_cuando_no_hay_reglas(sesion, hoy):
    sesion.add_all([
        Producto(id=2, codigo_modelo="MAN-DEP-002", nombre="Zapatilla B", categoria="Deportivo", codigo_sa6=640412,
                 talla="40", color="Negro", precio_venta_bs=300.0, costo_bs=150.0),
        Producto(id=3, codigo_modelo="MAN-DEP-003", nombre="Zapatilla C", categoria="Deportivo", codigo_sa6=640413,
                 talla="41", color="Negro", precio_venta_bs=300.0, costo_bs=150.0),
        Producto(id=4, codigo_modelo="MAN-DEP-004", nombre="Zapatilla D", categoria="Deportivo", codigo_sa6=640414,
                 talla="42", color="Negro", precio_venta_bs=300.0, costo_bs=150.0),
        Producto(id=5, codigo_modelo="MAN-DEP-005", nombre="Zapatilla E (otro color)", categoria="Deportivo",
                 codigo_sa6=640415, talla="40", color="Rojo", precio_venta_bs=300.0, costo_bs=150.0),
        Producto(id=6, codigo_modelo="MAN-DEP-006", nombre="Zapatilla F (inactiva)", categoria="Deportivo",
                 codigo_sa6=640416, talla="40", color="Negro", precio_venta_bs=300.0, costo_bs=150.0, activo=False),
        Producto(id=7, codigo_modelo="MAN-CUE-001", nombre="Botin de cuero (otra categoría)", categoria="Cuero",
                 codigo_sa6=640417, talla="40", color="Negro", precio_venta_bs=300.0, costo_bs=150.0),
    ])
    sesion.flush()
    # Todas las ventas de popularidad caen en la misma cesta (misma fecha), para
    # mantener el total de cestas muy por debajo del mínimo exigido a las reglas de asociación.
    for _ in range(5):
        sesion.add(_venta(hoy, 2))
    for _ in range(3):
        sesion.add(_venta(hoy, 3))
    sesion.add(_venta(hoy, 4))
    for _ in range(10):
        sesion.add(_venta(hoy, 5))
    sesion.flush()

    assert reco.generar_reglas(sesion).empty
    recomendaciones = reco.recomendar(sesion, 1)
    assert [r.producto_id for r in recomendaciones] == [2, 3, 4]
    assert all(r.metodo == METODO_ATRIBUTOS for r in recomendaciones)


def test_recomendar_usa_reglas_de_asociacion_cuando_hay_suficientes_cestas(sesion, hoy):
    sesion.add(Producto(id=2, codigo_modelo="MAN-DEP-002", nombre="Zapatilla B", categoria="Deportivo",
                        codigo_sa6=640412, talla="41", color="Azul", precio_venta_bs=300.0, costo_bs=150.0))
    sesion.flush()
    for i in range(22):
        fecha = hoy - timedelta(days=i)
        sesion.add(_venta(fecha, 1))
        sesion.add(_venta(fecha, 2))
    sesion.flush()

    reglas = reco.generar_reglas(sesion)
    assert not reglas.empty

    recomendaciones = reco.recomendar(sesion, 1)
    assert len(recomendaciones) <= TOP_N
    primera = recomendaciones[0]
    assert primera.producto_id == 2
    assert primera.metodo == METODO_ASOCIACION
    assert primera.soporte == pytest.approx(1.0)
    assert primera.confianza == pytest.approx(1.0)
    assert primera.lift == pytest.approx(1.0)


def test_registrar_recomendacion_mostrada_y_marcar_aceptada(sesion):
    recomendacion = Recomendacion(producto_id=1, codigo="MAN-DEP-001", nombre="Zapatilla Runner",
                                  metodo=METODO_ATRIBUTOS)
    log = reco.registrar_recomendacion_mostrada(sesion, 1, recomendacion)
    assert log.aceptada is None

    actualizado = reco.marcar_aceptada(sesion, log.id)
    assert actualizado.aceptada is True

    with pytest.raises(ErrorNegocio, match="no existe"):
        reco.marcar_aceptada(sesion, 999)


def test_tasa_conversion_vacia_y_con_datos(sesion):
    vacio = reco.tasa_conversion(sesion)
    assert vacio.empty
    assert list(vacio.columns) == ["Método", "Mostradas", "Aceptadas", "Tasa de conversión"]

    rec = Recomendacion(producto_id=1, codigo="MAN-DEP-001", nombre="Zapatilla Runner", metodo=METODO_ASOCIACION)
    log1 = reco.registrar_recomendacion_mostrada(sesion, 1, rec)
    log2 = reco.registrar_recomendacion_mostrada(sesion, 1, rec)
    reco.marcar_aceptada(sesion, log1.id, aceptada=True)
    reco.marcar_aceptada(sesion, log2.id, aceptada=False)

    resumen = reco.tasa_conversion(sesion)
    fila = resumen.loc[resumen["Método"] == METODO_ASOCIACION].iloc[0]
    assert fila["Mostradas"] == 2
    assert fila["Aceptadas"] == 1
    assert fila["Tasa de conversión"] == 0.5
