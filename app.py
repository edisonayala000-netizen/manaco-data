"""Manaco Data — punto de entrada: login, navegación por rol y página de Inicio.

Ejecutar con: ``streamlit run app.py``
"""

from __future__ import annotations

import logging
import runpy
from datetime import date, timedelta

import pandas as pd
import streamlit as st
from sqlalchemy import func, select

from src import auth
from src.auth import ErrorAutenticacion
from src.config import BASE_DIR, PERMISOS, ROL_ADMIN, ROL_GERENCIA
from src.db import crear_tablas, obtener_sesion
from src.models import Usuario
from src.services import inventario as inv
from src.ui import graficos
from src.ui.comunes import ICONO_TOAST
from src.ui.estilos import (
    ICONOS, alerta, aplicar_estilos, aviso, bs, encabezado, estado_vacio, fecha, fecha_larga, ico, logo_sidebar,
    num, ranking, saludo, seccion, tarjeta, tarjeta_kpi, tarjeta_usuario,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("manaco")

st.set_page_config(page_title="Manaco Data", page_icon=":material/footprint:", layout="wide",
                   initial_sidebar_state="auto")
aplicar_estilos()


@st.cache_resource(show_spinner="Preparando la base de datos (solo la primera vez)…")
def _preparar_base() -> bool:
    """Crea las tablas si faltan y, en una instalación nueva, carga los datos iniciales (una vez por proceso)."""
    crear_tablas()
    _cargar_datos_iniciales()
    return True


def _cargar_datos_iniciales() -> None:
    """Si la base no tiene usuarios (p. ej. en Streamlit Community Cloud), ejecuta init_db y seed_demo."""
    with obtener_sesion() as s:
        if s.scalar(select(func.count(Usuario.id))):
            return
    log.info("Base nueva: cargando el Excel, el usuario admin y los datos de demostración")
    for script in ("init_db.py", "seed_demo.py", "seed_solucion.py", "seed_modulos.py"):
        runpy.run_path(str(BASE_DIR / "scripts" / script), run_name="__main__")


# --- Páginas definidas en este archivo ----------------------------------------

BENEFICIOS = (
    ("photo_camera", "Cierre diario con conteo por foto", "La IA cuenta los pares y usted confirma."),
    ("notifications_active", "Alertas de diferencias al instante", "Faltantes y sobrantes en cuanto se cierra."),
    ("monitoring", "Tablero de mercado con datos reales", "Comercio exterior de calzado integrado."),
)


def pagina_login() -> None:
    """Pantalla de ingreso en dos paneles: marca a la izquierda y tarjeta de login a la derecha."""
    izq, der = st.columns([55, 45], gap="large")
    with izq, st.container(key="login-panel"):
        beneficios = "".join(
            f'<div class="md-beneficio"><div class="ico">{ico(i)}</div><div><b>{t}</b><small>{s}</small></div></div>'
            for i, t, s in BENEFICIOS
        )
        st.markdown(
            '<div class="md-login-panel"><div class="logo">Manaco <span>Data</span></div>'
            '<div class="lema">Control de inventario diario y análisis del mercado de calzado</div>'
            f"{beneficios}</div>", unsafe_allow_html=True)
    with der, st.container(key="login-tarjeta"):
        st.markdown('<div class="md-login-logo-movil">Manaco <span>Data</span></div>'
                    '<div class="md-login-tit"><h2>Bienvenido</h2><p>Ingresa con tu cuenta</p></div>',
                    unsafe_allow_html=True)
        with st.form("login", border=False):
            usuario = st.text_input("Usuario", placeholder="Tu usuario", icon=":material/person:")
            contrasena = st.text_input("Contraseña", type="password", placeholder="Tu contraseña",
                                       icon=":material/lock:")
            entrar = st.form_submit_button("Ingresar", type="primary", width="stretch", icon=":material/login:")
        if entrar:
            try:
                with obtener_sesion() as s:
                    st.session_state["usuario"] = auth.autenticar(s, usuario, contrasena)
                st.rerun()
            except ErrorAutenticacion as exc:
                aviso(str(exc), "error")


def _variacion(actual: int, previo: int, sufijo: str) -> tuple[str | None, str | None]:
    """Texto y tendencia de la variación frente a ayer."""
    if previo == 0:
        return None, None
    delta = actual - previo
    signo = "+" if delta > 0 else ""
    return f"{signo}{num(delta)} {sufijo} vs. ayer", ("sube" if delta >= 0 else "baja")


def pagina_inicio() -> None:
    """Resumen del día: KPI con minigráficos, alertas, cierres por estado, ranking y diferencias."""
    usuario = auth.proteger_pagina("inicio")
    hoy = date.today()
    nombre_corto = usuario.nombre.split()[0] if usuario.nombre else usuario.usuario
    encabezado(f"{saludo()}, {nombre_corto}",
               f"Así está el inventario de todas las tiendas hoy, {fecha_larga(hoy)}.", ICONOS["inicio"])

    with obtener_sesion() as s:
        semana = [inv.indicadores_dia(s, hoy - timedelta(days=d)) for d in range(6, -1, -1)]
        alertas = [(c.id, c.fecha, c.tienda.nombre, c.producto.codigo_modelo, c.estado, c.diferencia, msg)
                   for c, msg in inv.alertas_pendientes(s)]
        cierres = inv.tabla_cierres(s)
    k, k_ayer = semana[-1], semana[-2]
    cierres["Fecha"] = pd.to_datetime(cierres["Fecha"])
    recientes = cierres[cierres["Fecha"] >= pd.Timestamp(hoy - timedelta(days=29))]
    dias = [pd.Timestamp(hoy - timedelta(days=d)) for d in range(6, -1, -1)]
    alertas_dia = (cierres[cierres["Estado"] != "Correcto"].groupby("Fecha").size()
                   .reindex(dias, fill_value=0).tolist())

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        var, tend = _variacion(k.pares_apertura, k_ayer.pares_apertura, "pares")
        tarjeta_kpi("Pares en apertura", num(k.pares_apertura), var, "inventory_2", "azul", tend,
                    serie=[d.pares_apertura for d in semana])
    with c2:
        tarjeta_kpi("Pares vendidos", num(k.pares_vendidos), bs(k.ventas_bs, 0), "shopping_bag", "verde",
                    serie=[d.pares_vendidos for d in semana])
    with c3:
        listo = k.cierres_hechos and not k.cierres_pendientes
        tarjeta_kpi("Cierres del día", f"{k.cierres_hechos} / {k.cierres_hechos + k.cierres_pendientes}",
                    "Todo cerrado" if listo else (f"{k.cierres_pendientes} por cerrar" if k.cierres_pendientes else None),
                    "fact_check", "morado", "sube" if listo else None, serie=[d.cierres_hechos for d in semana])
    with c4:
        tarjeta_kpi("Alertas activas", num(len(alertas)), "Requieren revisión" if alertas else "Sin pendientes",
                    "notifications_active", "rojo", "baja" if alertas else "sube", alerta=bool(alertas),
                    serie=alertas_dia)

    izq, der = st.columns([60, 40], gap="medium")
    with izq, tarjeta("alertas", "Alertas pendientes", f"{len(alertas)} diferencias sin revisar", "warning"):
        if not alertas:
            estado_vacio("No hay alertas pendientes. Todos los cierres cuadran.", "verified")
        else:
            for _, f, tienda, _, estado, dif, msg in alertas[:5]:
                alerta(msg, estado, diferencia=dif, tienda=tienda, detalle=f"Cierre del {fecha(f)}")
            with st.expander(f"Ver todas ({len(alertas)})", icon=":material/list:"):
                tabla = pd.DataFrame(alertas, columns=["id", "Fecha", "Tienda", "Código", "Estado", "Diferencia",
                                                       "Mensaje"])
                tabla["Fecha"] = pd.to_datetime(tabla["Fecha"]).dt.strftime("%d/%m/%Y")
                st.dataframe(tabla.drop(columns="id"), hide_index=True, width="stretch",
                             column_config={"Diferencia": st.column_config.NumberColumn(format="%+d")})
                if usuario.rol in (ROL_ADMIN, ROL_GERENCIA):
                    opciones = {f"{fecha(f)} · {msg}": cid for cid, f, _, _, _, _, msg in alertas}
                    elegidas = st.multiselect("Marcar como revisadas", list(opciones),
                                              placeholder="Elija una o más alertas")
                    if st.button("Marcar como revisadas", disabled=not elegidas, icon=":material/done_all:"):
                        with obtener_sesion() as s:
                            for etiqueta in elegidas:
                                inv.marcar_alerta_atendida(s, opciones[etiqueta])
                        st.toast(f"{len(elegidas)} alerta(s) marcadas como revisadas.", icon=ICONO_TOAST["success"])
                        st.rerun()
    with der:
        with tarjeta("estados"):
            st.plotly_chart(graficos.grafico_estados(recientes), width="stretch", theme=None, config={"displayModeBar": False})
        with tarjeta("ranking", "Tiendas con más diferencias", "Pares descuadrados en los últimos 30 días",
                     "leaderboard"):
            con_dif = recientes[recientes["Diferencia"] != 0]
            top = (con_dif.assign(abs_dif=con_dif["Diferencia"].abs()).groupby("Tienda")
                   .agg(pares=("abs_dif", "sum"), cierres=("abs_dif", "size")).sort_values("pares", ascending=False))
            ranking([(t, f"{int(r.cierres)} cierres con diferencia", f"{int(r.pares)} pares")
                     for t, r in top.head(5).iterrows()])

    seccion("Diferencias de inventario", "Faltantes y sobrantes por día en los últimos 30 días")
    with tarjeta("diferencias"):
        st.plotly_chart(graficos.grafico_diferencias(recientes), width="stretch", theme=None,
                        config={"displayModeBar": False})


# --- Navegación ---------------------------------------------------------------

PAGINAS: list[tuple[str, object, str, str]] = [
    # clave, origen, título, ruta url
    ("inicio", pagina_inicio, "Inicio", "inicio"),
    ("apertura", "pages/1_Apertura.py", "Apertura", "apertura"),
    ("ventas", "pages/2_Ventas.py", "Ventas", "ventas"),
    ("cierre", "pages/3_Cierre_y_conteo.py", "Cierre y conteo", "cierre"),
    ("historial", "pages/4_Historial.py", "Historial", "historial"),
    ("tablero", "pages/5_Tablero_de_mercado.py", "Tablero de mercado", "tablero"),
    ("catalogo", "pages/6_Catalogo.py", "Catálogo", "catalogo"),
    ("usuarios", "pages/7_Usuarios.py", "Usuarios", "usuarios"),
    ("pronostico", "pages/8_Pronostico_demanda.py", "Pronóstico de demanda", "pronostico"),
    ("escenario", "pages/9_Prototipo_escenario.py", "Prototipo de escenario", "escenario"),
    ("entregables", "pages/10_Entregables_escritos.py", "Entregables escritos", "entregables"),
    ("inventario", "pages/11_Inventario_y_Compras.py", "Inventario y compras", "inventario"),
    ("clientes", "pages/12_Clientes_y_Segmentacion.py", "Clientes y segmentación", "clientes"),
    ("recomendaciones", "pages/13_Recomendaciones.py", "Recomendaciones", "recomendaciones"),
    ("marketing", "pages/14_Marketing_y_Promociones.py", "Marketing y promociones", "marketing"),
    ("contabilidad", "pages/15_Contabilidad.py", "Contabilidad", "contabilidad"),
]


def barra_lateral(usuario: auth.UsuarioSesion) -> None:
    """Tarjeta del usuario conectado y botón para cerrar sesión."""
    with st.sidebar:
        tarjeta_usuario(usuario.nombre, usuario.usuario, usuario.rol)
        if st.button("Cerrar sesión", width="stretch", icon=":material/logout:"):
            st.session_state.clear()
            st.rerun()


def main() -> None:
    """Muestra el login o las páginas permitidas para el rol del usuario."""
    try:
        _preparar_base()
    except Exception:  # noqa: BLE001
        log.exception("No se pudo preparar la base de datos")
        aviso("No se pudo abrir la base de datos. Ejecute python scripts/init_db.py y vuelva a intentar.", "error")
        st.stop()

    usuario = auth.usuario_actual()
    if usuario is None:
        navegacion = st.navigation([st.Page(pagina_login, title="Ingresar", icon=":material/login:")],
                                   position="hidden")
    else:
        logo_sidebar()
        paginas = [
            st.Page(origen, title=titulo, icon=f":material/{ICONOS[clave]}:", url_path=ruta, default=not i)
            for i, (clave, origen, titulo, ruta) in enumerate(p for p in PAGINAS if usuario.rol in PERMISOS[p[0]])
        ]
        navegacion = st.navigation(paginas)
        barra_lateral(usuario)

    try:
        navegacion.run()
    except Exception:  # noqa: BLE001 — nunca mostrar un traceback al usuario
        log.exception("Error no controlado en la página %s", navegacion.title)
        aviso("Ocurrió un problema inesperado en esta página. Intente de nuevo; "
              "si persiste, avise al administrador.", "error")


main()
