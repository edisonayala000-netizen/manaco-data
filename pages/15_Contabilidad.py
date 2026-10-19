"""Libro diario y balance de comprobación (partida doble)."""

from __future__ import annotations

import streamlit as st

from src.auth import proteger_pagina
from src.db import obtener_sesion
from src.services import contabilidad
from src.ui.comunes import mostrar_aviso_pendiente, selector_fecha
from src.ui.estilos import ICONOS, aviso, bs, encabezado, estado_vacio, num, tarjeta, tarjeta_kpi

proteger_pagina("contabilidad")
encabezado("Contabilidad", "Libro diario y balance de comprobación generados automáticamente por las operaciones.",
           ICONOS["contabilidad"])
mostrar_aviso_pendiente()

with obtener_sesion() as s:
    balance = contabilidad.balance_comprobacion(s)

if balance.empty:
    with tarjeta("plan-vacio"):
        estado_vacio("El plan de cuentas aún no está sembrado.", "account_balance")
        if st.button("Sembrar plan de cuentas base", type="primary", icon=":material/account_balance:"):
            with obtener_sesion() as s:
                contabilidad.sembrar_plan_cuentas(s)
            st.rerun()
    st.stop()

total_debe = float(balance["Debe Bs"].sum())
total_haber = float(balance["Haber Bs"].sum())
k1, k2, k3 = st.columns(3)
with k1:
    tarjeta_kpi("Total debe", bs(total_debe), icono="arrow_upward", color="azul", mini=True)
with k2:
    tarjeta_kpi("Total haber", bs(total_haber), icono="arrow_downward", color="morado", mini=True)
with k3:
    cuadrado = abs(total_debe - total_haber) <= contabilidad.TOLERANCIA_CUADRE
    tarjeta_kpi("Cuadre", "OK" if cuadrado else "Descuadrado", icono="balance",
               color="verde" if cuadrado else "rojo", mini=True)
st.write("")

tab_diario, tab_balance = st.tabs([":material/menu_book: Libro diario", ":material/balance: Balance de comprobación"])

with tab_diario:
    with tarjeta("diario-filtros", "Filtrar por fecha", icono="filter_alt"):
        a, b, c = st.columns([1, 1, 1])
        usar_filtro = a.checkbox("Filtrar por rango de fechas")
        desde = selector_fecha("diario_desde", b) if usar_filtro else None
        hasta = selector_fecha("diario_hasta", c) if usar_filtro else None

    with obtener_sesion() as s:
        diario = contabilidad.libro_diario(s, desde=desde, hasta=hasta)

    with tarjeta("diario-tabla", "Libro diario", icono="menu_book"):
        if diario.empty:
            estado_vacio("No hay asientos contables para el rango seleccionado.", "menu_book")
        else:
            st.dataframe(diario, hide_index=True, width="stretch", column_config={
                "Debe Bs": st.column_config.NumberColumn(format="localized"),
                "Haber Bs": st.column_config.NumberColumn(format="localized"),
            })

with tab_balance:
    with tarjeta("balance-tabla", "Balance de comprobación", icono="balance"):
        st.dataframe(balance, hide_index=True, width="stretch", column_config={
            "Debe Bs": st.column_config.NumberColumn(format="localized"),
            "Haber Bs": st.column_config.NumberColumn(format="localized"),
            "Saldo Bs": st.column_config.NumberColumn(format="localized"),
        })
        if not cuadrado:
            aviso("El balance no cuadra: revise los asientos registrados.", "error")
