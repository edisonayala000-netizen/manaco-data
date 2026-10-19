"""Pruebas de reglas de promoción (carrito) y campañas de marketing con cupón/UTM."""

from __future__ import annotations

from datetime import timedelta

import pytest

from src.services import contabilidad, promociones as promo
from src.services.promociones import ErrorNegocio, ItemCarrito


# --- Reglas de promoción: validaciones ------------------------------------------

def test_crear_regla_promocion_tipo_invalido(sesion, hoy):
    with pytest.raises(ErrorNegocio, match="inválido"):
        promo.crear_regla_promocion(sesion, "x", "NO_EXISTE", hoy, categoria="Deportivo")


def test_crear_regla_promocion_exige_producto_o_categoria(sesion, hoy):
    with pytest.raises(ErrorNegocio, match="producto o una categoría"):
        promo.crear_regla_promocion(sesion, "x", "PORCENTAJE", hoy, valor=10.0)


def test_crear_regla_promocion_porcentaje_fuera_de_rango(sesion, hoy):
    with pytest.raises(ErrorNegocio, match="entre 0 y 100"):
        promo.crear_regla_promocion(sesion, "x", "PORCENTAJE", hoy, valor=150.0, categoria="Deportivo")
    with pytest.raises(ErrorNegocio, match="entre 0 y 100"):
        promo.crear_regla_promocion(sesion, "x", "PORCENTAJE", hoy, valor=0.0, categoria="Deportivo")


def test_crear_regla_promocion_monto_fijo_debe_ser_positivo(sesion, hoy):
    with pytest.raises(ErrorNegocio, match="mayor a 0"):
        promo.crear_regla_promocion(sesion, "x", "MONTO_FIJO", hoy, valor=0.0, categoria="Cuero")


def test_crear_regla_promocion_combo_exige_cantidades(sesion, hoy):
    with pytest.raises(ErrorNegocio, match="cantidad necesaria y cantidad gratis"):
        promo.crear_regla_promocion(sesion, "x", "COMBO_ESPECIAL", hoy, categoria="Caucho")
    with pytest.raises(ErrorNegocio, match="menos que"):
        promo.crear_regla_promocion(sesion, "x", "COMBO_ESPECIAL", hoy, categoria="Caucho",
                                    cantidad_necesaria=2, cantidad_gratis=2)


def test_crear_regla_promocion_fecha_fin_antes_de_inicio(sesion, hoy):
    with pytest.raises(ErrorNegocio, match="fecha de fin"):
        promo.crear_regla_promocion(sesion, "x", "PORCENTAJE", hoy, valor=10.0, categoria="Deportivo",
                                    fecha_fin=hoy - timedelta(days=1))


def test_crear_regla_promocion_exitosa(sesion, hoy):
    regla = promo.crear_regla_promocion(sesion, "Descuento Deportivo", "PORCENTAJE", hoy, valor=10.0,
                                        categoria="Deportivo")
    tabla = promo.tabla_reglas_promocion(sesion)
    assert tabla.iloc[0]["Nombre"] == "Descuento Deportivo"
    assert regla.activa is True


# --- evaluar_carrito ---------------------------------------------------------------

def test_evaluar_carrito_vacio(sesion, hoy):
    with pytest.raises(ErrorNegocio, match="vacío"):
        promo.evaluar_carrito(sesion, [], fecha=hoy)


def test_evaluar_carrito_porcentaje(sesion, hoy):
    regla = promo.crear_regla_promocion(sesion, "Descuento Deportivo", "PORCENTAJE", hoy, valor=10.0,
                                        categoria="Deportivo")
    items = [ItemCarrito(producto_id=1, cantidad=2, precio_unitario_bs=100.0, categoria="Deportivo")]
    resultado = promo.evaluar_carrito(sesion, items, fecha=hoy)
    assert resultado.descuento_total_bs == 20.0
    assert resultado.reglas_aplicadas == [regla.id]


def test_evaluar_carrito_monto_fijo_exige_cantidad_minima(sesion, hoy):
    promo.crear_regla_promocion(sesion, "Rebaja Cuero", "MONTO_FIJO", hoy, valor=50.0, categoria="Cuero",
                                cantidad_necesaria=2)
    insuficiente = [ItemCarrito(producto_id=2, cantidad=1, precio_unitario_bs=300.0, categoria="Cuero")]
    assert promo.evaluar_carrito(sesion, insuficiente, fecha=hoy).descuento_total_bs == 0.0

    suficiente = [ItemCarrito(producto_id=2, cantidad=2, precio_unitario_bs=300.0, categoria="Cuero")]
    resultado = promo.evaluar_carrito(sesion, suficiente, fecha=hoy)
    assert resultado.descuento_total_bs == 50.0


def test_evaluar_carrito_combo_regala_las_unidades_mas_baratas(sesion, hoy):
    promo.crear_regla_promocion(sesion, "Combo 3x2", "COMBO_ESPECIAL", hoy, categoria="Caucho",
                                cantidad_necesaria=3, cantidad_gratis=1)
    items = [
        ItemCarrito(producto_id=3, cantidad=1, precio_unitario_bs=100.0, categoria="Caucho"),
        ItemCarrito(producto_id=4, cantidad=1, precio_unitario_bs=80.0, categoria="Caucho"),
        ItemCarrito(producto_id=5, cantidad=1, precio_unitario_bs=60.0, categoria="Caucho"),
    ]
    resultado = promo.evaluar_carrito(sesion, items, fecha=hoy)
    assert resultado.descuento_total_bs == 60.0  # se regala la unidad más barata


def test_evaluar_carrito_respeta_vigencia(sesion, hoy):
    promo.crear_regla_promocion(sesion, "Futura", "PORCENTAJE", hoy + timedelta(days=10), valor=10.0,
                                categoria="Deportivo")
    promo.crear_regla_promocion(sesion, "Vencida", "PORCENTAJE", hoy - timedelta(days=30), valor=10.0,
                                categoria="Deportivo", fecha_fin=hoy - timedelta(days=10))
    items = [ItemCarrito(producto_id=1, cantidad=1, precio_unitario_bs=100.0, categoria="Deportivo")]
    resultado = promo.evaluar_carrito(sesion, items, fecha=hoy)
    assert resultado.descuento_total_bs == 0.0


def test_evaluar_carrito_cupon_invalido(sesion, hoy):
    items = [ItemCarrito(producto_id=1, cantidad=1, precio_unitario_bs=100.0, categoria="Deportivo")]
    with pytest.raises(ErrorNegocio, match="no existe o ya no está activo"):
        promo.evaluar_carrito(sesion, items, cupon_codigo="NOEXISTE", fecha=hoy)


def test_evaluar_carrito_filtra_reglas_de_campana_por_cupon(sesion, hoy):
    campana = promo.crear_campana(sesion, "Verano", "Instagram", "VERANO15", "instagram", "verano",
                                  hoy, presupuesto_bs=1000.0)
    general = promo.crear_regla_promocion(sesion, "General Deportivo", "PORCENTAJE", hoy, valor=10.0,
                                          categoria="Deportivo")
    de_campana = promo.crear_regla_promocion(sesion, "Extra por cupón", "PORCENTAJE", hoy, valor=5.0,
                                             categoria="Deportivo", campana_id=campana.id)
    items = [ItemCarrito(producto_id=1, cantidad=1, precio_unitario_bs=100.0, categoria="Deportivo")]

    sin_cupon = promo.evaluar_carrito(sesion, items, fecha=hoy)
    assert sin_cupon.reglas_aplicadas == [general.id]

    con_cupon = promo.evaluar_carrito(sesion, items, cupon_codigo="VERANO15", fecha=hoy)
    assert set(con_cupon.reglas_aplicadas) == {general.id, de_campana.id}


# --- Campañas de marketing ----------------------------------------------------------

def test_crear_campana_canal_invalido(sesion, hoy):
    with pytest.raises(ErrorNegocio, match="Canal inválido"):
        promo.crear_campana(sesion, "x", "Twitter", "CUPON1", "twitter", "camp", hoy)


def test_crear_campana_exige_cupon(sesion, hoy):
    with pytest.raises(ErrorNegocio, match="cupón"):
        promo.crear_campana(sesion, "x", "TikTok", "   ", "tiktok", "camp", hoy)


def test_crear_campana_cupon_duplicado(sesion, hoy):
    promo.crear_campana(sesion, "Invierno", "TikTok", "INVIERNO20", "tiktok", "invierno", hoy)
    with pytest.raises(ErrorNegocio, match="Ya existe una campaña"):
        promo.crear_campana(sesion, "Otra", "TikTok", "invierno20", "tiktok", "otra", hoy)


def test_generar_enlace_utm_formato(sesion, hoy):
    campana = promo.crear_campana(sesion, "Invierno", "TikTok", "INVIERNO20", "tiktok", "invierno_2026", hoy,
                                  utm_medium="social")
    enlace = promo.generar_enlace_utm(campana)
    assert enlace == (
        "https://manaco.bo/tienda?utm_source=tiktok&utm_medium=social"
        "&utm_campaign=invierno_2026&cupon=INVIERNO20"
    )


def test_registrar_conversion_campana_no_existe(sesion, hoy):
    with pytest.raises(ErrorNegocio, match="no existe"):
        promo.registrar_conversion(sesion, 999, 100.0, hoy)


def test_registrar_conversion_con_descuento_requiere_plan_de_cuentas(sesion, hoy):
    campana = promo.crear_campana(sesion, "Invierno", "TikTok", "INVIERNO20", "tiktok", "invierno", hoy)
    with pytest.raises(contabilidad.ErrorNegocio, match="no existe"):
        promo.registrar_conversion(sesion, campana.id, 100.0, hoy, descuento_bs=20.0)


def test_registrar_conversion_y_roas_por_campana(sesion, hoy):
    contabilidad.sembrar_plan_cuentas(sesion)
    campana = promo.crear_campana(sesion, "Invierno", "TikTok", "INVIERNO20", "tiktok", "invierno", hoy,
                                  presupuesto_bs=200.0)
    promo.registrar_conversion(sesion, campana.id, 300.0, hoy, descuento_bs=20.0)
    promo.registrar_conversion(sesion, campana.id, 100.0, hoy)

    roas = promo.roas_por_campana(sesion)
    fila = roas.loc[roas["Campaña"] == "Invierno"].iloc[0]
    assert fila["Conversiones"] == 2
    assert fila["Monto generado Bs"] == 400.0
    assert fila["ROAS"] == 2.0

    diario = contabilidad.libro_diario(sesion)
    assert float(diario["Debe Bs"].sum()) == 20.0


def test_roas_por_campana_sin_presupuesto_es_none(sesion, hoy):
    campana = promo.crear_campana(sesion, "Sin presupuesto", "Facebook", "FB10", "facebook", "camp", hoy)
    roas = promo.roas_por_campana(sesion)
    assert roas.loc[roas["Campaña"] == "Sin presupuesto"].iloc[0]["ROAS"] is None
