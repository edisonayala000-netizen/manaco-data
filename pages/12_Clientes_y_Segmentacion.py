"""Clientes y segmentación RFM (Recencia, Frecuencia, Monto)."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.auth import proteger_pagina
from src.config import CIUDADES, SEGMENTOS_RFM
from src.db import obtener_sesion
from src.models import Cliente
from src.services import rfm
from src.ui.comunes import avisar_y_recargar, mostrar_aviso_pendiente
from src.ui.estilos import ICONOS, aviso, bs, encabezado, estado_vacio, num, seccion, tarjeta, tarjeta_kpi

proteger_pagina("clientes")
encabezado("Clientes y segmentación", "Perfile a sus clientes por Recencia, Frecuencia y Monto (RFM).",
           ICONOS["clientes"])
mostrar_aviso_pendiente()

tab_clientes, tab_rfm = st.tabs([":material/groups: Clientes", ":material/insights: Segmentación RFM"])

# --- Clientes --------------------------------------------------------------------
with tab_clientes:
    with obtener_sesion() as s:
        clientes = pd.DataFrame([{
            "id": c.id, "Nombre": c.nombre, "Documento": c.documento, "Teléfono": c.telefono,
            "Email": c.email, "Ciudad": c.ciudad, "Activo": c.activo,
        } for c in s.scalars(select(Cliente).order_by(Cliente.nombre)).all()],
            columns=["id", "Nombre", "Documento", "Teléfono", "Email", "Ciudad", "Activo"])

    if clientes.empty:
        with tarjeta("cli-vacio"):
            estado_vacio("No hay clientes registrados. Agregue el primero abajo.", "groups")
    else:
        seccion(f"{len(clientes)} clientes")
        with tarjeta("cli-tabla", "Editar clientes", icono="edit"):
            editado = st.data_editor(
                clientes, hide_index=True, width="stretch", key="cli_editor",
                disabled=["id", "Documento"],
                column_config={
                    "id": None,
                    "Ciudad": st.column_config.SelectboxColumn(options=list(CIUDADES)),
                    "Activo": st.column_config.CheckboxColumn(help="Desmarque para dar de baja"),
                },
            )
            if st.button("Guardar cambios de clientes", type="primary", icon=":material/save:"):
                with obtener_sesion() as s:
                    for _, fila in editado.iterrows():
                        c = s.get(Cliente, int(fila["id"]))
                        c.nombre = str(fila["Nombre"]).strip() or c.nombre
                        c.telefono, c.email = str(fila["Teléfono"] or ""), str(fila["Email"] or "")
                        c.ciudad, c.activo = fila["Ciudad"], bool(fila["Activo"])
                avisar_y_recargar("Clientes actualizados.")

    st.write("")
    with tarjeta("cli-nuevo", "Nuevo cliente", icono="person_add"), \
            st.form("nuevo_cliente", clear_on_submit=True, border=False):
        a, b, c = st.columns(3)
        nombre_c = a.text_input("Nombre", placeholder="María Pérez")
        documento = b.text_input("Documento (CI/NIT)", placeholder="1234567 LP")
        ciudad_c = c.selectbox("Ciudad", list(CIUDADES))
        d, e = st.columns(2)
        telefono_c = d.text_input("Teléfono")
        email_c = e.text_input("Email")
        if st.form_submit_button("Agregar cliente", type="primary", icon=":material/add:"):
            if not nombre_c.strip():
                aviso("El nombre es obligatorio.", "error")
            else:
                try:
                    with obtener_sesion() as s:
                        s.add(Cliente(nombre=nombre_c.strip(), documento=documento.strip() or None,
                                      telefono=telefono_c.strip(), email=email_c.strip(), ciudad=ciudad_c))
                    avisar_y_recargar(f"Cliente {nombre_c.strip()} agregado.")
                except IntegrityError:
                    aviso("Ya existe un cliente con ese documento.", "error")

# --- Segmentación RFM --------------------------------------------------------------
with tab_rfm:
    with obtener_sesion() as s:
        resumen = rfm.resumen_segmentos(s)
        tabla = rfm.tabla_segmentos(s)

    if st.button("Recalcular segmentación RFM", icon=":material/refresh:"):
        with obtener_sesion() as s:
            rfm.actualizar_perfiles_rfm(s)
        avisar_y_recargar("Segmentación RFM recalculada con las ventas más recientes.")

    if tabla.empty:
        with tarjeta("rfm-vacio"):
            estado_vacio("Aún no hay perfiles RFM. Registre ventas con cliente y pulse «Recalcular».", "insights")
    else:
        cols = st.columns(min(len(resumen), 5) or 1)
        for i, (_, fila) in enumerate(resumen.iterrows()):
            with cols[i % len(cols)]:
                tarjeta_kpi(fila["Segmento"], num(int(fila["Clientes"])), bs(fila["Monto total Bs"], 0),
                            icono="person", color="morado", mini=True)
        st.write("")
        with tarjeta("rfm-tabla", "Clientes por segmento", icono="insights"):
            segmento_filtro = st.selectbox("Filtrar por segmento", ["Todos"] + list(SEGMENTOS_RFM))
            vista = tabla if segmento_filtro == "Todos" else tabla[tabla["Segmento"] == segmento_filtro]
            st.dataframe(vista.drop(columns="id"), hide_index=True, width="stretch", column_config={
                "Monto total Bs": st.column_config.NumberColumn(format="localized"),
                "Calculado": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
            })
