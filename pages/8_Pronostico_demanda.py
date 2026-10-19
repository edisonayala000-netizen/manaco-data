"""Pronóstico de demanda por línea de producto, con ajuste por mercado informal."""

from __future__ import annotations

import streamlit as st

from src.auth import proteger_pagina
from src.services import pronostico as pr
from src.ui import graficos
from src.ui.estilos import ICONOS, banner_kpis, encabezado, nota, num, tarjeta

proteger_pagina("pronostico")
encabezado("Pronóstico de demanda", "Proyección mensual por línea, con y sin el efecto del mercado informal.",
           ICONOS["pronostico"])

SIN_BARRA = {"displayModeBar": False}

with tarjeta("filtros", "Filtros", None, "tune"):
    f1, f2, f3 = st.columns([1.3, 1, 1])
    linea = f1.segmented_control("Línea", pr.LINEAS, default=pr.LINEAS[0], key="pron_linea") or pr.LINEAS[0]
    meses_hist = f2.selectbox("Meses de historial", [12, 24, 36], index=1, key="pron_hist")
    meses_adelante = f3.selectbox("Meses a proyectar", [3, 6, 12], index=1, key="pron_fut")

historial = pr.generar_historial(linea, meses=meses_hist)
futuro = pr.pronosticar(historial, linea, meses_adelante=meses_adelante)
resultado = pr.backtest(historial, linea)
sensibilidad = pr.SENSIBILIDAD_INFORMAL[linea]

st.write("")
banner_kpis([
    ("Pronóstico sin ajuste (próx. mes)", num(futuro["Pronostico_base"].iloc[0]), "pares/mes", "gris"),
    ("Pronóstico ajustado (próx. mes)", num(futuro["Pronostico_ajustado"].iloc[0]), "pares/mes", "rojo"),
    ("Sensibilidad al mercado informal", f"{num(sensibilidad * 100, 0)}%", f"línea {linea}", "morado"),
    ("Error del ajuste (MAPE)", f"{num(resultado.mape_ajustado, 1)}%",
     f"vs. {num(resultado.mape_base, 1)}% sin ajustar", "verde"),
])

st.write("")
with tarjeta("g-pronostico"):
    st.plotly_chart(graficos.grafico_pronostico(historial, futuro, linea), width="stretch", theme=None,
                     config=SIN_BARRA)

st.write("")
tabla = futuro.rename(columns={
    "Fecha": "Mes", "Pronostico_base": "Sin ajustar (pares)", "Pronostico_ajustado": "Ajustado (pares)",
    "Presion_informal_proyectada": "Presión informal proyectada",
})
with tarjeta("tabla-pronostico", "Detalle del pronóstico", f"Próximos {meses_adelante} meses · línea {linea}"):
    st.dataframe(
        tabla, hide_index=True, width="stretch",
        column_config={
            "Mes": st.column_config.DateColumn(format="MMM YYYY"),
            "Sin ajustar (pares)": st.column_config.NumberColumn(format="%d"),
            "Ajustado (pares)": st.column_config.NumberColumn(format="%d"),
            "Presión informal proyectada": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f"),
        },
    )

nota(
    "De dónde salen estos datos",
    "<ul>"
    "<li><b>[Simulado]</b> El historial mensual no proviene de ventas reales: solo hay 90 días de ventas "
    "registradas en el sistema, insuficientes para estimar estacionalidad o tendencia. Se generó un historial "
    f"de {meses_hist} meses con un nivel base por línea, estacionalidad (inicio de clases y fin de año) y una "
    "presión del mercado informal creciente, igual que el escenario descrito en el caso.</li>"
    f"<li><b>[Supuesto]</b> La sensibilidad de cada línea al mercado informal ({num(sensibilidad * 100, 0)}% "
    "para esta línea) es una estimación del equipo, no un dato medido.</li>"
    "<li>El <b>pronóstico sin ajustar</b> usa un promedio móvil estacional sobre las ventas observadas; el "
    "<b>ajustado</b> reconstruye la demanda implícita (ventas ÷ efecto informal) y le vuelve a aplicar la "
    "presión informal proyectada. Como el historial simulado ya incluye el efecto informal, el backtest "
    "demuestra el método, pero no mide la magnitud real del contrabando: eso se valida con ventas reales.</li></ul>",
    icono="science",
)
