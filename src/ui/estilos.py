"""Identidad visual de Manaco Data: CSS global, formatos y componentes reutilizables.

Todo el CSS del sistema vive en este módulo; las páginas solo llaman a estas funciones.
Los íconos son *Material Symbols* (los mismos que usa Streamlit con ``:material/...:``).
"""

from __future__ import annotations

import html
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import date, datetime

import streamlit as st
from streamlit.errors import StreamlitAPIException

from src.config import BASE_DIR

ASSETS_DIR = BASE_DIR / "assets"

# --- Paleta ------------------------------------------------------------------
PRIMARIO = "#D62839"
PRIMARIO_OSCURO = "#A4161A"
TEXTO = "#111827"
TEXTO_2 = "#6B7280"
FONDO = "#F5F6FA"
EXITO, EXITO_FONDO = "#16A34A", "#DCFCE7"
ADVERTENCIA, ADVERTENCIA_FONDO = "#F59E0B", "#FEF3C7"
ERROR, ERROR_FONDO = "#DC2626", "#FEE2E2"
INFO, INFO_FONDO = "#2563EB", "#DBEAFE"
MORADO = "#7C3AED"

#: Color de cada categoría de calzado (gráficos y chips).
COLOR_CATEGORIA: dict[str, str] = {
    "Deportivo": "#2563EB", "Caucho y cuero": "#7C3AED", "Cuero": PRIMARIO, "Medias": "#0D9488",
}
#: Color de cada estado de cierre.
COLOR_ESTADO: dict[str, str] = {"Correcto": EXITO, "Faltante": ERROR, "Sobrante": ADVERTENCIA}
#: Nombre corto de color → hex (para tarjetas KPI y chips).
COLORES: dict[str, str] = {
    "rojo": PRIMARIO, "azul": INFO, "verde": EXITO, "morado": MORADO, "naranja": ADVERTENCIA, "gris": TEXTO_2,
}
COLOR_ROL: dict[str, str] = {"administrador": PRIMARIO, "encargado": INFO, "gerencia": MORADO}

#: Íconos Material de cada página (navegación y encabezados).
ICONOS: dict[str, str] = {
    "inicio": "home", "apertura": "inventory_2", "ventas": "point_of_sale", "cierre": "photo_camera",
    "historial": "history", "tablero": "monitoring", "pronostico": "trending_up", "escenario": "tune",
    "entregables": "assignment", "catalogo": "category", "usuarios": "group",
    "inventario": "inventory", "clientes": "groups", "recomendaciones": "recommend",
    "marketing": "campaign", "contabilidad": "account_balance",
}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,400..600,0..1,0&display=swap');
:root {{
  --md-primario: {PRIMARIO}; --md-primario-osc: {PRIMARIO_OSCURO};
  --md-texto: {TEXTO}; --md-texto-2: {TEXTO_2}; --md-fondo: {FONDO};
  --md-borde: #E5E7EB; --md-borde-suave: #EEF0F4;
  --md-exito: {EXITO}; --md-exito-f: {EXITO_FONDO};
  --md-adv: {ADVERTENCIA}; --md-adv-f: {ADVERTENCIA_FONDO};
  --md-error: {ERROR}; --md-error-f: {ERROR_FONDO};
  --md-info: {INFO}; --md-info-f: {INFO_FONDO};
  --md-sombra: 0 4px 20px rgba(17,24,39,.06);
  --md-sombra-hover: 0 10px 28px rgba(17,24,39,.11);
  --md-radio: 14px; --md-radio-sm: 10px;
  --md-titulos: 'Plus Jakarta Sans', 'Inter', sans-serif;
  --md-trans: all .18s ease;
}}

/* ---------- Base ---------- */
.stApp {{ background: var(--md-fondo); }}
h1, h2, h3, h4, h5 {{ font-family: var(--md-titulos) !important; color: var(--md-texto); letter-spacing: -.01em; }}
.block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1240px; }}
.ms {{ font-family: 'Material Symbols Rounded'; font-weight: normal; font-style: normal; line-height: 1;
       display: inline-block; vertical-align: middle; font-feature-settings: 'liga'; -webkit-font-smoothing: antialiased;
       font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24; text-transform: none; letter-spacing: normal; }}

/* Ocultar marca de Streamlit y textos en inglés */
#MainMenu, footer, [data-testid="stAppDeployButton"], [data-testid="stMainMenu"],
[data-testid="stStatusWidget"], [data-testid="InputInstructions"] {{ display: none !important; }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stDecoration"] {{ display: none; }}
[data-testid="stHeaderActionElements"] {{ display: none !important; }}  /* ícono de enlace junto a los títulos */

/* ---------- Barra lateral ---------- */
[data-testid="stSidebar"] {{ background: linear-gradient(180deg, #111827 0%, #1F2937 100%); }}
[data-testid="stSidebarContent"] {{ display: flex; flex-direction: column; }}
[data-testid="stSidebarUserContent"] {{ margin-top: auto; padding-bottom: 1.2rem; }}
[data-testid="stSidebarHeader"] {{ padding-top: 1.3rem; padding-bottom: .6rem; }}
[data-testid="stSidebarHeader"] img, [data-testid="stLogo"] {{ height: 3.1rem !important; max-width: 100%; }}
[data-testid="stSidebarNavLink"] {{ border-radius: var(--md-radio-sm); margin: 2px 10px; padding: .55rem .8rem;
                                    transition: var(--md-trans); }}
[data-testid="stSidebarNavLink"] span {{ color: #D1D5DB !important; font-weight: 500; }}
[data-testid="stSidebarNavLink"] [data-testid="stIconMaterial"] {{ color: #9CA3AF !important; }}
[data-testid="stSidebarNavLink"]:hover {{ background: rgba(255,255,255,.07); }}
[data-testid="stSidebarNavLink"]:hover span {{ color: #FFFFFF !important; }}
[data-testid="stSidebarNavLink"][aria-current="page"] {{
  background: linear-gradient(135deg, var(--md-primario), var(--md-primario-osc));
  box-shadow: 0 6px 16px rgba(214,40,57,.35); }}
[data-testid="stSidebarNavLink"][aria-current="page"] span,
[data-testid="stSidebarNavLink"][aria-current="page"] [data-testid="stIconMaterial"] {{ color: #FFFFFF !important; font-weight: 600; }}
[data-testid="stSidebarNavSeparator"] {{ display: none; }}
.md-usuario {{ display: flex; align-items: center; gap: .7rem; background: rgba(255,255,255,.05);
               border: 1px solid rgba(255,255,255,.08); border-radius: var(--md-radio); padding: .8rem; margin: 0 0 .7rem 0; }}
.md-avatar {{ width: 42px; height: 42px; min-width: 42px; border-radius: 50%; display: flex; align-items: center;
              justify-content: center; font-family: var(--md-titulos); font-weight: 800; color: #fff; font-size: .95rem;
              background: linear-gradient(135deg, var(--md-primario), var(--md-primario-osc)); }}
.md-usuario .nom {{ color: #F9FAFB; font-weight: 600; font-size: .92rem; line-height: 1.2; }}
.md-usuario .arroba {{ color: #9CA3AF; font-size: .78rem; }}
.md-insignia {{ display: inline-block; font-size: .64rem; font-weight: 700; text-transform: uppercase; letter-spacing: .07em;
                padding: .14rem .5rem; border-radius: 999px; margin-top: .25rem; }}
[data-testid="stSidebar"] .stButton button {{ background: transparent !important; border: 1px solid #4B5563 !important;
                                              color: #E5E7EB !important; box-shadow: none !important; }}
[data-testid="stSidebar"] .stButton button:hover {{ border-color: var(--md-primario) !important; color: #FFFFFF !important;
                                                    background: rgba(214,40,57,.15) !important; }}

/* ---------- Banner de encabezado ---------- */
.md-banner {{ position: relative; overflow: hidden; border-radius: 18px; padding: 1.5rem 1.7rem; margin-bottom: 1.4rem;
              background: linear-gradient(120deg, var(--md-primario) 0%, var(--md-primario-osc) 100%);
              color: #fff; display: flex; align-items: center; gap: 1.1rem; box-shadow: 0 12px 30px rgba(164,22,26,.25); }}
.md-banner::before, .md-banner::after {{ content: ""; position: absolute; border-radius: 50%; background: rgba(255,255,255,.08); }}
.md-banner::before {{ width: 260px; height: 260px; right: -60px; top: -120px; }}
.md-banner::after {{ width: 160px; height: 160px; right: 200px; bottom: -100px; }}
.md-banner .circ {{ width: 58px; height: 58px; min-width: 58px; border-radius: 50%; background: rgba(255,255,255,.16);
                    display: flex; align-items: center; justify-content: center; z-index: 1; }}
.md-banner .circ .ms {{ font-size: 30px; color: #fff; }}
.md-banner .txt {{ flex: 1; z-index: 1; min-width: 0; }}
.md-banner h1 {{ color: #fff !important; font-size: 1.65rem !important; font-weight: 800; margin: 0; padding: 0 !important; line-height: 1.2; }}
.md-banner p {{ margin: .25rem 0 0 0; color: rgba(255,255,255,.88); font-size: .95rem; }}
.md-banner .fecha {{ z-index: 1; text-align: right; background: rgba(255,255,255,.14); border-radius: 12px;
                     padding: .5rem .9rem; font-size: .8rem; white-space: nowrap; }}
.md-banner .fecha b {{ display: block; font-family: var(--md-titulos); font-size: 1.05rem; }}

/* ---------- Tarjetas KPI ---------- */
.md-kpi {{ position: relative; background: #fff; border-radius: var(--md-radio); padding: 1.05rem 1.15rem 1rem;
           box-shadow: var(--md-sombra); border: 1px solid var(--md-borde-suave); height: 100%; transition: var(--md-trans); }}
.md-kpi:hover {{ transform: translateY(-2px); box-shadow: var(--md-sombra-hover); }}
.md-kpi.alerta {{ border-left: 4px solid var(--md-error); }}
.md-kpi .cab {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: .55rem; }}
.md-chip-ico {{ width: 38px; height: 38px; border-radius: 11px; display: flex; align-items: center; justify-content: center; }}
.md-chip-ico .ms {{ font-size: 21px; }}
.md-kpi .lbl {{ font-size: .7rem; color: var(--md-texto-2); text-transform: uppercase; letter-spacing: .07em; font-weight: 600; }}
.md-kpi .val {{ font-family: var(--md-titulos); font-weight: 800; font-size: 2.2rem; color: var(--md-texto);
                line-height: 1.15; font-variant-numeric: tabular-nums; white-space: nowrap; margin: .1rem 0 .35rem; }}
.md-kpi .pie {{ display: flex; align-items: flex-end; justify-content: space-between; gap: .4rem; min-height: 24px; }}
.md-var {{ display: inline-flex; align-items: center; gap: .2rem; font-size: .74rem; font-weight: 600; border-radius: 999px;
           padding: .14rem .55rem; white-space: nowrap; }}
.md-var.sube {{ background: var(--md-exito-f); color: #15803D; }}
.md-var.baja {{ background: var(--md-error-f); color: #B91C1C; }}
.md-var.neutra {{ background: #F3F4F6; color: var(--md-texto-2); }}
.md-pulso {{ width: 10px; height: 10px; border-radius: 50%; background: var(--md-error); position: relative; margin-right: 4px; }}
.md-pulso::after {{ content: ""; position: absolute; inset: 0; border-radius: 50%; background: var(--md-error);
                    animation: md-pulso 1.6s ease-out infinite; }}
@keyframes md-pulso {{ 0% {{ transform: scale(1); opacity: .7; }} 100% {{ transform: scale(3); opacity: 0; }} }}
.md-spark {{ display: block; }}
.md-kpi.mini {{ padding: .8rem 1rem; }}
.md-kpi.mini .cab {{ margin-bottom: .35rem; }}
.md-kpi.mini .val {{ font-size: 1.6rem; margin: 0 0 .15rem; }}

/* ---------- Banner oscuro de KPI (tablero) ---------- */
.md-banner-oscuro {{ background: linear-gradient(120deg, #111827, #1F2937); border-radius: 18px; padding: 1.3rem 1.4rem;
                     display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 1rem; margin-bottom: 1.2rem;
                     box-shadow: 0 12px 30px rgba(17,24,39,.22); }}
.md-banner-oscuro .it {{ border-left: 3px solid var(--c, var(--md-primario)); padding-left: .85rem; }}
.md-banner-oscuro .lbl {{ color: #9CA3AF; font-size: .7rem; text-transform: uppercase; letter-spacing: .08em; font-weight: 600; }}
.md-banner-oscuro .val {{ color: #fff; font-family: var(--md-titulos); font-weight: 800; font-size: 1.85rem;
                          font-variant-numeric: tabular-nums; line-height: 1.2; white-space: nowrap; }}
.md-banner-oscuro .sub {{ color: #D1D5DB; font-size: .78rem; }}

/* ---------- Alertas de inventario y avisos ---------- */
.md-alerta {{ display: flex; align-items: center; gap: .9rem; background: var(--f); border-left: 4px solid var(--c);
              border-radius: 12px; padding: .8rem 1rem; margin: 0 0 .6rem 0; transition: var(--md-trans); }}
.md-alerta:hover {{ transform: translateX(2px); }}
.md-alerta .ico {{ width: 34px; height: 34px; min-width: 34px; border-radius: 50%; background: #fff; display: flex;
                   align-items: center; justify-content: center; color: var(--c); box-shadow: 0 2px 6px rgba(0,0,0,.06); }}
.md-alerta .ico .ms {{ font-size: 20px; }}
.md-alerta .cuerpo {{ flex: 1; min-width: 0; }}
.md-alerta .msg {{ font-weight: 600; color: var(--md-texto); font-size: .93rem; line-height: 1.35; }}
.md-alerta .det {{ color: var(--md-texto-2); font-size: .78rem; margin-top: .1rem; }}
.md-alerta .pastas {{ display: flex; flex-direction: column; align-items: flex-end; gap: .25rem; }}
.md-pastilla {{ display: inline-flex; align-items: center; gap: .25rem; font-size: .74rem; font-weight: 700; border-radius: 999px;
                padding: .18rem .62rem; white-space: nowrap; }}
.md-pastilla .ms {{ font-size: 15px; }}
.md-aviso {{ display: flex; align-items: center; gap: .7rem; background: var(--f); color: var(--t); border: 1px solid var(--b);
             border-radius: 12px; padding: .7rem .95rem; margin: .2rem 0 .8rem 0; font-size: .92rem; font-weight: 500; }}
.md-aviso .ms {{ font-size: 21px; color: var(--c); }}

/* ---------- Estado vacío ---------- */
.md-vacio {{ text-align: center; padding: 2rem 1rem 1rem; color: var(--md-texto-2); }}
.md-vacio .ms {{ font-size: 54px; color: #D1D5DB; }}
.md-vacio p {{ margin: .6rem auto 0; max-width: 440px; font-size: .95rem; }}
[class*="st-key-vacio-accion"] {{ display: flex; align-items: center; padding-bottom: 1.2rem; }}
[class*="st-key-vacio-accion"] [data-testid="stPageLink"] {{ display: flex; justify-content: center; width: 100%; }}
[class*="st-key-vacio-accion"] a {{ background: linear-gradient(135deg, var(--md-primario), var(--md-primario-osc)) !important;
                          border-radius: var(--md-radio-sm); padding: .4rem 1.1rem !important; width: auto !important;
                          box-shadow: 0 6px 16px rgba(214,40,57,.28); }}
[class*="st-key-vacio-accion"] a span, [class*="st-key-vacio-accion"] a p {{ color: #fff !important; font-weight: 600; }}

/* ---------- Tarjetas (contenedores con key "tarjeta-…") ---------- */
[class*="st-key-tarjeta"] {{ background: #fff; border-radius: var(--md-radio) !important; box-shadow: var(--md-sombra);
                             border: 1px solid var(--md-borde-suave) !important; padding: 1.15rem 1.25rem !important;
                             transition: box-shadow .18s ease; }}
[class*="st-key-tarjeta"]:hover {{ box-shadow: var(--md-sombra-hover); }}
.md-tit {{ display: flex; align-items: center; gap: .55rem; margin: 0 0 .15rem 0; }}
.md-tit .ms {{ font-size: 21px; color: var(--md-primario); }}
.md-tit h3 {{ font-size: 1.06rem !important; font-weight: 700; margin: 0 !important; padding: 0 !important; }}
.md-sub {{ color: var(--md-texto-2); font-size: .84rem; margin: 0 0 .5rem 0; }}
.md-seccion {{ margin: 1.3rem 0 .6rem; }}
.md-seccion h3 {{ font-size: 1.15rem !important; margin: 0 !important; padding: 0 !important; }}
.md-seccion p {{ margin: .1rem 0 0; color: var(--md-texto-2); font-size: .86rem; }}

/* ---------- Formularios ---------- */
[data-testid="stForm"] {{ border: none; padding: 0; }}
[data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] {{
  background: #fff !important; border-color: var(--md-borde) !important; border-radius: var(--md-radio-sm) !important;
  transition: var(--md-trans); }}
[data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within, [data-baseweb="textarea"]:focus-within {{
  border-color: var(--md-primario) !important; box-shadow: 0 0 0 3px rgba(214,40,57,.14) !important; }}
[data-baseweb="input"] input, [data-baseweb="input"] > div, [data-baseweb="textarea"] textarea {{ background: #fff !important; }}
[data-testid="stWidgetLabel"] p {{ font-weight: 600; color: #374151; font-size: .86rem; }}
.stButton button, .stFormSubmitButton button, .stDownloadButton button {{ border-radius: var(--md-radio-sm); font-weight: 600;
  transition: var(--md-trans); }}
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {{
  background: linear-gradient(135deg, var(--md-primario), var(--md-primario-osc)) !important; border: none !important;
  color: #fff !important; box-shadow: 0 6px 16px rgba(214,40,57,.28); }}
[data-testid="stBaseButton-primary"]:hover, [data-testid="stBaseButton-primaryFormSubmit"]:hover {{
  filter: brightness(.93); transform: translateY(-1px); box-shadow: 0 10px 22px rgba(214,40,57,.34); }}
[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-secondaryFormSubmit"] {{
  background: #fff !important; border: 1px solid var(--md-borde) !important; color: #374151 !important; }}
[data-testid="stBaseButton-secondary"]:hover, [data-testid="stBaseButton-secondaryFormSubmit"]:hover {{
  border-color: var(--md-primario) !important; color: var(--md-primario) !important; }}
[data-testid="stFileUploaderDropzone"] {{ background: #FAFAFB; border: 2px dashed #D1D5DB; border-radius: var(--md-radio); }}

/* ---------- Pestañas como pastillas segmentadas ---------- */
.stTabs [role="tablist"] {{ background: #E9EBF0; border-radius: 12px; padding: 4px; gap: 4px; width: fit-content;
                            max-width: 100%; overflow-x: auto; border: none !important; box-shadow: none !important; }}
.stTabs [data-testid="stTab"] {{ border-radius: 9px; padding: .45rem 1.05rem; background: transparent; border: none !important;
                                 color: var(--md-texto-2); transition: var(--md-trans); }}
.stTabs [data-testid="stTab"] p {{ font-weight: 600; color: inherit; }}
.stTabs [data-testid="stTab"]:hover {{ color: var(--md-texto); }}
.stTabs [data-testid="stTab"][aria-selected="true"] {{ background: #fff; color: var(--md-primario);
                                                       box-shadow: 0 2px 8px rgba(17,24,39,.1); }}
.stTabs [data-testid="stTab"]::after, .stTabs [data-testid="stTab"]::before {{ display: none !important; }}
.stTabs [role="tabpanel"] {{ padding-top: 1rem; }}

/* ---------- Tablas, gráficos, expanders ---------- */
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {{ border-radius: 12px; overflow: hidden; }}
[data-testid="stPlotlyChart"] {{ animation: md-entrada .5s ease both; }}
[data-testid="stPlotlyChart"] .main-svg {{ background: transparent !important; }}
@keyframes md-entrada {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: none; }} }}
[data-testid="stExpander"] details {{ background: #fff; border-radius: 12px; border-color: var(--md-borde-suave); }}

/* ---------- Asistente de pasos ---------- */
.md-pasos {{ display: flex; align-items: center; background: #fff; border-radius: var(--md-radio); padding: .9rem 1.2rem;
             box-shadow: var(--md-sombra); margin-bottom: 1.1rem; gap: .5rem; }}
.md-paso {{ display: flex; align-items: center; gap: .55rem; color: #9CA3AF; font-weight: 600; font-size: .9rem; white-space: nowrap; }}
.md-paso .n {{ width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
               background: #F3F4F6; color: #9CA3AF; font-family: var(--md-titulos); font-weight: 800; }}
.md-paso .n .ms {{ font-size: 18px; }}
.md-paso.hecho .n {{ background: var(--md-exito); color: #fff; }}
.md-paso.hecho {{ color: var(--md-texto); }}
.md-paso.activo .n {{ background: linear-gradient(135deg, var(--md-primario), var(--md-primario-osc)); color: #fff;
                      box-shadow: 0 0 0 5px rgba(214,40,57,.15); }}
.md-paso.activo {{ color: var(--md-primario); }}
.md-linea {{ flex: 1; height: 3px; border-radius: 3px; background: #E5E7EB; min-width: 20px; }}
.md-linea.hecha {{ background: var(--md-exito); }}

/* ---------- Resultado de cierre ---------- */
.md-resultado {{ border-radius: 18px; padding: 1.5rem; background: var(--f); border: 2px solid var(--c); margin: .4rem 0 1rem; }}
.md-resultado .top {{ display: flex; align-items: center; gap: 1rem; }}
.md-resultado .grande {{ width: 64px; height: 64px; min-width: 64px; border-radius: 50%; background: var(--c); color: #fff;
                         display: flex; align-items: center; justify-content: center; }}
.md-resultado .grande .ms {{ font-size: 38px; }}
.md-resultado h2 {{ margin: 0 !important; padding: 0 !important; font-size: 1.55rem !important; color: var(--t) !important; }}
.md-resultado .msg {{ color: var(--t); font-weight: 500; margin-top: .15rem; }}
.md-bloques {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: .8rem; margin-top: 1.1rem; }}
.md-bloque {{ background: #fff; border-radius: 12px; padding: .8rem 1rem; text-align: center; }}
.md-bloque .lbl {{ font-size: .7rem; color: var(--md-texto-2); text-transform: uppercase; letter-spacing: .07em; font-weight: 600; }}
.md-bloque .val {{ font-family: var(--md-titulos); font-weight: 800; font-size: 1.9rem; font-variant-numeric: tabular-nums; }}
.md-conteo {{ text-align: center; padding: .4rem 0 .8rem; }}
.md-conteo .num {{ font-family: var(--md-titulos); font-weight: 800; font-size: 4rem; line-height: 1; color: var(--md-texto); }}
.md-conteo .uni {{ color: var(--md-texto-2); font-weight: 600; margin-top: .3rem; }}
.md-etq {{ font-size: .72rem; color: var(--md-texto-2); font-weight: 600; text-transform: uppercase; letter-spacing: .06em; }}
.md-barra {{ height: 10px; border-radius: 999px; background: #EEF0F4; overflow: hidden; margin: .4rem 0 .2rem; }}
.md-barra > div {{ height: 100%; border-radius: 999px; background: var(--c, var(--md-primario)); transition: width .4s ease; }}

/* ---------- Stock con barras ---------- */
.md-stock {{ display: flex; flex-direction: column; gap: .6rem; }}
.md-stock .fila {{ display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(0, 2fr) 3.8rem; gap: .8rem; align-items: center; }}
.md-stock .cod {{ font-weight: 700; font-size: .85rem; color: var(--md-texto); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.md-stock .nom {{ font-size: .74rem; color: var(--md-texto-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.md-stock .cant {{ text-align: right; font-weight: 700; font-variant-numeric: tabular-nums; font-size: .92rem; }}
.md-stock .cant small {{ color: var(--md-texto-2); font-weight: 500; }}

/* ---------- Sugerencia, notas, línea de tiempo, grillas ---------- */
.md-sugerencia {{ display: flex; gap: .8rem; align-items: center; background: #FFFBEB; border: 1px solid #FDE68A;
                  border-radius: 12px; padding: .75rem 1rem; margin: .3rem 0 .9rem; color: #78350F; font-size: .92rem; }}
.md-sugerencia .ms {{ color: var(--md-adv); font-size: 24px; }}
.md-nota {{ background: #fff; border-left: 4px solid var(--md-primario); border-radius: 12px; padding: 1rem 1.2rem;
            color: #374151; font-size: .9rem; box-shadow: var(--md-sombra); margin-top: .6rem; }}
.md-nota .tt {{ display: flex; align-items: center; gap: .45rem; font-weight: 700; color: var(--md-texto); }}
.md-nota .tt .ms {{ color: var(--md-primario); font-size: 20px; }}
.md-nota ul {{ margin: .4rem 0 0 1.1rem; padding: 0; }}
.md-tiempo {{ position: relative; padding-left: 2.6rem; }}
.md-tiempo::before {{ content: ""; position: absolute; left: 15px; top: 10px; bottom: 10px; width: 2px; background: #E5E7EB; }}
.md-hito {{ position: relative; background: #fff; border-radius: 12px; padding: .75rem 1rem; margin-bottom: .7rem;
            box-shadow: var(--md-sombra); }}
.md-hito .pt {{ position: absolute; left: -2.6rem; top: .7rem; width: 32px; height: 32px; border-radius: 50%; background: var(--c);
                color: #fff; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 0 4px var(--md-fondo); }}
.md-hito .pt .ms {{ font-size: 18px; }}
.md-hito b {{ font-size: .93rem; }}
.md-hito p {{ margin: .15rem 0 0; color: var(--md-texto-2); font-size: .83rem; }}
.md-flujo {{ display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap; margin: .3rem 0 1.2rem; }}
.md-flujo .caja {{ background: #fff; border-radius: 14px; padding: .8rem 1.5rem; text-align: center; box-shadow: var(--md-sombra); }}
.md-flujo .caja .val {{ font-family: var(--md-titulos); font-weight: 800; font-size: 2rem; color: var(--c, var(--md-texto)); }}
.md-flujo .caja .lbl {{ font-size: .72rem; color: var(--md-texto-2); text-transform: uppercase; letter-spacing: .06em; font-weight: 600; }}
.md-flujo > .ms {{ font-size: 30px; color: #9CA3AF; }}
.md-grilla {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(215px, 1fr)); gap: .8rem; margin-bottom: 1rem; }}
.md-ficha {{ background: #fff; border-radius: var(--md-radio); padding: .9rem 1rem; box-shadow: var(--md-sombra);
             border: 1px solid var(--md-borde-suave); transition: var(--md-trans); display: flex; flex-direction: column; gap: .3rem; }}
.md-ficha:hover {{ transform: translateY(-2px); box-shadow: var(--md-sombra-hover); }}
.md-ficha .cab {{ display: flex; align-items: center; justify-content: space-between; gap: .4rem; flex-wrap: wrap; }}
.md-ficha .cod {{ font-family: var(--md-titulos); font-weight: 800; font-size: .95rem; white-space: nowrap; }}
.md-ficha .nom {{ font-size: .88rem; color: #374151; font-weight: 500; }}
.md-ficha .det {{ font-size: .76rem; color: var(--md-texto-2); }}
.md-ficha .precio {{ font-family: var(--md-titulos); font-weight: 800; font-size: 1.1rem; margin-top: .2rem; }}
.md-ficha.inactiva {{ opacity: .55; }}
.md-ficha .persona {{ display: flex; align-items: center; gap: .65rem; }}
.md-ranking .fila {{ display: flex; align-items: center; gap: .7rem; padding: .55rem 0; border-bottom: 1px solid var(--md-borde-suave); }}
.md-ranking .fila:last-child {{ border-bottom: none; }}
.md-ranking .pos {{ width: 28px; height: 28px; min-width: 28px; border-radius: 8px; background: #F3F4F6; display: flex;
                    align-items: center; justify-content: center; font-weight: 800; font-size: .82rem; color: var(--md-texto-2); }}
.md-ranking .pos.p1 {{ background: var(--md-error-f); color: var(--md-error); }}
.md-ranking .nom {{ flex: 1; font-weight: 600; font-size: .9rem; min-width: 0; }}
.md-ranking .nom small {{ display: block; color: var(--md-texto-2); font-weight: 500; font-size: .76rem; }}

/* ---------- Login ---------- */
.md-login-panel {{ position: relative; overflow: hidden; min-height: 84vh; border-radius: 22px; padding: 3rem 2.6rem; color: #fff;
                   background: linear-gradient(150deg, var(--md-primario) 0%, var(--md-primario-osc) 45%, #111827 100%);
                   display: flex; flex-direction: column; justify-content: center; }}
.md-login-panel::before {{ content: ""; position: absolute; width: 420px; height: 420px; border-radius: 50%;
                           background: rgba(255,255,255,.07); right: -140px; top: -120px; }}
.md-login-panel::after {{ content: ""; position: absolute; width: 260px; height: 260px; border-radius: 50%;
                          background: rgba(255,255,255,.06); left: -90px; bottom: -80px; }}
.md-login-panel > * {{ position: relative; z-index: 1; }}
.md-login-panel .logo {{ font-family: var(--md-titulos); font-weight: 800; font-size: 3rem; letter-spacing: -.02em; line-height: 1.1; }}
.md-login-panel .logo span {{ color: #FECACA; }}
.md-login-panel .lema {{ font-size: 1.15rem; color: rgba(255,255,255,.9); max-width: 430px; margin: .7rem 0 2.2rem; }}
.md-beneficio {{ display: flex; align-items: center; gap: .9rem; margin-bottom: 1.1rem; }}
.md-beneficio .ico {{ width: 44px; height: 44px; min-width: 44px; border-radius: 12px; background: rgba(255,255,255,.14);
                      display: flex; align-items: center; justify-content: center; }}
.md-beneficio .ico .ms {{ font-size: 23px; color: #fff; }}
.md-beneficio b {{ display: block; font-size: .98rem; }}
.md-beneficio small {{ color: rgba(255,255,255,.78); font-size: .82rem; }}
.st-key-login-tarjeta {{ background: #fff; border-radius: 22px; box-shadow: 0 20px 50px rgba(17,24,39,.10);
                         padding: 2.4rem 2.2rem !important; margin-top: 14vh; border: 1px solid var(--md-borde-suave); }}
.md-login-tit h2 {{ font-size: 1.9rem !important; font-weight: 800; margin: 0 !important; padding: 0 !important; }}
.md-login-tit p {{ color: var(--md-texto-2); margin: .3rem 0 1.2rem; }}
.md-login-logo-movil {{ display: none; font-family: var(--md-titulos); font-weight: 800; font-size: 1.6rem; margin-bottom: 1rem; }}
.md-login-logo-movil span {{ color: var(--md-primario); }}

/* ---------- Responsive ---------- */
@media (max-width: 760px) {{
  .block-container {{ padding-left: 1rem; padding-right: 1rem; padding-top: 3.6rem; }}
  .md-banner {{ padding: 1.1rem 1.1rem; gap: .8rem; }}
  .md-banner h1 {{ font-size: 1.25rem !important; }}
  .md-banner .fecha {{ display: none; }}
  .md-banner .circ {{ width: 46px; height: 46px; min-width: 46px; }}
  .md-kpi .val {{ font-size: 1.75rem; }}
  .md-bloque .val {{ font-size: 1.45rem; }}
  .md-pasos .md-paso span.t {{ display: none; }}
  .st-key-login-panel {{ display: none; }}
  .st-key-login-tarjeta {{ margin-top: 2vh; padding: 1.6rem 1.3rem !important; }}
  .md-login-logo-movil {{ display: block; }}
  .md-alerta {{ flex-wrap: wrap; }}
  .md-alerta .pastas {{ flex-direction: row; width: 100%; justify-content: flex-start; padding-left: 2.9rem; }}
  .md-banner-oscuro .val {{ font-size: 1.45rem; }}
}}
</style>
"""


def aplicar_estilos() -> None:
    """Inyecta el CSS global y oculta la marca de Streamlit."""
    st.html(CSS)


# --- Formatos ----------------------------------------------------------------

def num(valor: float | int | None, decimales: int = 0) -> str:
    """Formato boliviano: miles con punto y decimales con coma (1.234,5)."""
    if valor is None:
        return "—"
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")


def bs(valor: float | None, decimales: int = 2) -> str:
    """Monto en bolivianos: ``Bs 1.234,50``."""
    return "—" if valor is None else f"Bs {num(valor, decimales)}"


def fecha(valor: date | None) -> str:
    """Fecha en formato dd/mm/aaaa."""
    return "—" if valor is None else valor.strftime("%d/%m/%Y")


MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre")
DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")


def fecha_larga(valor: date) -> str:
    """Fecha legible: 'viernes 17 de octubre'."""
    return f"{DIAS[valor.weekday()]} {valor.day} de {MESES[valor.month - 1]}"


def saludo() -> str:
    """'Buenos días', 'Buenas tardes' o 'Buenas noches' según la hora local."""
    hora = datetime.now().hour
    return "Buenos días" if 5 <= hora < 12 else ("Buenas tardes" if 12 <= hora < 19 else "Buenas noches")


def _e(texto: object) -> str:
    return html.escape(str(texto))


def ico(nombre: str, clase: str = "") -> str:
    """HTML de un ícono Material Symbols (p. ej. ``ico('home')``)."""
    return f'<span class="ms {clase}">{_e(nombre)}</span>'


def alfa(hex_color: str, opacidad: float) -> str:
    """Color hex con transparencia (``rgba``)."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{opacidad})"


def _html(contenido: str) -> None:
    st.markdown(contenido, unsafe_allow_html=True)


# --- Estructura ----------------------------------------------------------------

def encabezado(titulo: str, subtitulo: str, icono: str) -> None:
    """Banner con degradado rojo: ícono en círculo, título, subtítulo y la fecha actual."""
    hoy = date.today()
    _html(
        f'<div class="md-banner"><div class="circ">{ico(icono)}</div>'
        f'<div class="txt"><h1>{_e(titulo)}</h1><p>{_e(subtitulo)}</p></div>'
        f'<div class="fecha">{_e(fecha_larga(hoy).capitalize())}<b>{fecha(hoy)}</b></div></div>'
    )


def seccion(titulo: str, subtitulo: str | None = None) -> None:
    """Título de sección dentro de una página."""
    sub = f"<p>{_e(subtitulo)}</p>" if subtitulo else ""
    _html(f'<div class="md-seccion"><h3>{_e(titulo)}</h3>{sub}</div>')


@contextmanager
def tarjeta(clave: str, titulo: str | None = None, subtitulo: str | None = None,
            icono: str | None = None) -> Iterator[None]:
    """Contenedor con estilo de tarjeta blanca y título opcional.

    Uso: ``with tarjeta("venta", "Nueva venta", icono="point_of_sale"): ...``
    """
    with st.container(key=f"tarjeta-{clave}"):
        if titulo:
            icono_html = ico(icono) if icono else ""
            _html(f'<div class="md-tit">{icono_html}<h3>{_e(titulo)}</h3></div>')
            if subtitulo:
                _html(f'<div class="md-sub">{_e(subtitulo)}</div>')
        yield


def logo_sidebar() -> None:
    """Logotipo blanco con 'Data' en rojo y la línea 'Plataforma de inventario'."""
    st.logo(str(ASSETS_DIR / "logo.svg"), size="large", icon_image=str(ASSETS_DIR / "icono.svg"))


def iniciales(nombre: str) -> str:
    """Iniciales (máximo 2) de un nombre."""
    partes = [p for p in nombre.split() if p]
    return ("".join(p[0] for p in partes[:2]) or "?").upper()


def avatar(nombre: str, color: str | None = None) -> str:
    """HTML de un avatar circular con iniciales."""
    estilo = f' style="background:{color}"' if color else ""
    return f'<div class="md-avatar"{estilo}>{_e(iniciales(nombre))}</div>'


_COLOR_CLARO = {PRIMARIO: "#FCA5A5", INFO: "#93C5FD", MORADO: "#C4B5FD"}


def tarjeta_usuario(nombre: str, usuario: str, rol: str) -> None:
    """Tarjeta del usuario conectado (avatar de iniciales, @usuario e insignia de rol)."""
    color = COLOR_ROL.get(rol, PRIMARIO)
    _html(
        f'<div class="md-usuario">{avatar(nombre)}<div><div class="nom">{_e(nombre)}</div>'
        f'<div class="arroba">@{_e(usuario)}</div>'
        f'<span class="md-insignia" style="background:{alfa(color, .22)};color:{_COLOR_CLARO.get(color, "#E5E7EB")}">'
        f"{_e(rol)}</span></div></div>"
    )


# --- KPI ---------------------------------------------------------------------

def sparkline(valores: Sequence[float], color: str, ancho: int = 96, alto: int = 30) -> str:
    """Minigráfico SVG de una serie corta (p. ej. últimos 7 días)."""
    vals = [float(v) for v in valores]
    if len(vals) < 2:
        return ""
    vmin, vmax = min(vals), max(vals)
    rango = (vmax - vmin) or 1.0
    paso = ancho / (len(vals) - 1)
    puntos = [(i * paso, alto - 3 - (v - vmin) / rango * (alto - 6)) for i, v in enumerate(vals)]
    linea = " ".join(f"{x:.1f},{y:.1f}" for x, y in puntos)
    area = f"0,{alto} {linea} {ancho},{alto}"
    ux, uy = puntos[-1]
    return (
        f'<svg class="md-spark" width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}">'
        f'<polygon points="{area}" fill="{alfa(color, .12)}"/>'
        f'<polyline points="{linea}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round"/><circle cx="{ux:.1f}" cy="{uy:.1f}" r="2.8" fill="{color}"/></svg>'
    )


def tarjeta_kpi(
    etiqueta: str, valor: str, variacion: str | None = None, icono: str = "insights",
    color: str = "azul", tendencia: str | None = None, alerta: bool = False,
    serie: Sequence[float] | None = None, mini: bool = False,
) -> None:
    """Tarjeta KPI: chip de ícono de color, etiqueta, número grande y variación en pastilla.

    ``tendencia``: ``"sube"`` (verde ▲), ``"baja"`` (rojo ▼) o ``None`` (neutra).
    ``alerta``: borde izquierdo rojo y punto que pulsa.
    ``serie``: valores para un minigráfico de los últimos días.
    """
    hex_color = COLORES.get(color, color)
    flecha = {"sube": "▲ ", "baja": "▼ "}.get(tendencia or "", "")
    var_html = (f'<span class="md-var {tendencia or "neutra"}">{flecha}{_e(variacion)}</span>'
                if variacion else "<span></span>")
    pulso = '<span class="md-pulso"></span>' if alerta else ""
    spark = sparkline(serie, hex_color) if serie else ""
    clases = "md-kpi" + (" alerta" if alerta else "") + (" mini" if mini else "")
    chip_ico = (f'<div class="md-chip-ico" style="background:{alfa(hex_color, .12)};color:{hex_color}">'
                f"{ico(icono)}</div>")
    _html(
        f'<div class="{clases}"><div class="cab">{chip_ico}{pulso}</div>'
        f'<div class="lbl">{_e(etiqueta)}</div><div class="val">{_e(valor)}</div>'
        f'<div class="pie">{var_html}{spark}</div></div>'
    )


def banner_kpis(items: Sequence[tuple[str, str, str, str]]) -> None:
    """Banner oscuro con KPI en blanco. ``items``: (etiqueta, valor, subtítulo, color)."""
    celdas = "".join(
        f'<div class="it" style="--c:{COLORES.get(c, c)}"><div class="lbl">{_e(e)}</div>'
        f'<div class="val">{_e(v)}</div><div class="sub">{_e(s)}</div></div>'
        for e, v, s, c in items
    )
    _html(f'<div class="md-banner-oscuro">{celdas}</div>')


# --- Alertas, avisos y estados -------------------------------------------------

_TIPOS = {
    # tipo: (color, fondo, color de texto, ícono)
    "Faltante": (ERROR, ERROR_FONDO, "#7F1D1D", "warning"),
    "Sobrante": (ADVERTENCIA, ADVERTENCIA_FONDO, "#78350F", "error"),
    "Correcto": (EXITO, EXITO_FONDO, "#14532D", "check_circle"),
    "error": (ERROR, ERROR_FONDO, "#7F1D1D", "error"),
    "warning": (ADVERTENCIA, ADVERTENCIA_FONDO, "#78350F", "warning"),
    "success": (EXITO, EXITO_FONDO, "#14532D", "check_circle"),
    "info": (INFO, INFO_FONDO, "#1E3A8A", "info"),
}


def alerta(mensaje: str, tipo: str, diferencia: int | None = None, tienda: str | None = None,
           detalle: str | None = None) -> None:
    """Alerta de inventario: ícono, borde de color, mensaje en negrita y pastillas a la derecha."""
    color, fondo, _, icono = _TIPOS.get(tipo, _TIPOS["info"])
    pastas = ""
    if diferencia is not None:
        signo = "−" if diferencia < 0 else ("+" if diferencia > 0 else "")
        n = abs(diferencia)
        pastas += (f'<span class="md-pastilla" style="background:{color};color:#fff">'
                   f'{signo}{n} {"par" if n == 1 else "pares"}</span>')
    if tienda:
        pastas += (f'<span class="md-pastilla" style="background:#fff;color:{TEXTO_2}">'
                   f'{ico("storefront")} {_e(tienda)}</span>')
    det = f'<div class="det">{_e(detalle)}</div>' if detalle else ""
    _html(
        f'<div class="md-alerta" style="--c:{color};--f:{fondo}"><div class="ico">{ico(icono)}</div>'
        f'<div class="cuerpo"><div class="msg">{_e(mensaje)}</div>{det}</div>'
        f'<div class="pastas">{pastas}</div></div>'
    )


def aviso(mensaje: str, tipo: str = "info") -> None:
    """Aviso compacto (éxito, error, advertencia o información) en lugar de las cajas de Streamlit."""
    color, fondo, texto, icono = _TIPOS.get(tipo, _TIPOS["info"])
    _html(f'<div class="md-aviso" style="--c:{color};--f:{fondo};--t:{texto};--b:{alfa(color, .25)}">'
          f"{ico(icono)}<div>{_e(mensaje)}</div></div>")


def estado_vacio(mensaje: str, icono: str = "inbox", accion: tuple[str, str, str] | None = None,
                 clave: str = "vacio") -> None:
    """Estado vacío: ícono grande gris, mensaje centrado y botón opcional.

    ``accion``: (texto del botón, archivo de la página, ícono Material), p. ej.
    ``("Ir a Apertura", "pages/1_Apertura.py", "inventory_2")``.
    """
    _html(f'<div class="md-vacio">{ico(icono)}<p>{_e(mensaje)}</p></div>')
    if accion:
        texto, pagina, icono_btn = accion
        with st.container(key=f"vacio-accion-{clave}"):
            try:
                st.page_link(pagina, label=texto, icon=f":material/{icono_btn}:")
            except StreamlitAPIException:
                pass  # la página no está disponible para el rol del usuario: se omite el botón


def pastilla_estado(estado: str) -> str:
    """HTML de una pastilla de color para Correcto, Faltante o Sobrante."""
    color = COLOR_ESTADO.get(estado, TEXTO_2)
    icono = {"Correcto": "check_circle", "Faltante": "arrow_downward", "Sobrante": "arrow_upward"}.get(estado, "circle")
    return (f'<span class="md-pastilla" style="background:{alfa(color, .14)};color:{color}">'
            f"{ico(icono)} {_e(estado)}</span>")


def estilo_estado(estado: str) -> str:
    """Estilo de celda tipo pastilla para colorear la columna Estado en ``st.dataframe``."""
    return {
        "Faltante": f"background-color: {ERROR_FONDO}; color: #B91C1C; font-weight: 700",
        "Sobrante": f"background-color: {ADVERTENCIA_FONDO}; color: #B45309; font-weight: 700",
        "Correcto": f"background-color: {EXITO_FONDO}; color: #15803D; font-weight: 700",
    }.get(estado, "")


def chip(texto: str, color: str) -> str:
    """HTML de un chip de color (categorías, roles)."""
    hex_color = COLORES.get(color, color)
    return (f'<span class="md-pastilla" style="background:{alfa(hex_color, .12)};color:{hex_color}">'
            f"{_e(texto)}</span>")


def sugerencia(texto_html: str) -> None:
    """Tarjeta de sugerencia con ícono de bombilla (admite HTML simple)."""
    _html(f'<div class="md-sugerencia">{ico("lightbulb")}<div>{texto_html}</div></div>')


def nota(titulo: str, texto_html: str, icono: str = "info") -> None:
    """Cuadro de nota con borde de acento y título con ícono (admite HTML simple)."""
    _html(f'<div class="md-nota"><div class="tt">{ico(icono)}{_e(titulo)}</div>{texto_html}</div>')


# --- Componentes de páginas específicas ----------------------------------------

def pasos(actual: int, etiquetas: Sequence[str] = ("Seleccionar", "Contar", "Resultado")) -> None:
    """Indicador de asistente: pasos hechos (verde), activo (rojo) y pendientes (gris)."""
    partes = []
    for i, texto in enumerate(etiquetas, start=1):
        estado = "hecho" if i < actual else ("activo" if i == actual else "")
        numero = ico("check") if i < actual else str(i)
        if i > 1:
            partes.append(f'<div class="md-linea {"hecha" if i <= actual else ""}"></div>')
        partes.append(f'<div class="md-paso {estado}"><span class="n">{numero}</span>'
                      f'<span class="t">{_e(texto)}</span></div>')
    _html(f'<div class="md-pasos">{"".join(partes)}</div>')


def tarjeta_resultado(estado: str, mensaje: str, esperado: int, contado: int, diferencia: int) -> None:
    """Gran tarjeta con el resultado del cierre y tres bloques: esperado, contado y diferencia."""
    color, fondo, texto, _ = _TIPOS.get(estado, _TIPOS["info"])
    n = abs(diferencia)
    pares = "par" if n == 1 else "pares"
    titulo = {
        "Correcto": "Cierre correcto",
        "Faltante": f"{'Falta' if n == 1 else 'Faltan'} {n} {pares}",
        "Sobrante": f"{'Sobra' if n == 1 else 'Sobran'} {n} {pares}",
    }.get(estado, estado)
    icono = {"Correcto": "check", "Faltante": "priority_high", "Sobrante": "add"}.get(estado, "info")
    dif_txt = f"{diferencia:+d}".replace("-", "−") if diferencia else "0"
    _html(
        f'<div class="md-resultado" style="--c:{color};--f:{fondo};--t:{texto}">'
        f'<div class="top"><div class="grande">{ico(icono)}</div><div><h2>{_e(titulo)}</h2>'
        f'<div class="msg">{_e(mensaje)}</div></div></div>'
        f'<div class="md-bloques">'
        f'<div class="md-bloque"><div class="lbl">Esperado</div><div class="val">{esperado}</div></div>'
        f'<div class="md-bloque"><div class="lbl">Contado</div><div class="val">{contado}</div></div>'
        f'<div class="md-bloque"><div class="lbl">Diferencia</div>'
        f'<div class="val" style="color:{color}">{dif_txt}</div></div></div></div>'
    )


def conteo_grande(cantidad: int, unidad: str, confianza: float, detectados: int) -> None:
    """Número contado por la IA en grande con su confianza en una barra."""
    pct = max(0.0, min(confianza, 1.0)) * 100
    color = EXITO if pct >= 60 else (ADVERTENCIA if pct >= 35 else ERROR)
    _html(
        f'<div class="md-conteo"><div class="md-etq">Conteo IA</div><div class="num">{cantidad}</div>'
        f'<div class="uni">{_e(unidad)} · {detectados} objetos detectados</div></div>'
        f'<div class="md-etq">Confianza promedio · {num(pct, 0)} %</div>'
        f'<div class="md-barra" style="--c:{color}"><div style="width:{pct:.0f}%"></div></div>'
    )


def lista_stock(filas: Sequence[tuple[str, str, int, int]]) -> None:
    """Stock por producto con barra de color. ``filas``: (código, nombre, disponible, saldo inicial).

    Verde si queda más del 50 %, amarillo entre 20 y 50 % y rojo por debajo del 20 %.
    """
    items = []
    for codigo, nombre, disponible, inicial in filas:
        pct = 100 * disponible / inicial if inicial else 0
        color = EXITO if pct > 50 else (ADVERTENCIA if pct >= 20 else ERROR)
        items.append(
            f'<div class="fila"><div><div class="cod">{_e(codigo)}</div><div class="nom">{_e(nombre)}</div></div>'
            f'<div class="md-barra" style="--c:{color}"><div style="width:{pct:.0f}%"></div></div>'
            f'<div class="cant">{disponible}<small>/{inicial}</small></div></div>'
        )
    _html(f'<div class="md-stock">{"".join(items)}</div>')


def linea_tiempo(hitos: Sequence[tuple[str, str, str]]) -> None:
    """Línea de tiempo vertical. ``hitos``: (título, detalle, tipo: ok | alerta | error | info)."""
    partes = []
    for titulo, detalle, tipo in hitos:
        color = {"ok": EXITO, "alerta": ADVERTENCIA, "error": ERROR, "info": INFO}.get(tipo, EXITO)
        icono = {"ok": "check", "alerta": "filter_alt", "error": "close", "info": "flag"}.get(tipo, "check")
        partes.append(f'<div class="md-hito" style="--c:{color}"><div class="pt">{ico(icono)}</div>'
                      f"<b>{_e(titulo)}</b><p>{_e(detalle)}</p></div>")
    _html(f'<div class="md-tiempo">{"".join(partes)}</div>')


def flujo_filas(originales: int, validas: int, descartadas: int) -> None:
    """Resumen visual: filas originales → válidas / descartadas."""
    _html(
        f'<div class="md-flujo"><div class="caja"><div class="val">{num(originales)}</div>'
        f'<div class="lbl">Filas originales</div></div>{ico("arrow_forward")}'
        f'<div class="caja" style="--c:{EXITO}"><div class="val">{num(validas)}</div><div class="lbl">Válidas</div></div>'
        f'<div class="caja" style="--c:{ERROR}"><div class="val">{num(descartadas)}</div>'
        f'<div class="lbl">Descartadas</div></div></div>'
    )


def ranking(filas: Sequence[tuple[str, str, str]]) -> None:
    """Ranking simple. ``filas``: (nombre, detalle, valor en pastilla)."""
    if not filas:
        estado_vacio("Sin diferencias en el período.", "verified")
        return
    partes = [
        f'<div class="fila"><div class="pos {"p1" if i == 1 else ""}">{i}</div>'
        f'<div class="nom">{_e(n)}<small>{_e(d)}</small></div>'
        f'<span class="md-pastilla" style="background:{ERROR_FONDO};color:#B91C1C">{_e(v)}</span></div>'
        for i, (n, d, v) in enumerate(filas, start=1)
    ]
    _html(f'<div class="md-ranking">{"".join(partes)}</div>')


def grilla(fichas_html: Sequence[str]) -> None:
    """Cuadrícula de fichas (productos, usuarios)."""
    _html(f'<div class="md-grilla">{"".join(fichas_html)}</div>')


def ficha_producto(codigo: str, nombre: str, categoria: str, talla: str, color: str,
                   precio: float, activo: bool) -> str:
    """HTML de la ficha de un producto con chip de categoría de color."""
    estado = "" if activo else " inactiva"
    return (
        f'<div class="md-ficha{estado}"><div class="cab"><span class="cod">{_e(codigo)}</span>'
        f'{chip(categoria, COLOR_CATEGORIA.get(categoria, TEXTO_2))}</div>'
        f'<div class="nom">{_e(nombre)}</div><div class="det">Talla {_e(talla)} · {_e(color)}'
        f'{"" if activo else " · dado de baja"}</div><div class="precio">{bs(precio)}</div></div>'
    )


def ficha_usuario(nombre: str, usuario: str, rol: str, activo: bool) -> str:
    """HTML de la ficha de un usuario con avatar y chip de rol."""
    color = COLOR_ROL.get(rol, TEXTO_2)
    estado = "" if activo else " inactiva"
    return (
        f'<div class="md-ficha{estado}"><div class="persona">{avatar(nombre, color)}<div>'
        f'<div class="nom" style="font-weight:700">{_e(nombre)}</div><div class="det">@{_e(usuario)}'
        f'{"" if activo else " · inactivo"}</div></div></div><div>{chip(rol, color)}</div></div>'
    )
