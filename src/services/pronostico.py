"""Pronóstico de demanda por línea de producto, con ajuste por mercado informal.

Metodología (Manaco_Caso_Solucion_y_Prototipo.md, sección 3.7): promedio móvil con
estacionalidad mensual, y un factor de ajuste por presión del mercado informal:
``demanda ajustada = demanda implícita × (1 − sensibilidad de la línea × presión informal)``.

Este módulo no depende de Streamlit ni de la base de datos. No hay suficiente historial
real de ventas (``Venta`` solo cubre los últimos 90 días), así que ``generar_historial``
simula 24 meses de demanda mensual por línea — igual que el prototipo publicado en la
sección 4 del documento. Todo lo que produce esa función está etiquetado [Simulado]; la
sensibilidad de cada línea al mercado informal está etiquetada [Supuesto].
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date

import pandas as pd

from src.config import CATEGORIAS_SA6

LINEAS: tuple[str, ...] = tuple(CATEGORIAS_SA6)

#: Sensibilidad de cada línea a la presión del mercado informal (0 = inmune). [Supuesto]
SENSIBILIDAD_INFORMAL: dict[str, float] = {
    "Deportivo": 0.35,
    "Caucho y cuero": 0.20,
    "Cuero": 0.10,
    "Medias": 0.30,
}

#: Nivel base de demanda mensual (pares) por línea. [Supuesto]
_NIVEL_BASE: dict[str, float] = {"Deportivo": 1800, "Caucho y cuero": 1200, "Cuero": 700, "Medias": 2500}
#: Alias público: ``seed_solucion.py`` calibra la producción simulada con este nivel.
NIVEL_BASE = _NIVEL_BASE
#: Meses de pico estacional: inicio de clases (feb-mar) y fiestas de fin de año.
_MESES_PICO: tuple[int, ...] = (2, 3, 12)
_SEMILLA = 2026


@dataclass(frozen=True)
class ResultadoBacktest:
    """Error porcentual promedio (MAPE) del pronóstico, con y sin ajuste informal."""

    mape_base: float
    mape_ajustado: float


def _restar_meses(fecha: date, n: int) -> date:
    total = fecha.year * 12 + (fecha.month - 1) - n
    return date(total // 12, total % 12 + 1, 1)


def _sumar_meses(fecha: date, n: int) -> date:
    return _restar_meses(fecha, -n)


def generar_historial(linea: str, meses: int = 24, fin: date | None = None) -> pd.DataFrame:
    """Simula ``meses`` de demanda mensual de una línea. [Simulado]

    Columnas: ``Fecha`` (inicio de mes), ``Presion_informal`` (0-1, como la que se
    estimaría a partir del tipo de cambio paralelo) y ``Pares_vendidos`` (ventas
    formales de Manaco, ya reducidas por la competencia informal).
    """
    if linea not in _NIVEL_BASE:
        raise ValueError(f"Línea desconocida: {linea}")
    rnd = random.Random(f"{_SEMILLA}-{linea}")
    fin = fin or date.today()
    meses_fin = date(fin.year, fin.month, 1)
    fechas = [_restar_meses(meses_fin, meses - 1 - i) for i in range(meses)]

    nivel, sensibilidad = _NIVEL_BASE[linea], SENSIBILIDAD_INFORMAL[linea]
    filas = []
    for i, fecha in enumerate(fechas):
        # Tendencia sostenida al alza (como la escasez de dólares del caso), no un paseo
        # aleatorio: así un pronóstico que la ignora acumula error con el tiempo.
        presion = min(0.9, max(0.05, 0.08 + 0.032 * i + rnd.uniform(-0.015, 0.015)))
        estacional = 1.25 if fecha.month in _MESES_PICO else 1.0
        tendencia = 1 + 0.004 * i
        ruido = rnd.gauss(1.0, 0.05)
        demanda = nivel * estacional * tendencia * ruido
        vendidos = demanda * (1 - sensibilidad * presion)
        filas.append((fecha, round(presion, 3), round(vendidos)))
    return pd.DataFrame(filas, columns=["Fecha", "Presion_informal", "Pares_vendidos"])


def promedio_movil_estacional(serie: pd.Series, fechas: pd.Series, ventana: int = 3) -> pd.Series:
    """Promedio móvil de ``ventana`` meses, ajustado por el índice estacional de cada mes."""
    base = serie.rolling(ventana, min_periods=1).mean()
    promedio_general = serie.mean()
    indice = serie.groupby(fechas.dt.month).transform(lambda s: s.mean() / promedio_general)
    return base * indice.fillna(1.0)


def _demanda_implicita(historial: pd.DataFrame, sensibilidad: float) -> pd.Series:
    """Reconstruye la demanda subyacente dividiendo las ventas por el efecto informal estimado."""
    return historial["Pares_vendidos"] / (1 - sensibilidad * historial["Presion_informal"])


def pronosticar(
    historial: pd.DataFrame, linea: str, meses_adelante: int = 6, presion_informal: float | None = None,
) -> pd.DataFrame:
    """Proyecta ``meses_adelante`` meses: pronóstico base (ignora el mercado informal) y
    pronóstico ajustado (reconstruye la demanda implícita y le aplica la presión informal
    proyectada, o la que se indique en ``presion_informal`` para simular un escenario)."""
    sensibilidad = SENSIBILIDAD_INFORMAL[linea]
    fechas = pd.to_datetime(historial["Fecha"])
    demanda_implicita = _demanda_implicita(historial, sensibilidad)

    nivel_ventas = float(promedio_movil_estacional(historial["Pares_vendidos"], fechas).iloc[-1])
    nivel_demanda = float(promedio_movil_estacional(demanda_implicita, fechas).iloc[-1])
    ultima_fecha, presion_actual = historial["Fecha"].iloc[-1], float(historial["Presion_informal"].iloc[-1])
    tendencia_presion = float(historial["Presion_informal"].diff().tail(6).mean() or 0.0)

    filas = []
    for i in range(1, meses_adelante + 1):
        fecha = _sumar_meses(ultima_fecha, i)
        indice_mes = 1.25 if fecha.month in _MESES_PICO else 1.0
        presion_proy = (
            presion_informal if presion_informal is not None
            else min(0.95, max(0.0, presion_actual + tendencia_presion * i))
        )
        filas.append((
            fecha, round(nivel_ventas * indice_mes),
            round(nivel_demanda * indice_mes * (1 - sensibilidad * presion_proy)),
            round(presion_proy, 3),
        ))
    return pd.DataFrame(
        filas, columns=["Fecha", "Pronostico_base", "Pronostico_ajustado", "Presion_informal_proyectada"],
    )


def backtest(historial: pd.DataFrame, linea: str, meses_prueba: int = 6) -> ResultadoBacktest:
    """MAPE del pronóstico base vs. el ajustado sobre los últimos ``meses_prueba`` meses conocidos."""
    sensibilidad = SENSIBILIDAD_INFORMAL[linea]
    fechas = pd.to_datetime(historial["Fecha"])
    demanda_implicita = _demanda_implicita(historial, sensibilidad)

    base_pred = promedio_movil_estacional(historial["Pares_vendidos"], fechas).shift(1)
    demanda_pred = promedio_movil_estacional(demanda_implicita, fechas).shift(1)
    ajustado_pred = demanda_pred * (1 - sensibilidad * historial["Presion_informal"])

    recorte = slice(-meses_prueba, None)
    reales = historial["Pares_vendidos"]
    return ResultadoBacktest(
        mape_base=_mape(reales[recorte], base_pred[recorte]),
        mape_ajustado=_mape(reales[recorte], ajustado_pred[recorte]),
    )


def _mape(reales: pd.Series, predichos: pd.Series) -> float:
    reales, predichos = reales.reset_index(drop=True), predichos.reset_index(drop=True)
    mascara = (reales != 0) & predichos.notna()
    if not mascara.any():
        return 0.0
    errores = (reales[mascara] - predichos[mascara]).abs() / reales[mascara].abs()
    return float(errores.mean() * 100)


def brecha_precio(precio_linea: float, precio_promedio: float, precio_informal_promedio: float,
                  tipo_cambio: float, tipo_cambio_actual: float) -> float:
    """Brecha (%) entre el precio de una línea de Manaco y el del calzado informal equivalente.

    ``ref_mercado_local`` guarda un solo precio informal para todo el mercado, así que se usa
    como **descuento informal promedio** (precio informal ÷ precio promedio de Manaco) y se
    aplica al precio de cada línea, para comparar calzado equivalente. [Supuesto]: el
    descuento es igual en todas las líneas y el precio informal sube en bolivianos en la
    misma proporción que el tipo de cambio paralelo, porque ese calzado se compra en dólares.
    """
    if not (precio_linea > 0 and precio_promedio > 0 and precio_informal_promedio > 0
            and tipo_cambio > 0 and tipo_cambio_actual > 0):
        return 0.0
    descuento_informal = precio_informal_promedio / precio_promedio
    precio_informal_linea = precio_linea * descuento_informal * (tipo_cambio / tipo_cambio_actual)
    return (precio_linea - precio_informal_linea) / precio_informal_linea * 100
