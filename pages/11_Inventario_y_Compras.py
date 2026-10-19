"""Proveedores, inventario con punto de reorden y órdenes de compra."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.auth import proteger_pagina
from src.db import obtener_sesion
from src.services import compras
from src.services.compras import ErrorNegocio, LineaCompra
from src.ui.comunes import avisar_y_recargar, exigir_catalogo, mostrar_aviso_pendiente, selector_fecha, selector_tienda
from src.ui.estilos import ICONOS, aviso, encabezado, estado_vacio, num, tarjeta, tarjeta_kpi

proteger_pagina("inventario")
encabezado("Inventario y compras", "Controle el stock de reposición, los proveedores y las órdenes de compra.",
           ICONOS["inventario"])
mostrar_aviso_pendiente()
tiendas, productos = exigir_catalogo()

with obtener_sesion() as s:
    proveedores = compras.tabla_proveedores(s)
    inventario_df = compras.tabla_inventario(s)
    alertas = compras.alertas_pendientes(s)
    ordenes = compras.tabla_ordenes_compra(s)

k1, k2, k3 = st.columns(3)
with k1:
    tarjeta_kpi("Productos bajo control", num(len(inventario_df)), icono="inventory", color="azul", mini=True)
with k2:
    tarjeta_kpi("Alertas de stock crítico", num(len(alertas)), icono="warning",
                color="rojo" if len(alertas) else "verde", mini=True)
with k3:
    tarjeta_kpi("Órdenes de compra", num(len(ordenes)), icono="shopping_cart", color="morado", mini=True)
st.write("")

tab_prov, tab_inv, tab_oc = st.tabs(
    [":material/local_shipping: Proveedores", ":material/inventory: Inventario",
     ":material/shopping_cart: Órdenes de compra"])

# --- Proveedores ---------------------------------------------------------------
with tab_prov:
    with tarjeta("prov-tabla", "Proveedores", icono="local_shipping"):
        if proveedores.empty:
            estado_vacio("No hay proveedores registrados. Agregue el primero abajo.", "local_shipping")
        else:
            st.dataframe(proveedores.drop(columns="id"), hide_index=True, width="stretch")
    st.write("")
    with tarjeta("prov-nuevo", "Nuevo proveedor", icono="add_business"), \
            st.form("nuevo_proveedor", clear_on_submit=True, border=False):
        a, b = st.columns(2)
        nombre_p = a.text_input("Nombre", placeholder="Calzados del Sur S.R.L.")
        nit = b.text_input("NIT", placeholder="123456789")
        c, d = st.columns(2)
        telefono = c.text_input("Teléfono")
        email = d.text_input("Email")
        if st.form_submit_button("Agregar proveedor", type="primary", icon=":material/add:"):
            try:
                with obtener_sesion() as s:
                    compras.crear_proveedor(s, nombre_p, nit=nit, telefono=telefono, email=email)
                avisar_y_recargar(f"Proveedor {nombre_p.strip()} agregado.")
            except ErrorNegocio as exc:
                aviso(str(exc), "error")

# --- Inventario (punto de reorden) ---------------------------------------------
with tab_inv:
    if alertas.empty:
        with tarjeta("alertas-vacio"):
            estado_vacio("No hay alertas de stock crítico pendientes.", "verified")
    else:
        with tarjeta("alertas", "Alertas de stock crítico",
                     f"{len(alertas)} producto(s) en o bajo su punto de reorden", "warning"):
            st.dataframe(alertas.drop(columns="id"), hide_index=True, width="stretch")

    st.write("")
    with tarjeta("inv-tabla", "Stock bajo control de reorden", icono="inventory"):
        if inventario_df.empty:
            estado_vacio("Ningún producto está bajo control de reorden todavía. Agregue uno abajo.", "inventory")
        else:
            st.dataframe(inventario_df.drop(columns="id"), hide_index=True, width="stretch",
                         column_config={"En alerta": st.column_config.CheckboxColumn(disabled=True)})

    st.write("")
    with tarjeta("inv-nuevo", "Poner un producto bajo control de reorden", icono="add_circle"), \
            st.form("nuevo_inventario", clear_on_submit=True, border=False):
        a, b = st.columns(2)
        tienda_id, _ = selector_tienda(tiendas, "inv_tienda", a)
        etiqueta_prod = b.selectbox("Producto", productos["etiqueta"].tolist(), key="inv_producto")
        producto_id = int(productos.loc[productos["etiqueta"] == etiqueta_prod, "id"].iloc[0])
        c, d, e = st.columns(3)
        stock_inicial = c.number_input("Stock inicial", min_value=0, step=1, value=0)
        stock_minimo = d.number_input("Stock mínimo", min_value=0, step=1, value=5)
        punto_reorden = e.number_input("Punto de reorden", min_value=0, step=1, value=10)
        opciones_prov = {"(sin proveedor predeterminado)": None}
        opciones_prov.update({r["Nombre"]: int(r["id"]) for _, r in proveedores.iterrows()})
        prov_elegido = st.selectbox("Proveedor predeterminado (para pedidos automáticos)", list(opciones_prov))
        if st.form_submit_button("Guardar", type="primary", icon=":material/save:"):
            try:
                with obtener_sesion() as s:
                    compras.obtener_o_crear_inventario(
                        s, producto_id, tienda_id, int(stock_inicial), int(stock_minimo), int(punto_reorden),
                        opciones_prov[prov_elegido])
                avisar_y_recargar("Producto puesto bajo control de reorden.")
            except ErrorNegocio as exc:
                aviso(str(exc), "error")

# --- Órdenes de compra -----------------------------------------------------------
with tab_oc:
    with tarjeta("oc-tabla", "Órdenes de compra", icono="shopping_cart"):
        if ordenes.empty:
            estado_vacio("No hay órdenes de compra todavía.", "shopping_cart")
        else:
            st.dataframe(ordenes.drop(columns="id"), hide_index=True, width="stretch", column_config={
                "Subtotal Bs": st.column_config.NumberColumn(format="localized"),
                "Flete Bs": st.column_config.NumberColumn(format="localized"),
                "Arancel Bs": st.column_config.NumberColumn(format="localized"),
                "Total Bs": st.column_config.NumberColumn(format="localized"),
            })

    st.write("")
    izq, der = st.columns(2, gap="medium")
    with izq, tarjeta("oc-nueva", "Nueva orden de compra", icono="add_shopping_cart"):
        if proveedores.empty:
            estado_vacio("Registre un proveedor primero.", "local_shipping")
        else:
            with st.form("nueva_oc", clear_on_submit=True, border=False):
                a, b = st.columns(2)
                opciones_prov2 = {r["Nombre"]: int(r["id"]) for _, r in proveedores.iterrows()}
                prov_nombre = a.selectbox("Proveedor", list(opciones_prov2))
                tienda_oc_id, _ = selector_tienda(tiendas, "oc_tienda", b)
                fecha_emision = selector_fecha("oc_fecha")
                lineas_df = st.data_editor(
                    pd.DataFrame([{"Código": "", "Cantidad": 0, "Costo unitario Bs": 0.0}]),
                    num_rows="dynamic", hide_index=True, width="stretch", key="oc_lineas",
                    column_config={
                        "Código": st.column_config.SelectboxColumn(options=productos["codigo"].tolist()),
                        "Cantidad": st.column_config.NumberColumn(min_value=0, step=1),
                        "Costo unitario Bs": st.column_config.NumberColumn(min_value=0.0, format="localized"),
                    },
                )
                if st.form_submit_button("Crear orden", type="primary", icon=":material/add:"):
                    filas_validas = lineas_df[(lineas_df["Código"] != "") & (lineas_df["Cantidad"] > 0)]
                    if filas_validas.empty:
                        aviso("Agregue al menos una línea con producto y cantidad.", "error")
                    else:
                        lineas = [
                            LineaCompra(int(productos.loc[productos["codigo"] == fila["Código"], "id"].iloc[0]),
                                       int(fila["Cantidad"]), float(fila["Costo unitario Bs"]))
                            for _, fila in filas_validas.iterrows()
                        ]
                        try:
                            with obtener_sesion() as s:
                                compras.crear_orden_compra(s, opciones_prov2[prov_nombre], tienda_oc_id,
                                                           fecha_emision, lineas)
                            avisar_y_recargar("Orden de compra creada en borrador.")
                        except ErrorNegocio as exc:
                            aviso(str(exc), "error")

    with der, tarjeta("oc-gestion", "Aprobar y recibir una orden", icono="fact_check"):
        if ordenes.empty:
            estado_vacio("No hay órdenes para gestionar.", "shopping_cart")
        else:
            opciones_oc = {f"#{r['id']} · {r['Proveedor']} · {r['Estado']}": int(r["id"])
                           for _, r in ordenes.iterrows()}
            oc_elegida = st.selectbox("Orden", list(opciones_oc))
            oc_id = opciones_oc[oc_elegida]
            with obtener_sesion() as s:
                detalle = compras.detalle_orden_compra(s, oc_id)
            st.dataframe(detalle, hide_index=True, width="stretch")
            fila_oc = ordenes.loc[ordenes["id"] == oc_id].iloc[0]
            if fila_oc["Estado"] == "BORRADOR":
                if st.button("Aprobar orden", icon=":material/check_circle:"):
                    with obtener_sesion() as s:
                        compras.aprobar_orden_compra(s, oc_id)
                    avisar_y_recargar("Orden aprobada.")
            elif fila_oc["Estado"] == "APROBADA":
                with st.form("recibir_oc", border=False):
                    fecha_recepcion = selector_fecha("oc_fecha_recepcion")
                    f1, f2 = st.columns(2)
                    flete = f1.number_input("Flete (Bs)", min_value=0.0, step=10.0, value=0.0)
                    arancel = f2.number_input("Arancel (Bs)", min_value=0.0, step=10.0, value=0.0)
                    if st.form_submit_button("Recibir orden", type="primary", icon=":material/inventory:"):
                        try:
                            with obtener_sesion() as s:
                                compras.recibir_orden_compra(s, oc_id, fecha_recepcion, flete, arancel)
                            avisar_y_recargar("Orden recibida: stock actualizado y costo recalculado.")
                        except ErrorNegocio as exc:
                            aviso(str(exc), "error")
            else:
                st.caption(f"Esta orden ya está en estado {fila_oc['Estado']}.")
