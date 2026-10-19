"""Motor de recomendación de venta cruzada (cesta de mercado)."""

from __future__ import annotations

import streamlit as st

from src.auth import proteger_pagina
from src.db import obtener_sesion
from src.services import recomendacion
from src.services.recomendacion import METODO_ASOCIACION, ErrorNegocio
from src.ui.comunes import exigir_catalogo, mostrar_aviso_pendiente, selector_producto
from src.ui.estilos import ICONOS, aviso, encabezado, estado_vacio, num, tarjeta, tarjeta_kpi

proteger_pagina("recomendaciones")
encabezado("Recomendaciones", "Venta cruzada: qué ofrecer junto a cada producto, según el historial de compras.",
           ICONOS["recomendaciones"])
mostrar_aviso_pendiente()
_, productos = exigir_catalogo()

with obtener_sesion() as s:
    conversion = recomendacion.tasa_conversion(s)

k1, k2 = st.columns(2)
with k1:
    mostradas = int(conversion["Mostradas"].sum()) if not conversion.empty else 0
    tarjeta_kpi("Recomendaciones registradas", num(mostradas), icono="recommend", color="azul", mini=True)
with k2:
    aceptadas = int(conversion["Aceptadas"].sum()) if not conversion.empty else 0
    tarjeta_kpi("Aceptadas por el cliente", num(aceptadas), icono="check_circle", color="verde", mini=True)
st.write("")

with tarjeta("rec-buscar", "Buscar recomendaciones para un producto", icono="search"):
    fila_producto = selector_producto(productos, "rec_producto")
    producto_id = int(fila_producto["id"])
    if st.button("Generar recomendaciones", type="primary", icon=":material/auto_awesome:"):
        try:
            with obtener_sesion() as s:
                recomendaciones = recomendacion.recomendar(s, producto_id)
                logs = [recomendacion.registrar_recomendacion_mostrada(s, producto_id, r) for r in recomendaciones]
            st.session_state["rec_resultado"] = [
                {"log_id": log.id, "codigo": r.codigo, "nombre": r.nombre, "metodo": r.metodo,
                 "soporte": r.soporte, "confianza": r.confianza, "lift": r.lift}
                for log, r in zip(logs, recomendaciones)
            ]
        except ErrorNegocio as exc:
            aviso(str(exc), "error")

resultado = st.session_state.get("rec_resultado")
if resultado:
    st.write("")
    with tarjeta("rec-resultado", f"Top {len(resultado)} complementarios", icono="recommend"):
        cols = st.columns(len(resultado))
        for col, item in zip(cols, resultado):
            with col:
                st.markdown(f"**{item['codigo']}** · {item['nombre']}")
                if item["metodo"] == METODO_ASOCIACION:
                    st.caption(f"Soporte {item['soporte']:.1%} · Confianza {item['confianza']:.1%} "
                               f"· Lift {item['lift']:.2f}")
                else:
                    st.caption("Misma categoría/color (sin historial suficiente)")
                if st.button("Marcar aceptada", key=f"acepta_{item['log_id']}", icon=":material/thumb_up:"):
                    with obtener_sesion() as s:
                        recomendacion.marcar_aceptada(s, item["log_id"], True)
                    aviso("Recomendación marcada como aceptada.", "success")

st.write("")
with tarjeta("rec-conversion", "Tasa de conversión por método", icono="insights"):
    if conversion.empty:
        estado_vacio("Aún no se registraron recomendaciones mostradas.", "insights")
    else:
        st.dataframe(conversion, hide_index=True, width="stretch",
                     column_config={"Tasa de conversión": st.column_config.NumberColumn(format="percent")})
