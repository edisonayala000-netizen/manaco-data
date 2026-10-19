"""Registro rápido de ventas y stock disponible en tiempo real."""

from __future__ import annotations

import streamlit as st

from src.auth import proteger_pagina
from src.db import obtener_sesion
from src.services import compras, inventario as inv
from src.services.inventario import ErrorNegocio
from src.ui.comunes import (
    avisar_y_recargar, exigir_catalogo, mostrar_aviso_pendiente, selector_fecha, selector_producto,
    selector_tienda,
)
from src.ui.estilos import (
    ICONOS, aviso, bs, encabezado, estado_vacio, fecha as ffecha, lista_stock, num, seccion, sugerencia, tarjeta,
    tarjeta_kpi,
)

IR_APERTURA = ("Ir a Apertura", "pages/1_Apertura.py", "inventory_2")

usuario = proteger_pagina("ventas")
encabezado("Ventas", "Registre cada venta; el stock disponible se descuenta al instante.", ICONOS["ventas"])
mostrar_aviso_pendiente()
tiendas, productos = exigir_catalogo()

with tarjeta("filtros"):
    c1, c2 = st.columns(2)
    dia = selector_fecha("ve_fecha", c1)
    tienda_id, tienda_nombre = selector_tienda(tiendas, "ve_tienda", c2)

with obtener_sesion() as s:
    stock = inv.stock_disponible(s, dia, tienda_id)
    ventas = inv.tabla_ventas(s, dia, dia, tienda_id)
    cerrados = inv.productos_cerrados(s, dia, tienda_id)

pares_hoy = int(ventas["Cantidad"].sum()) if not ventas.empty else 0
importe_hoy = float(ventas["Importe"].sum()) if not ventas.empty else 0.0
st.write("")
k1, k2, k3 = st.columns(3)
with k1:
    tarjeta_kpi("Pares vendidos hoy", num(pares_hoy), icono="shopping_bag", color="verde", mini=True)
with k2:
    tarjeta_kpi("Importe del día", bs(importe_hoy, 0), icono="payments", color="azul", mini=True)
with k3:
    tarjeta_kpi("Stock disponible", num(int(stock["Disponible"].sum()) if not stock.empty else 0),
                f"{len(stock)} productos abiertos" if not stock.empty else None, icono="inventory", color="morado",
                mini=True)
st.write("")

abiertos = productos[productos["codigo"].isin(stock["Código"]) & ~productos["id"].isin(cerrados)]
izq, der = st.columns([1, 1.2], gap="medium")
with izq, tarjeta("venta", "Nueva venta", icono="point_of_sale"):
    if stock.empty:
        estado_vacio(f"No hay aperturas en {tienda_nombre} el {ffecha(dia)}. Registre primero la apertura.",
                     "inventory_2", IR_APERTURA, clave="venta")
    elif abiertos.empty:
        estado_vacio(f"Todos los productos de {tienda_nombre} ya están cerrados el {ffecha(dia)}.", "lock")
    else:
        if cerrados:
            st.caption(f"{len(cerrados)} producto(s) ya cerrado(s) hoy no aparecen en la lista.")
        producto = selector_producto(abiertos, "ve_producto")
        disponible = int(stock.loc[stock["Código"] == producto["codigo"], "Disponible"].iloc[0])
        sugerencia(f"Disponible: <b>{disponible} pares</b> · Precio de lista: <b>{bs(producto['precio'])}</b>")
        with st.form("form_venta", clear_on_submit=True, border=False):
            a, b = st.columns(2)
            cantidad = a.number_input("Cantidad (pares)", min_value=1, step=1, value=1)
            precio = b.number_input("Precio unitario (Bs)", min_value=0.0, step=1.0,
                                    value=float(producto["precio"]), format="%.2f")
            if st.form_submit_button("Registrar venta", type="primary", width="stretch",
                                     icon=":material/add_shopping_cart:"):
                try:
                    with obtener_sesion() as s:
                        venta = inv.registrar_venta(s, dia, tienda_id, int(producto["id"]), int(cantidad),
                                                    float(precio), usuario.id)
                        compras.sincronizar_stock_tras_venta(s, venta)
                    avisar_y_recargar(f"Venta registrada: {int(cantidad)} par(es) de {producto['codigo']} "
                                      f"por {bs(cantidad * precio)}.")
                except ErrorNegocio as exc:
                    aviso(str(exc), "error")

with der, tarjeta("stock", "Stock disponible", "Verde > 50 % · amarillo 20–50 % · rojo < 20 % del saldo inicial",
                  "inventory"):
    if stock.empty:
        estado_vacio("Sin productos abiertos.", "inventory_2")
    else:
        lista_stock([(r["Código"], r["Producto"], int(r["Disponible"]), int(r["Saldo inicial"]))
                     for _, r in stock.iterrows()])

seccion(f"Ventas del {ffecha(dia)}", tienda_nombre)
with tarjeta("tabla"):
    if ventas.empty:
        estado_vacio("Aún no hay ventas registradas.", "receipt_long")
    else:
        vista = ventas.drop(columns=["Fecha", "Tienda"]).copy()
        vista["Hora"] = vista["Hora"].map(lambda h: h.strftime("%H:%M"))
        vista = vista.rename(columns={"Precio unitario": "Precio unitario (Bs)", "Importe": "Importe (Bs)"})
        st.dataframe(vista, hide_index=True, width="stretch", column_config={
            "Cantidad": st.column_config.NumberColumn(format="%d pares"),
            "Precio unitario (Bs)": st.column_config.NumberColumn(format="localized"),
            "Importe (Bs)": st.column_config.NumberColumn(format="localized"),
        })
