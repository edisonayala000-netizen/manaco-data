"""Reglas de promoción, campañas de marketing digital (cupón + UTM) y simulador de carrito."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.auth import proteger_pagina
from src.config import CANALES_CAMPANA, TIPO_PROMO_COMBO, TIPO_PROMO_MONTO_FIJO, TIPO_PROMO_PORCENTAJE, TIPOS_PROMOCION
from src.db import obtener_sesion
from src.services import promociones
from src.services.promociones import ErrorNegocio, ItemCarrito
from src.ui.comunes import avisar_y_recargar, exigir_catalogo, mostrar_aviso_pendiente, selector_fecha
from src.ui.estilos import ICONOS, aviso, encabezado, estado_vacio, num, tarjeta, tarjeta_kpi

proteger_pagina("marketing")
encabezado("Marketing y promociones", "Reglas de descuento, campañas digitales con cupón/UTM y simulador de carrito.",
           ICONOS["marketing"])
mostrar_aviso_pendiente()
_, productos = exigir_catalogo()
categorias = sorted(productos["categoria"].unique().tolist())

with obtener_sesion() as s:
    reglas = promociones.tabla_reglas_promocion(s)
    campanas = promociones.tabla_campanas(s)
    roas = promociones.roas_por_campana(s)

k1, k2, k3 = st.columns(3)
with k1:
    tarjeta_kpi("Reglas activas", num(int(reglas["Activa"].sum()) if not reglas.empty else 0),
               icono="sell", color="morado", mini=True)
with k2:
    tarjeta_kpi("Campañas activas", num(int(campanas["Activa"].sum()) if not campanas.empty else 0),
               icono="campaign", color="azul", mini=True)
with k3:
    conversiones_totales = int(roas["Conversiones"].sum()) if not roas.empty else 0
    tarjeta_kpi("Conversiones atribuidas", num(conversiones_totales), icono="trending_up", color="verde", mini=True)
st.write("")

tab_reglas, tab_campanas, tab_carrito = st.tabs(
    [":material/sell: Reglas de promoción", ":material/campaign: Campañas",
     ":material/shopping_cart_checkout: Probar carrito"])

# --- Reglas de promoción -----------------------------------------------------------
with tab_reglas:
    with tarjeta("reglas-tabla", "Reglas de promoción", icono="sell"):
        if reglas.empty:
            estado_vacio("No hay reglas de promoción. Cree la primera abajo.", "sell")
        else:
            st.dataframe(reglas.drop(columns="id"), hide_index=True, width="stretch")

    st.write("")
    with tarjeta("reglas-nueva", "Nueva regla de promoción", icono="add_circle"), \
            st.form("nueva_regla", clear_on_submit=True, border=False):
        a, b = st.columns(2)
        nombre_r = a.text_input("Nombre", placeholder="Descuento de temporada")
        tipo_r = b.selectbox("Tipo", list(TIPOS_PROMOCION))
        c, d = st.columns(2)
        objetivo = c.radio("Aplica a", ["Categoría", "Producto"], horizontal=True)
        if objetivo == "Categoría":
            categoria_r = d.selectbox("Categoría", categorias)
            etiqueta_prod_r = None
        else:
            etiqueta_prod_r = d.selectbox("Producto", productos["etiqueta"].tolist())
            categoria_r = None
        e, f = st.columns(2)
        valor_r = e.number_input("Valor (% o Bs, según tipo)", min_value=0.0, step=1.0, value=0.0)
        g, h = st.columns(2)
        cantidad_necesaria_r = g.number_input("Cant. necesaria (combo)", min_value=0, step=1, value=0)
        cantidad_gratis_r = h.number_input("Cant. gratis (combo)", min_value=0, step=1, value=0)
        i, j = st.columns(2)
        fecha_inicio_r = selector_fecha("regla_inicio", i)
        con_fin = j.checkbox("Tiene fecha de fin")
        fecha_fin_r = selector_fecha("regla_fin", j) if con_fin else None
        if st.form_submit_button("Crear regla", type="primary", icon=":material/add:"):
            try:
                with obtener_sesion() as s:
                    producto_id_r = None
                    if etiqueta_prod_r is not None:
                        producto_id_r = int(productos.loc[productos["etiqueta"] == etiqueta_prod_r, "id"].iloc[0])
                    promociones.crear_regla_promocion(
                        s, nombre_r, tipo_r, fecha_inicio_r, valor=valor_r, producto_id=producto_id_r,
                        categoria=categoria_r,
                        cantidad_necesaria=int(cantidad_necesaria_r) if tipo_r == TIPO_PROMO_COMBO else None,
                        cantidad_gratis=int(cantidad_gratis_r) if tipo_r == TIPO_PROMO_COMBO else None,
                        fecha_fin=fecha_fin_r)
                avisar_y_recargar(f"Regla {nombre_r.strip()} creada.")
            except ErrorNegocio as exc:
                aviso(str(exc), "error")

# --- Campañas ------------------------------------------------------------------------
with tab_campanas:
    with tarjeta("camp-tabla", "Campañas de marketing digital", icono="campaign"):
        if campanas.empty:
            estado_vacio("No hay campañas registradas. Cree la primera abajo.", "campaign")
        else:
            st.dataframe(campanas.drop(columns="id"), hide_index=True, width="stretch", column_config={
                "Enlace": st.column_config.LinkColumn(),
                "Presupuesto Bs": st.column_config.NumberColumn(format="localized"),
            })

    st.write("")
    with tarjeta("camp-roas", "ROAS por campaña", icono="trending_up"):
        if roas.empty:
            estado_vacio("Registre conversiones para calcular el ROAS.", "trending_up")
        else:
            st.dataframe(roas, hide_index=True, width="stretch")

    st.write("")
    with tarjeta("camp-nueva", "Nueva campaña", icono="add_circle"), \
            st.form("nueva_campana", clear_on_submit=True, border=False):
        a, b = st.columns(2)
        nombre_c = a.text_input("Nombre", placeholder="Rebaja de invierno TikTok")
        canal_c = b.selectbox("Canal", list(CANALES_CAMPANA))
        c, d = st.columns(2)
        cupon_c = c.text_input("Código de cupón", placeholder="INVIERNO20")
        presupuesto_c = d.number_input("Presupuesto (Bs)", min_value=0.0, step=100.0, value=0.0)
        e, f = st.columns(2)
        utm_source_c = e.text_input("UTM source", placeholder="tiktok")
        utm_campaign_c = f.text_input("UTM campaign", placeholder="invierno_2026")
        g, h = st.columns(2)
        utm_medium_c = g.text_input("UTM medium", value="social")
        fecha_inicio_c = selector_fecha("camp_inicio", h)
        if st.form_submit_button("Crear campaña", type="primary", icon=":material/add:"):
            try:
                with obtener_sesion() as s:
                    promociones.crear_campana(
                        s, nombre_c, canal_c, cupon_c, utm_source_c, utm_campaign_c, fecha_inicio_c,
                        utm_medium=utm_medium_c, presupuesto_bs=presupuesto_c)
                avisar_y_recargar(f"Campaña {nombre_c.strip()} creada.")
            except ErrorNegocio as exc:
                aviso(str(exc), "error")

# --- Probar carrito --------------------------------------------------------------------
with tab_carrito:
    with tarjeta("carrito-probar", "Simular descuento de un carrito", icono="shopping_cart_checkout"):
        fecha_carrito = selector_fecha("carrito_fecha")
        cupon_carrito = st.text_input("Cupón (opcional)", placeholder="INVIERNO20")
        lineas_carrito = st.data_editor(
            pd.DataFrame([{"Código": "", "Cantidad": 0}]),
            num_rows="dynamic", hide_index=True, width="stretch", key="carrito_lineas",
            column_config={
                "Código": st.column_config.SelectboxColumn(options=productos["codigo"].tolist()),
                "Cantidad": st.column_config.NumberColumn(min_value=0, step=1),
            },
        )
        if st.button("Evaluar carrito", type="primary", icon=":material/calculate:"):
            filas_validas = lineas_carrito[(lineas_carrito["Código"] != "") & (lineas_carrito["Cantidad"] > 0)]
            if filas_validas.empty:
                aviso("Agregue al menos una línea con producto y cantidad.", "error")
            else:
                items = []
                for _, fila in filas_validas.iterrows():
                    prod = productos.loc[productos["codigo"] == fila["Código"]].iloc[0]
                    items.append(ItemCarrito(int(prod["id"]), int(fila["Cantidad"]), float(prod["precio"]),
                                             str(prod["categoria"])))
                try:
                    with obtener_sesion() as s:
                        resultado = promociones.evaluar_carrito(
                            s, items, cupon_codigo=cupon_carrito.strip() or None, fecha=fecha_carrito)
                    if resultado.descuento_total_bs <= 0:
                        aviso("Ninguna promoción aplica a este carrito.", "info")
                    else:
                        aviso(f"Descuento total: {resultado.descuento_total_bs:.2f} Bs", "success")
                        for detalle in resultado.detalles:
                            st.caption(f"• {detalle}")
                except ErrorNegocio as exc:
                    aviso(str(exc), "error")
