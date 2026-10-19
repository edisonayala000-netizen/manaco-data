"""Pruebas del libro diario de partida doble."""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import select

from src.config import CUENTA_CAJA_BANCOS, CUENTA_CXP_PROVEEDORES, CUENTA_DESCUENTOS_VENTA, CUENTA_INVENTARIO
from src.services import contabilidad as cont
from src.services.contabilidad import ErrorNegocio, LineaAsiento


def test_sembrar_plan_cuentas_es_idempotente(sesion):
    cont.sembrar_plan_cuentas(sesion)
    cantidad = len(sesion.execute(select(cont.CuentaContable)).all())
    cont.sembrar_plan_cuentas(sesion)
    assert len(sesion.execute(select(cont.CuentaContable)).all()) == cantidad


def test_obtener_cuenta_falla_sin_sembrar(sesion):
    with pytest.raises(ErrorNegocio, match="no existe"):
        cont.obtener_cuenta(sesion, CUENTA_INVENTARIO)


def test_crear_asiento_exige_al_menos_una_linea(sesion, hoy):
    cont.sembrar_plan_cuentas(sesion)
    with pytest.raises(ErrorNegocio, match="al menos una línea"):
        cont.crear_asiento(sesion, hoy, "glosa", "MANUAL", [])


def test_crear_asiento_exige_cuadre(sesion, hoy):
    cont.sembrar_plan_cuentas(sesion)
    with pytest.raises(ErrorNegocio, match="no cuadra"):
        cont.crear_asiento(sesion, hoy, "Descuadrado", "MANUAL", [
            LineaAsiento(CUENTA_INVENTARIO, debe_bs=100.0),
            LineaAsiento(CUENTA_CXP_PROVEEDORES, haber_bs=50.0),
        ])


def test_crear_asiento_y_libro_diario(sesion, hoy):
    cont.sembrar_plan_cuentas(sesion)
    cont.crear_asiento(sesion, hoy, "Compra de mercadería", "COMPRA", [
        LineaAsiento(CUENTA_INVENTARIO, debe_bs=100.0),
        LineaAsiento(CUENTA_CXP_PROVEEDORES, haber_bs=100.0),
    ])
    diario = cont.libro_diario(sesion)
    assert len(diario) == 2
    assert set(diario["Cuenta"]) == {CUENTA_INVENTARIO, CUENTA_CXP_PROVEEDORES}

    balance = cont.balance_comprobacion(sesion)
    fila_inv = balance.loc[balance["Cuenta"] == CUENTA_INVENTARIO].iloc[0]
    fila_cxp = balance.loc[balance["Cuenta"] == CUENTA_CXP_PROVEEDORES].iloc[0]
    assert fila_inv["Saldo Bs"] == 100.0
    assert fila_cxp["Saldo Bs"] == -100.0


def test_libro_diario_filtra_por_rango_de_fechas(sesion, hoy):
    ayer = hoy - timedelta(days=1)
    cont.sembrar_plan_cuentas(sesion)
    cont.crear_asiento(sesion, ayer, "Ayer", "MANUAL",
                       [LineaAsiento(CUENTA_INVENTARIO, debe_bs=10.0), LineaAsiento(CUENTA_CXP_PROVEEDORES, haber_bs=10.0)])
    cont.crear_asiento(sesion, hoy, "Hoy", "MANUAL",
                       [LineaAsiento(CUENTA_INVENTARIO, debe_bs=20.0), LineaAsiento(CUENTA_CXP_PROVEEDORES, haber_bs=20.0)])
    solo_hoy = cont.libro_diario(sesion, desde=hoy, hasta=hoy)
    assert set(solo_hoy["Glosa"]) == {"Hoy"}


def test_registrar_descuento_promocion_crea_asiento(sesion, hoy):
    cont.sembrar_plan_cuentas(sesion)
    asiento = cont.registrar_descuento_promocion(sesion, hoy, 25.0, referencia_id=1)
    assert asiento is not None
    diario = cont.libro_diario(sesion)
    fila_desc = diario.loc[diario["Cuenta"] == CUENTA_DESCUENTOS_VENTA].iloc[0]
    fila_caja = diario.loc[diario["Cuenta"] == CUENTA_CAJA_BANCOS].iloc[0]
    assert fila_desc["Debe Bs"] == 25.0
    assert fila_caja["Haber Bs"] == 25.0


def test_registrar_descuento_promocion_ignora_monto_cero(sesion, hoy):
    cont.sembrar_plan_cuentas(sesion)
    assert cont.registrar_descuento_promocion(sesion, hoy, 0.0) is None
    assert cont.libro_diario(sesion).empty
