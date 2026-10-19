"""Entregables escritos del caso: problemas priorizados, síntesis, ficha y recomendación."""

from __future__ import annotations

import streamlit as st

from src.auth import proteger_pagina
from src.ui.estilos import ICONOS, encabezado, nota, seccion, tarjeta

proteger_pagina("entregables")
encabezado(
    "Entregables escritos",
    "Los 4 textos que exige la rúbrica del caso, con las cifras que ya calcula el sistema.",
    ICONOS["entregables"],
)

tab1, tab2, tab3, tab4 = st.tabs([
    ":material/priority_high: 1. Problemas prioritarios",
    ":material/summarize: 2. Síntesis ejecutiva",
    ":material/description: 3. Ficha de una página",
    ":material/fact_check: 4. Recomendación ejecutiva",
])

with tab1:
    seccion("Problemas prioritarios", "5 problemas que cubren las 6 áreas del caso, ordenados por impacto")
    with tarjeta("problemas"):
        st.markdown(
            "| N.º | Problema y área | Justificación | Datos necesarios |\n"
            "| --- | --- | --- | --- |\n"
            "| 1 | **Inventario sin control diario en tienda** · *Producción, inventarios y logística* | Sin "
            "conteo diario, una diferencia de stock solo se nota en el cierre contable mensual, cuando ya no se "
            "puede rastrear su causa. Ejemplo de la demo: *\"Faltan 2 pares de MAN-DEP-001 en Tienda Prado "
            "(esperado 38, contado 36)\"*. | Saldo inicial, ventas del día y conteo de cierre por tienda y "
            "producto; histórico de diferencias (Historial, `cierres`). |\n"
            "| 2 | **Presión de la oferta importada y del mercado informal** · *Competitividad y mercado* | "
            "**Dato:** Deportivo importa 2,97 veces lo que exporta (Excel, 240 filas válidas). **Hipótesis a "
            "validar:** el calzado informal entra sin pagar aranceles ni impuestos, compite por precio y le quita ventas a Manaco. | Ventas "
            "reales por línea y mes, precios de la competencia formal e informal, tipo de cambio paralelo "
            "(Pronóstico de demanda, `ref_mercado_local`). |\n"
            "| 3 | **Rentabilidad por línea sin medir** · *Rentabilidad y estructura de costos* | En el mercado "
            "de referencia el Cuero vale casi el doble por par (~41–45 USD frente a ~25), pero Manaco no sabe qué "
            "línea le deja más utilidad: no integra costos de producción, defectos, devoluciones, almacenamiento "
            "ni distribución. | Costo real por lote, costo de defectos y devoluciones, gastos de almacenamiento y "
            "distribución, precio real con descuentos (`fact_produccion`, `fact_calidad`). |\n"
            "| 4 | **Cliente desconocido** · *Clientes, segmentación y marketing* | El sistema registra qué se "
            "vende, dónde y cuándo, pero no quién compra. Sin eso no se puede segmentar ni medir el canal "
            "digital que menciona el caso. | Tipo de cliente (edad, ciudad, segmento), frecuencia y monto de "
            "compra, canal (tienda o digital), motivos de devolución. |\n"
            "| 5 | **Datos dispersos y sin responsables claros** · *Gestión organizacional y calidad de datos* | "
            "Mercado, ventas, inventario y calidad están separados, y los archivos de las sucursales llegan con "
            "errores. Si nadie responde por corregirlos, cualquier reporte de gerencia queda distorsionado. | "
            "Bitácora de ingesta por sucursal (filas leídas, corregidas y rechazadas), reglas de validación y "
            "un responsable por fuente de datos (`log_ingesta`, `bitacora_limpieza`). |"
        )
    nota(
        "Por qué este orden y qué responde cada fuente",
        "El 1 afecta a diario y ya tiene solución en marcha; el 2 y el 3 definen en qué línea competir; el 4 y "
        "el 5 son la condición para que las decisiones siguientes tengan datos confiables. El Excel de comercio "
        "exterior responde comparaciones de categorías, socios y valor por par en un mercado de referencia; "
        "<b>no</b> responde costos, márgenes, clientes ni ventas de Manaco: eso exige datos internos.",
        icono="sort",
    )

with tab2:
    seccion("Diagnóstico de datos", "Síntesis ejecutiva: 3 hallazgos, 2 limitaciones y 1 pregunta estratégica")
    st.caption(":material/table_view: La tabla depurada y el diccionario de datos están en Tablero de mercado → "
               "Limpieza de datos, con descarga en Excel.")
    with tarjeta("hallazgos", "3 hallazgos (base de comercio exterior, 240 filas válidas)", icono="lightbulb"):
        st.markdown(
            "1. **Deportivo es la categoría más dependiente de la importación.** Importa **2,97 veces** lo que "
            "exporta en valor y **2,91 veces** en pares. Como la proporción casi no cambia con la métrica, la "
            "conclusión es sólida: en esta línea la oferta importada domina el mercado de referencia.\n"
            "2. **El calzado de cuero es un nicho de mayor valor por par.** Su valor aduanero ronda los "
            "**41–45 USD por par**, frente a unos **25 USD** de Deportivo y de Caucho y cuero. En volumen es "
            "pequeño (7,7 millones de pares importados frente a 498 millones de Caucho y cuero), pero cada par "
            "vale casi el doble: es la señal más clara de dónde diferenciarse por calidad y no por precio.\n"
            "3. **Medir por valor o por cantidad cambia quiénes son los proveedores relevantes.** Por categoría, "
            "el orden es el mismo con ambas métricas. Por socio, en cambio, **República Checa entra al top 6 de "
            "proveedores por pares, pero no por valor**, porque su calzado es el más barato de la base (unos "
            "9 USD por par). Si solo se mira el valor, se pierden de vista los proveedores que compiten por precio."
        )
    with tarjeta("limitaciones", "2 limitaciones", icono="warning"):
        st.markdown(
            "1. **La referencia es española y el valor es aduanero.** Sirve para comparar categorías y "
            "proporciones, pero no representa el mercado boliviano ni el precio al consumidor, que incluye "
            "aranceles, transporte y margen del comerciante.\n"
            "2. **La cobertura por año es desigual.** Hay 28 registros en 2020 y 82 en 2024, así que "
            "cualquier \"crecimiento\" entre años refleja la cantidad de registros, no el mercado. Por eso no se "
            "sacan tendencias temporales."
        )
    nota(
        "1 pregunta estratégica",
        "Si Deportivo es la línea con más presión importada y Cuero la de mayor valor por par, ¿debe Manaco "
        "defender volumen en Deportivo o concentrar su diferenciación en Cuero? ¿Qué margen real por línea "
        "necesitaría ver para decidirlo?",
        icono="help",
    )
    with tarjeta("preguntas", "Respuestas a las 5 preguntas del caso", icono="quiz"):
        st.markdown(
            "| Pregunta del caso | Respuesta con los datos |\n"
            "| --- | --- |\n"
            "| ¿Qué datos internos debería recopilar Manaco? | Ventas por producto, tienda y día (ya las registra el sistema); costos reales por lote; defectos y devoluciones con su motivo; datos del cliente (segmento, ciudad y canal); fechas de entrega; inventario por almacén; y precios reales con descuentos. |\n"
            "| ¿Qué hipótesis sobre competencia, abastecimiento o diferenciación podría investigar? | Competencia: Deportivo depende de la importación (importa 2,97 veces lo que exporta), así que es la línea más expuesta al calzado importado barato. Abastecimiento: hay proveedores muy baratos por par (República Checa, unos 9 USD) que sirven de referencia de costo. Diferenciación: el Cuero vale casi el doble por par, lo que sugiere un nicho de calidad. |\n"
            "| ¿Cómo varía el valor por par y por qué no es el precio al consumidor? | Va de 8 a 119 USD por registro; la mediana es de unos 47 USD en Cuero y unos 27 USD en Deportivo y en Caucho y cuero. Es un valor aduanero: no incluye aranceles, impuestos, transporte ni el margen del comerciante, así que el precio en tienda es mayor. |\n"
            "| ¿Qué países son proveedores y destinos relevantes? | Proveedores, por valor: Grecia, Países Bajos, Vietnam, Irlanda, Turquía y Rumanía. Destinos, por valor: Indonesia, Vietnam, Eslovenia, Irlanda, Grecia y Austria. Son relevantes dentro de los 30 socios del archivo, no del comercio mundial. |\n"
            "| ¿Qué categorías tienen mayor valor? ¿Cambia al comparar con la cantidad? | Caucho y cuero lidera en ambos flujos (11.709,7 M USD importados y 8.514,2 M USD exportados), seguida de Deportivo; Cuero es muy pequeña. Por categoría el orden no cambia con la cantidad de pares; por socio sí: República Checa entra al top 6 de proveedores por pares, pero no por valor. |"
        )

with tab3:
    seccion("Propuesta estratégica", "Ficha de una página")
    with tarjeta("ficha"):
        st.markdown(
            "**Problema:** Manaco no controla a diario su inventario en tienda ni mide la rentabilidad real de "
            "cada línea, y no cruza esos datos con el mercado. Así no puede decidir en qué línea competir frente "
            "a la oferta importada e informal.\n\n"
            "**Solución analítica — Manaco Data:** (1) control diario de apertura, venta y cierre con alerta "
            "automática de faltante o sobrante, apoyado en conteo por foto con IA; (2) tablero de mercado que "
            "cruza comercio exterior con ventas internas por código SA6; (3) pronóstico de demanda y prototipo "
            "de escenario, que hoy demuestran el método con datos **[Simulado]** y se recalibran con ventas "
            "reales. **Decisión que apoya:** qué línea priorizar y cuánto producir.\n\n"
            "**Datos que necesita:** aperturas, ventas y cierres diarios (ya los registra); comercio exterior "
            "(ya cargado y limpio); costos por lote, defectos y devoluciones (hoy simulados, por reemplazar).\n\n"
            "**3 objetivos SMART a 3 años** (la línea base se mide en el primer mes de uso):\n"
            "- **Inventario:** bajar los cierres con diferencia a menos del 10% al cierre del año 1, del 5% al "
            "año 2 y del 3% al año 3, en todas las tiendas. *KPI:* % de cierres `Correcto` por tienda "
            "(Historial, Inicio).\n"
            "- **Datos reales:** 100% de las tiendas con registro diario completo desde el mes 3; al año 2, 24 "
            "meses de historia real que reemplacen los datos [Simulado]; al año 3, pronóstico por línea con error "
            "(MAPE) menor al 15% sobre ventas reales. *KPI:* % de tiendas con registro completo, meses de "
            "historia real y MAPE.\n"
            "- **Calidad:** bajar la tasa de defectos a 3% o menos en todos los lotes al año 1, 2,5% al año 2 y "
            "2% al año 3, y reducir a la mitad las devoluciones por costura y pegado de suela. *KPI:* tasa de "
            "defectos y devoluciones por lote (`fact_calidad`).\n\n"
            "**Responsables y coordinación:** Gerencia General patrocina y revisa los 3 KPI en un comité "
            "mensual; Gerencia Comercial fija metas de venta y atiende alertas; Gerencia de Producción responde "
            "por defectos y cobertura; los encargados de tienda registran a diario; Administración/TI mantiene el "
            "sistema, el catálogo, la carga de datos y la migración a PostgreSQL.\n\n"
            "**2 riesgos de implementación y su mitigación:**\n"
            "1. *Registro diario incompleto:* el cierre de inventario pasa a ser parte del cierre de caja, Inicio "
            "muestra los cierres pendientes y gerencia recibe un reporte semanal por tienda.\n"
            "2. *Decidir con datos simulados:* todo dato simulado lleva la etiqueta [Simulado], no se compromete "
            "presupuesto hasta tener 12 meses reales, y las metas se recalibran con la línea base real.\n\n"
            "**Viabilidad:** el sistema ya funciona en una computadora local. El costo principal es el tiempo del "
            "personal para registrar a diario y, en el año 2, la migración a un servidor con PostgreSQL."
        )

with tab4:
    seccion("Decisión financiera / mercado", "Recomendación ejecutiva")
    with tarjeta("lectura", "Lectura de los indicadores", icono="insights"):
        st.markdown(
            "- **Producción [Simulado]:** lotes mensuales calibrados con la demanda base de cada línea (±15%).\n"
            "- **Defectos [Simulado]:** entre 1% y 5% por lote. El promedio queda cerca de la meta de 3%, así que "
            "cerca de la mitad de los lotes la supera. Motivos: costura, pegado de suela, talla y manchas.\n"
            "- **Devoluciones [Simulado]:** entre el 20% y el 50% de los pares defectuosos llegan al cliente y "
            "vuelven. Son los defectos que más dañan la marca.\n"
            "- **Entregas: no hay datos.** El sistema no registra fechas de despacho ni de entrega, así que no se "
            "puede medir cumplimiento ni quiebres de stock por demora.\n"
            "- **Ventas [Simulado]:** 90 días de demo en 3 tiendas. Alcanzan para el control diario, no para ver "
            "tendencias de largo plazo.\n"
            "- **Margen de catálogo [Supuesto, precios de la demo]:** cerca del 45% en las tres líneas, pero por "
            "par el Cuero deja unos 239 Bs, frente a unos 155 Bs de Deportivo y de Caucho y cuero."
        )
    with tarjeta("faltantes", "Qué falta para estimar costos y rentabilidad", icono="help"):
        st.markdown(
            "Costos reales por lote (insumos, mano de obra, energía) · costos fijos de planta y tiendas · costo "
            "de cada devolución (flete, reproceso, reposición) · gastos de almacenamiento y distribución por "
            "ciudad · precio real de venta con descuentos · fechas de entrega prometidas frente a reales."
        )
    with tarjeta("alternativas", "2 alternativas comparadas", icono="balance"):
        st.markdown(
            "| | Alternativa A — Competir por precio | Alternativa B — Diferenciar por calidad en Cuero |\n"
            "| --- | --- | --- |\n"
            "| Acción | Bajar el precio para cerrar la brecha frente al mercado informal. | Mantener el precio; "
            "control de calidad por lote y garantía en la línea Cuero. |\n"
            "| Beneficio esperado | Recuperar volumen frente al calzado informal. | Menos devoluciones y "
            "reprocesos; marca más fuerte en la línea de mayor valor por par. |\n"
            "| Costo | Con un margen cercano al 45%, bajar el precio 10% obliga a vender **~29% más pares** solo "
            "para mantener la utilidad bruta. | Inspección por lote, capacitación en costura y pegado, y stock "
            "de tallas centrales. Se cuantifica con costos reales. |\n"
            "| Indicador | Brecha frente al mercado informal (meta ≤20%). | Tasa de defectos (≤3%) y "
            "devoluciones de Cuero. |\n"
            "| Control | Bajo: la brecha depende del tipo de cambio paralelo. | Alto: son procesos internos. |\n"
            "| Riesgo principal | Guerra de precios contra un competidor sin costos formales. | Que la garantía "
            "no se perciba si no se comunica. |"
        )
    nota(
        "Recomendación: Alternativa B",
        "Cerrar la brecha de precio es una carrera que Manaco no controla: depende del tipo de cambio paralelo y "
        "el competidor informal no paga impuestos ni planilla. Además, la aritmética es exigente: un 10% menos "
        "de precio exige casi un 30% más de volumen solo para quedar igual. La calidad, en cambio, es una "
        "palanca interna, y el Cuero es la línea donde el mercado paga más por par.",
        icono="check_circle",
    )
    with tarjeta("segmento", "Segmento y acción comercial", icono="groups"):
        st.markdown(
            "**Segmento [Supuesto]:** adultos que trabajan en oficinas o servicios y compran calzado de cuero de "
            "vestir en las tiendas de La Paz, Cochabamba y Santa Cruz.\n\n"
            "**Por qué:** el Cuero tiene el mayor valor por par del mercado de referencia (~41–45 USD), la menor "
            "presión importada (importa 1,52 veces lo que exporta, frente a 2,97 veces de Deportivo) y el mayor "
            "margen por par del catálogo. Falta validarlo con datos de clientes.\n\n"
            "**Acción:** lanzar *Cuero garantizado*: garantía de 6 meses en costura y suela, control de calidad "
            "de cada lote antes de enviarlo a tienda y stock asegurado de tallas centrales en las 3 tiendas, "
            "comunicado en tienda y en canales digitales."
        )
    with tarjeta("indicadores", "3 indicadores de seguimiento", icono="monitoring"):
        st.markdown(
            "1. **Tasa de defectos y devoluciones de la línea Cuero** (meta ≤3% de defectos) — `fact_calidad`.\n"
            "2. **Ventas de la línea Cuero** en pares y Bs frente a los 3 meses previos — Ventas / Tablero.\n"
            "3. **% de cierres de inventario correctos por tienda** — Historial / Inicio."
        )

nota(
    "De dónde salen estos textos",
    "Las cifras de comercio exterior son reales y ya están limpias en el sistema. Las de ventas e inventario "
    "vienen de la demo, y las de producción, calidad, mercado local y precios de catálogo están "
    "etiquetadas <b>[Simulado]</b> o <b>[Supuesto]</b>: reemplácelas por historia real de Manaco "
    "antes de comprometer presupuesto con estos objetivos. Versión completa en "
    "<code>docs/ENTREGABLES_ESCRITOS.md</code>.",
    icono="science",
)
