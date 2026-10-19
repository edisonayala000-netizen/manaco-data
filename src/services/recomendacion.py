"""Motor de recomendación de venta cruzada (cesta de mercado) y su respaldo por atributos.

Agrupa las ventas en "cestas" por (fecha, tienda, cliente) — supuesto explícito,
ya que el sistema no registra un carrito/transacción con identificador propio —
y aplica FP-Growth/Apriori (``mlxtend``) para encontrar reglas de asociación.
Si un producto no tiene suficientes ventas o ninguna regla lo cubre, cae al
respaldo por atributos (misma categoría y, si alcanza, mismo color).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules, fpgrowth
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.config import CONFIANZA_MINIMA_ASOCIACION, MINIMO_VENTAS_ASOCIACION, SOPORTE_MINIMO_ASOCIACION
from src.models import Producto, RecomendacionLog, Venta

METODO_ASOCIACION = "ASOCIACION"
METODO_ATRIBUTOS = "ATRIBUTOS"
TOP_N = 3


class ErrorNegocio(Exception):
    """Una regla de negocio impide la operación. El mensaje es apto para el usuario."""


@dataclass(frozen=True)
class Recomendacion:
    """Un producto recomendado, con el método y las métricas que lo respaldan."""

    producto_id: int
    codigo: str
    nombre: str
    metodo: str
    soporte: float | None = None
    confianza: float | None = None
    lift: float | None = None


def _construir_cestas(sesion: Session) -> pd.DataFrame:
    """Matriz booleana cesta × producto. Cesta = (fecha, tienda, cliente)."""
    filas = sesion.execute(select(Venta.fecha, Venta.tienda_id, Venta.cliente_id, Venta.producto_id)).all()
    if not filas:
        return pd.DataFrame()
    datos = pd.DataFrame(filas, columns=["fecha", "tienda_id", "cliente_id", "producto_id"])
    datos["cesta"] = (
        datos["fecha"].astype(str) + "_" + datos["tienda_id"].astype(str) + "_"
        + datos["cliente_id"].where(datos["cliente_id"].notna(), -1).astype(int).astype(str)
    )
    return pd.crosstab(datos["cesta"], datos["producto_id"]).astype(bool)


def generar_reglas(sesion: Session, metodo: str = "fpgrowth") -> pd.DataFrame:
    """Reglas de asociación (antecedents/consequents/support/confidence/lift) sobre todas las cestas.

    Devuelve un DataFrame vacío si hay muy pocas cestas para que el resultado sea confiable
    (``MINIMO_VENTAS_ASOCIACION``) o si ningún conjunto de productos alcanza el soporte mínimo.
    """
    cestas = _construir_cestas(sesion)
    if cestas.empty or len(cestas) < MINIMO_VENTAS_ASOCIACION:
        return pd.DataFrame()
    algoritmo = fpgrowth if metodo == "fpgrowth" else apriori
    frecuentes = algoritmo(cestas, min_support=SOPORTE_MINIMO_ASOCIACION, use_colnames=True)
    if frecuentes.empty:
        return pd.DataFrame()
    reglas = association_rules(frecuentes, metric="confidence", min_threshold=CONFIANZA_MINIMA_ASOCIACION)
    return reglas.sort_values("lift", ascending=False)


def _top_por_atributos(sesion: Session, producto: Producto, excluir: set[int]) -> list[Recomendacion]:
    """Respaldo: productos activos de la misma categoría (y, si alcanza, mismo color), por popularidad."""
    ventas_por_producto = dict(sesion.execute(select(Venta.producto_id, func.count()).group_by(Venta.producto_id)).all())
    candidatos = sesion.scalars(
        select(Producto).where(
            Producto.categoria == producto.categoria, Producto.id != producto.id, Producto.activo.is_(True),
        )
    ).all()
    candidatos = [c for c in candidatos if c.id not in excluir]
    mismo_color = [c for c in candidatos if c.color == producto.color]
    ordenados = sorted(mismo_color or candidatos, key=lambda c: ventas_por_producto.get(c.id, 0), reverse=True)
    return [Recomendacion(c.id, c.codigo_modelo, c.nombre, METODO_ATRIBUTOS) for c in ordenados[:TOP_N]]


def recomendar(sesion: Session, producto_id: int) -> list[Recomendacion]:
    """Top-3 productos complementarios: reglas de asociación primero, respaldo por atributos si faltan."""
    producto = sesion.get(Producto, producto_id)
    if producto is None:
        raise ErrorNegocio("El producto no existe.")

    recomendaciones: list[Recomendacion] = []
    vistos = {producto_id}
    reglas = generar_reglas(sesion)
    if not reglas.empty:
        propias = reglas[reglas["antecedents"] == frozenset({producto_id})]
        for _, fila in propias.iterrows():
            if len(recomendaciones) >= TOP_N:
                break
            for consecuente_id in fila["consequents"]:
                if consecuente_id in vistos:
                    continue
                consecuente = sesion.get(Producto, consecuente_id)
                if consecuente is None or not consecuente.activo:
                    continue
                recomendaciones.append(Recomendacion(
                    consecuente.id, consecuente.codigo_modelo, consecuente.nombre, METODO_ASOCIACION,
                    soporte=float(fila["support"]), confianza=float(fila["confidence"]), lift=float(fila["lift"]),
                ))
                vistos.add(consecuente_id)
                if len(recomendaciones) >= TOP_N:
                    break

    if len(recomendaciones) < TOP_N:
        faltan = TOP_N - len(recomendaciones)
        recomendaciones.extend(_top_por_atributos(sesion, producto, vistos)[:faltan])

    return recomendaciones[:TOP_N]


def registrar_recomendacion_mostrada(
    sesion: Session, producto_base_id: int, recomendacion: Recomendacion, cliente_id: int | None = None,
) -> RecomendacionLog:
    """Audita cada recomendación mostrada; ``marcar_aceptada`` se llama si el cliente la compra."""
    log = RecomendacionLog(
        producto_base_id=producto_base_id, producto_recomendado_id=recomendacion.producto_id,
        metodo=recomendacion.metodo, soporte=recomendacion.soporte, confianza=recomendacion.confianza,
        lift=recomendacion.lift, cliente_id=cliente_id,
    )
    sesion.add(log)
    sesion.flush()
    return log


def marcar_aceptada(sesion: Session, log_id: int, aceptada: bool = True) -> RecomendacionLog:
    log = sesion.get(RecomendacionLog, log_id)
    if log is None:
        raise ErrorNegocio("El registro de recomendación no existe.")
    log.aceptada = aceptada
    sesion.flush()
    return log


def tasa_conversion(sesion: Session) -> pd.DataFrame:
    """Tasa de aceptación por método (asociación vs. atributos), para medir si el motor funciona."""
    filas = sesion.execute(select(RecomendacionLog.metodo, RecomendacionLog.aceptada)).all()
    if not filas:
        return pd.DataFrame(columns=["Método", "Mostradas", "Aceptadas", "Tasa de conversión"])
    datos = pd.DataFrame(filas, columns=["Método", "Aceptada"])
    resumen = datos.groupby("Método").agg(
        Mostradas=("Aceptada", "size"), Aceptadas=("Aceptada", lambda s: int((s == True).sum())),  # noqa: E712
    ).reset_index()
    resumen["Tasa de conversión"] = (resumen["Aceptadas"] / resumen["Mostradas"]).round(3)
    return resumen
