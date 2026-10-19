"""Motor de promociones (carrito) y campañas de marketing digital con cupón y UTM.

Este módulo no depende de Streamlit. ``evaluar_carrito`` recibe una lista de
líneas (producto, cantidad, precio) y un cupón opcional, y devuelve el
descuento total a aplicar antes de cobrar — no toca la base de datos. Guardar
la venta con su descuento y registrar la conversión de campaña son pasos
explícitos aparte, para que cada uno se pueda probar por separado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import CANALES_CAMPANA, TIPO_PROMO_COMBO, TIPO_PROMO_MONTO_FIJO, TIPO_PROMO_PORCENTAJE, TIPOS_PROMOCION
from src.models import CampanaMarketing, ConversionCampana, Producto, ReglaPromocion
from src.services import contabilidad


class ErrorNegocio(Exception):
    """Una regla de negocio impide la operación. El mensaje es apto para el usuario."""


@dataclass(frozen=True)
class ItemCarrito:
    """Una línea del carrito antes de cobrar: producto, cantidad y precio de lista."""

    producto_id: int
    cantidad: int
    precio_unitario_bs: float
    categoria: str


@dataclass
class ResultadoPromocion:
    """Descuento total del carrito y el detalle de qué regla lo generó."""

    descuento_total_bs: float = 0.0
    detalles: list[str] = field(default_factory=list)
    reglas_aplicadas: list[int] = field(default_factory=list)


# --- Reglas de promoción ---------------------------------------------------------

def crear_regla_promocion(
    sesion: Session, nombre: str, tipo: str, fecha_inicio: date, valor: float = 0.0,
    producto_id: int | None = None, categoria: str | None = None, cantidad_necesaria: int | None = None,
    cantidad_gratis: int | None = None, campana_id: int | None = None, fecha_fin: date | None = None,
) -> ReglaPromocion:
    if tipo not in TIPOS_PROMOCION:
        raise ErrorNegocio(f"Tipo de promoción inválido: {tipo}.")
    if producto_id is None and categoria is None:
        raise ErrorNegocio("La regla necesita un producto o una categoría objetivo.")
    if tipo == TIPO_PROMO_PORCENTAJE and not (0 < valor <= 100):
        raise ErrorNegocio("El porcentaje de descuento debe estar entre 0 y 100.")
    if tipo == TIPO_PROMO_MONTO_FIJO and valor <= 0:
        raise ErrorNegocio("El monto fijo de descuento debe ser mayor a 0.")
    if tipo == TIPO_PROMO_COMBO:
        if not cantidad_necesaria or not cantidad_gratis:
            raise ErrorNegocio("El combo necesita cantidad necesaria y cantidad gratis (p. ej. 3x2 → 3 y 1).")
        if cantidad_gratis >= cantidad_necesaria:
            raise ErrorNegocio("En un combo, las unidades gratis deben ser menos que las unidades necesarias.")
    if fecha_fin is not None and fecha_fin < fecha_inicio:
        raise ErrorNegocio("La fecha de fin no puede ser anterior a la fecha de inicio.")

    regla = ReglaPromocion(
        nombre=nombre, tipo=tipo, valor=valor, producto_id=producto_id, categoria=categoria,
        cantidad_necesaria=cantidad_necesaria, cantidad_gratis=cantidad_gratis, campana_id=campana_id,
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
    )
    sesion.add(regla)
    sesion.flush()
    return regla


def tabla_reglas_promocion(sesion: Session, solo_activas: bool = False) -> pd.DataFrame:
    consulta = select(ReglaPromocion)
    if solo_activas:
        consulta = consulta.where(ReglaPromocion.activa.is_(True))
    filas = sesion.scalars(consulta.order_by(ReglaPromocion.fecha_inicio.desc())).all()
    return pd.DataFrame([
        {"id": r.id, "Nombre": r.nombre, "Tipo": r.tipo, "Valor": r.valor,
         "Producto": r.producto.codigo_modelo if r.producto else None, "Categoría": r.categoria,
         "Cant. necesaria": r.cantidad_necesaria, "Cant. gratis": r.cantidad_gratis,
         "Inicio": r.fecha_inicio, "Fin": r.fecha_fin, "Activa": r.activa}
        for r in filas
    ])


def _reglas_vigentes(sesion: Session, fecha: date, cupon_codigo: str | None) -> list[ReglaPromocion]:
    consulta = select(ReglaPromocion).where(
        ReglaPromocion.activa.is_(True), ReglaPromocion.fecha_inicio <= fecha,
        (ReglaPromocion.fecha_fin.is_(None)) | (ReglaPromocion.fecha_fin >= fecha),
    )
    reglas = list(sesion.scalars(consulta).all())
    if cupon_codigo is None:
        return [r for r in reglas if r.campana_id is None]

    campana = sesion.scalar(select(CampanaMarketing).where(CampanaMarketing.codigo_cupon == cupon_codigo))
    if campana is None or not campana.activa:
        raise ErrorNegocio(f"El cupón {cupon_codigo} no existe o ya no está activo.")
    return [r for r in reglas if r.campana_id is None or r.campana_id == campana.id]


def _coincide(regla: ReglaPromocion, item: ItemCarrito) -> bool:
    if regla.producto_id is not None:
        return regla.producto_id == item.producto_id
    return regla.categoria == item.categoria


def evaluar_carrito(
    sesion: Session, items: list[ItemCarrito], cupon_codigo: str | None = None, fecha: date | None = None,
) -> ResultadoPromocion:
    """Aplica todas las reglas vigentes (y las del cupón, si se indica) al carrito."""
    if not items:
        raise ErrorNegocio("El carrito está vacío.")
    fecha = fecha or date.today()
    resultado = ResultadoPromocion()

    for regla in _reglas_vigentes(sesion, fecha, cupon_codigo):
        coincidentes = [i for i in items if _coincide(regla, i)]
        if not coincidentes:
            continue

        if regla.tipo == TIPO_PROMO_PORCENTAJE:
            subtotal = sum(i.cantidad * i.precio_unitario_bs for i in coincidentes)
            descuento = round(subtotal * regla.valor / 100, 2)
            if descuento <= 0:
                continue
            resultado.descuento_total_bs += descuento
            resultado.detalles.append(f"{regla.nombre}: -{regla.valor:.0f}% ({descuento:.2f} Bs)")
            resultado.reglas_aplicadas.append(regla.id)

        elif regla.tipo == TIPO_PROMO_MONTO_FIJO:
            unidades = sum(i.cantidad for i in coincidentes)
            if regla.cantidad_necesaria and unidades < regla.cantidad_necesaria:
                continue
            descuento = round(regla.valor, 2)
            resultado.descuento_total_bs += descuento
            resultado.detalles.append(f"{regla.nombre}: -{descuento:.2f} Bs")
            resultado.reglas_aplicadas.append(regla.id)

        elif regla.tipo == TIPO_PROMO_COMBO:
            unidades = []
            for i in coincidentes:
                unidades.extend([i.precio_unitario_bs] * i.cantidad)
            unidades.sort()  # las unidades más baratas son las que se regalan
            sets_completos = len(unidades) // regla.cantidad_necesaria
            unidades_gratis = sets_completos * regla.cantidad_gratis
            if unidades_gratis <= 0:
                continue
            descuento = round(sum(unidades[:unidades_gratis]), 2)
            resultado.descuento_total_bs += descuento
            resultado.detalles.append(
                f"{regla.nombre}: {regla.cantidad_necesaria}x{regla.cantidad_necesaria - regla.cantidad_gratis} "
                f"→ {unidades_gratis} par(es) gratis ({descuento:.2f} Bs)")
            resultado.reglas_aplicadas.append(regla.id)

    resultado.descuento_total_bs = round(resultado.descuento_total_bs, 2)
    return resultado


# --- Campañas de marketing --------------------------------------------------------

def crear_campana(
    sesion: Session, nombre: str, canal: str, codigo_cupon: str, utm_source: str, utm_campaign: str,
    fecha_inicio: date, utm_medium: str = "social", fecha_fin: date | None = None, presupuesto_bs: float = 0.0,
) -> CampanaMarketing:
    if canal not in CANALES_CAMPANA:
        raise ErrorNegocio(f"Canal inválido: {canal}.")
    if not codigo_cupon.strip():
        raise ErrorNegocio("La campaña necesita un código de cupón único.")
    codigo_cupon = codigo_cupon.strip().upper()
    if sesion.scalar(select(CampanaMarketing).where(CampanaMarketing.codigo_cupon == codigo_cupon)):
        raise ErrorNegocio(f"Ya existe una campaña con el cupón {codigo_cupon}.")

    campana = CampanaMarketing(
        nombre=nombre, canal=canal, codigo_cupon=codigo_cupon, utm_source=utm_source,
        utm_medium=utm_medium, utm_campaign=utm_campaign, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
        presupuesto_bs=presupuesto_bs,
    )
    sesion.add(campana)
    sesion.flush()
    return campana


def generar_enlace_utm(campana: CampanaMarketing, url_base: str = "https://manaco.bo/tienda") -> str:
    """Enlace con parámetros UTM y el cupón, listo para pegar en la campaña de redes sociales."""
    return (
        f"{url_base}?utm_source={campana.utm_source}&utm_medium={campana.utm_medium}"
        f"&utm_campaign={campana.utm_campaign}&cupon={campana.codigo_cupon}"
    )


def tabla_campanas(sesion: Session, solo_activas: bool = False) -> pd.DataFrame:
    consulta = select(CampanaMarketing)
    if solo_activas:
        consulta = consulta.where(CampanaMarketing.activa.is_(True))
    filas = sesion.scalars(consulta.order_by(CampanaMarketing.fecha_inicio.desc())).all()
    return pd.DataFrame([
        {"id": c.id, "Nombre": c.nombre, "Canal": c.canal, "Cupón": c.codigo_cupon,
         "UTM campaign": c.utm_campaign, "Inicio": c.fecha_inicio, "Fin": c.fecha_fin,
         "Presupuesto Bs": c.presupuesto_bs, "Activa": c.activa, "Enlace": generar_enlace_utm(c)}
        for c in filas
    ])


def registrar_conversion(
    sesion: Session, campana_id: int, monto_bs: float, fecha: date, venta_id: int | None = None,
    cliente_id: int | None = None, descuento_bs: float = 0.0,
) -> ConversionCampana:
    """Registra una venta atribuida a la campaña y, si hubo descuento, su asiento contable."""
    campana = sesion.get(CampanaMarketing, campana_id)
    if campana is None:
        raise ErrorNegocio("La campaña no existe.")
    conversion = ConversionCampana(
        campana_id=campana_id, venta_id=venta_id, cliente_id=cliente_id,
        monto_bs=monto_bs, descuento_bs=descuento_bs, fecha=fecha,
    )
    sesion.add(conversion)
    sesion.flush()
    if descuento_bs > 0:
        contabilidad.registrar_descuento_promocion(sesion, fecha, descuento_bs, referencia_id=conversion.id)
    return conversion


def roas_por_campana(sesion: Session) -> pd.DataFrame:
    """ROAS = monto generado / presupuesto invertido, por campaña."""
    campanas = sesion.scalars(select(CampanaMarketing)).all()
    filas = []
    for c in campanas:
        conversiones = sesion.scalars(select(ConversionCampana).where(ConversionCampana.campana_id == c.id)).all()
        monto_total = sum(conv.monto_bs for conv in conversiones)
        roas = round(monto_total / c.presupuesto_bs, 2) if c.presupuesto_bs > 0 else None
        filas.append({
            "Campaña": c.nombre, "Canal": c.canal, "Cupón": c.codigo_cupon, "Conversiones": len(conversiones),
            "Monto generado Bs": round(monto_total, 2), "Presupuesto Bs": c.presupuesto_bs, "ROAS": roas,
        })
    return pd.DataFrame(filas)
