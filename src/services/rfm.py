"""Segmentación de clientes por Recencia, Frecuencia y Monto (RFM).

Este módulo no depende de Streamlit. Calcula los tres indicadores a partir del
historial de ``Venta`` de cada ``Cliente``, los convierte en una escala 1–5 por
quintiles y clasifica el resultado en un segmento de negocio.
"""

from __future__ import annotations

from datetime import date, datetime

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import SEGMENTO_FRECUENTE, SEGMENTO_INACTIVO, SEGMENTO_NUEVO, SEGMENTO_RIESGO, SEGMENTO_VIP
from src.models import Cliente, PerfilRfm, Venta


class ErrorNegocio(Exception):
    """Una regla de negocio impide la operación. El mensaje es apto para el usuario."""


def _escala_1_a_5(serie: pd.Series, mayor_es_mejor: bool) -> pd.Series:
    """Convierte una serie numérica en una escala 1–5 por percentil (quintiles)."""
    percentil = serie.rank(method="average", pct=True, ascending=mayor_es_mejor)
    return np.ceil(percentil * 5).clip(lower=1, upper=5).astype(int)


def clasificar_segmento(score_r: int, score_f: int, score_m: int) -> str:
    """Regla de negocio asumida para pasar de los 3 puntajes a un segmento accionable.

    Cliente nuevo: una sola compra (F=1) pero reciente (R alto). VIP: compra seguido,
    reciente y gasta mucho. En riesgo: solía comprar seguido pero hace tiempo que no
    vuelve (R bajo, F medio/alto). Inactivo: ni compra seguido ni recientemente.
    Todo lo demás cae en "Frecuentes".
    """
    if score_f == 1 and score_r >= 4:
        return SEGMENTO_NUEVO
    if score_r >= 4 and score_f >= 4 and score_m >= 4:
        return SEGMENTO_VIP
    if score_r <= 2 and score_f >= 3:
        return SEGMENTO_RIESGO
    if score_r <= 2 and score_f <= 2:
        return SEGMENTO_INACTIVO
    return SEGMENTO_FRECUENTE


def calcular_rfm(sesion: Session, fecha_referencia: date | None = None) -> pd.DataFrame:
    """RFM crudo y puntuado por cliente. Solo considera ventas con ``cliente_id`` registrado."""
    fecha_referencia = fecha_referencia or date.today()
    filas = sesion.execute(
        select(Venta.cliente_id, Venta.fecha, Venta.cantidad, Venta.precio_unitario_bs, Venta.descuento_bs)
        .where(Venta.cliente_id.is_not(None))
    ).all()
    if not filas:
        return pd.DataFrame(columns=[
            "cliente_id", "recencia_dias", "frecuencia", "monto_total_bs", "score_r", "score_f", "score_m",
            "segmento",
        ])

    datos = pd.DataFrame(filas, columns=["cliente_id", "fecha", "cantidad", "precio_unitario_bs", "descuento_bs"])
    datos["monto"] = datos["cantidad"] * datos["precio_unitario_bs"] - datos["descuento_bs"]
    resumen = datos.groupby("cliente_id").agg(
        ultima_compra=("fecha", "max"), frecuencia=("fecha", "count"), monto_total_bs=("monto", "sum"),
    ).reset_index()
    resumen["recencia_dias"] = resumen["ultima_compra"].apply(lambda f: (fecha_referencia - f).days)
    resumen["score_r"] = _escala_1_a_5(resumen["recencia_dias"], mayor_es_mejor=False)
    resumen["score_f"] = _escala_1_a_5(resumen["frecuencia"], mayor_es_mejor=True)
    resumen["score_m"] = _escala_1_a_5(resumen["monto_total_bs"], mayor_es_mejor=True)
    resumen["segmento"] = resumen.apply(
        lambda r: clasificar_segmento(int(r.score_r), int(r.score_f), int(r.score_m)), axis=1)
    return resumen.drop(columns=["ultima_compra"])


def actualizar_perfiles_rfm(sesion: Session, fecha_referencia: date | None = None) -> pd.DataFrame:
    """Recalcula el RFM de todos los clientes con ventas y guarda (o actualiza) su ``PerfilRfm``."""
    resumen = calcular_rfm(sesion, fecha_referencia)
    for _, fila in resumen.iterrows():
        cliente_id = int(fila.cliente_id)
        perfil = sesion.scalar(select(PerfilRfm).where(PerfilRfm.cliente_id == cliente_id))
        if perfil is None:
            perfil = PerfilRfm(cliente_id=cliente_id)
            sesion.add(perfil)
        perfil.recencia_dias = int(fila.recencia_dias)
        perfil.frecuencia = int(fila.frecuencia)
        perfil.monto_total_bs = float(fila.monto_total_bs)
        perfil.score_r = int(fila.score_r)
        perfil.score_f = int(fila.score_f)
        perfil.score_m = int(fila.score_m)
        perfil.segmento = fila.segmento
        perfil.calculado_en = datetime.now()
    sesion.flush()
    return resumen


def tabla_segmentos(sesion: Session, segmento: str | None = None) -> pd.DataFrame:
    """Tabla de perfiles RFM ya calculados, lista para mostrar en la UI."""
    consulta = select(PerfilRfm).join(Cliente)
    if segmento is not None:
        consulta = consulta.where(PerfilRfm.segmento == segmento)
    filas = sesion.scalars(consulta.order_by(PerfilRfm.monto_total_bs.desc())).all()
    return pd.DataFrame([
        {"id": p.id, "Cliente": p.cliente.nombre, "Segmento": p.segmento, "Recencia (días)": p.recencia_dias,
         "Frecuencia": p.frecuencia, "Monto total Bs": p.monto_total_bs, "R": p.score_r, "F": p.score_f,
         "M": p.score_m, "Calculado": p.calculado_en}
        for p in filas
    ])


def resumen_segmentos(sesion: Session) -> pd.DataFrame:
    """Clientes y monto total por segmento, para las tarjetas KPI de la página."""
    tabla = tabla_segmentos(sesion)
    if tabla.empty:
        return pd.DataFrame(columns=["Segmento", "Clientes", "Monto total Bs"])
    return tabla.groupby("Segmento", as_index=False).agg(
        Clientes=("Cliente", "count"), **{"Monto total Bs": ("Monto total Bs", "sum")},
    )
