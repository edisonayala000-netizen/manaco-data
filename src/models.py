"""Modelos SQLAlchemy 2.x del sistema Manaco Data."""

from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import (
    Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, Time,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Clase base de todos los modelos."""


class Usuario(Base):
    """Persona que usa el sistema, con su rol."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    usuario: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hash_contrasena: Mapped[str] = mapped_column(String(100))
    rol: Mapped[str] = mapped_column(String(20))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Tienda(Base):
    """Tienda o almacén de Manaco."""

    __tablename__ = "tiendas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True)
    ciudad: Mapped[str] = mapped_column(String(40))
    tipo: Mapped[str] = mapped_column(String(20), default="tienda")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Producto(Base):
    """Modelo de calzado (un código por talla y color)."""

    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo_modelo: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    categoria: Mapped[str] = mapped_column(String(30))
    codigo_sa6: Mapped[int] = mapped_column(Integer)
    talla: Mapped[str] = mapped_column(String(10))
    color: Mapped[str] = mapped_column(String(30))
    precio_venta_bs: Mapped[float] = mapped_column(Float)
    costo_bs: Mapped[float] = mapped_column(Float)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Apertura(Base):
    """Saldo inicial de un producto en una tienda al empezar el día."""

    __tablename__ = "aperturas"
    __table_args__ = (UniqueConstraint("fecha", "tienda_id", "producto_id", name="uq_apertura_dia"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tiendas.id"))
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    saldo_inicial: Mapped[int] = mapped_column(Integer)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    tienda: Mapped[Tienda] = relationship()
    producto: Mapped[Producto] = relationship()


class Venta(Base):
    """Venta de uno o más pares de un producto."""

    __tablename__ = "ventas"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    hora: Mapped[time] = mapped_column(Time)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tiendas.id"))
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    cantidad: Mapped[int] = mapped_column(Integer)
    precio_unitario_bs: Mapped[float] = mapped_column(Float)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"), nullable=True, index=True)
    cupon_codigo: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    descuento_bs: Mapped[float] = mapped_column(Float, default=0.0)

    tienda: Mapped[Tienda] = relationship()
    producto: Mapped[Producto] = relationship()
    cliente: Mapped["Cliente | None"] = relationship()


class Cierre(Base):
    """Conteo de cierre y conciliación contra el saldo esperado."""

    __tablename__ = "cierres"
    __table_args__ = (UniqueConstraint("fecha", "tienda_id", "producto_id", name="uq_cierre_dia"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tiendas.id"))
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    saldo_inicial: Mapped[int] = mapped_column(Integer)
    total_vendido: Mapped[int] = mapped_column(Integer)
    saldo_esperado: Mapped[int] = mapped_column(Integer)
    conteo_ia: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conteo_final: Mapped[int] = mapped_column(Integer)
    diferencia: Mapped[int] = mapped_column(Integer)
    estado: Mapped[str] = mapped_column(String(20))
    foto_ruta: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confianza_ia: Mapped[float | None] = mapped_column(Float, nullable=True)
    observacion: Mapped[str] = mapped_column(Text, default="")
    alerta_atendida: Mapped[bool] = mapped_column(Boolean, default=False)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    tienda: Mapped[Tienda] = relationship()
    producto: Mapped[Producto] = relationship()


class AnulacionCierre(Base):
    """Registro de auditoría de un cierre anulado por el administrador."""

    __tablename__ = "anulaciones_cierre"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date)
    tienda_id: Mapped[int] = mapped_column(Integer)
    producto_id: Mapped[int] = mapped_column(Integer)
    conteo_final: Mapped[int] = mapped_column(Integer)
    diferencia: Mapped[int] = mapped_column(Integer)
    estado: Mapped[str] = mapped_column(String(20))
    motivo: Mapped[str] = mapped_column(Text)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    anulado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ComercioExterior(Base):
    """Registro de comercio exterior de calzado (Excel limpio)."""

    __tablename__ = "comercio_exterior"

    id: Mapped[int] = mapped_column(primary_key=True)
    pais_reportante: Mapped[str] = mapped_column(String(60))
    flujo_comercial: Mapped[str] = mapped_column(String(20))
    anio: Mapped[int] = mapped_column(Integer)
    codigo_sa6: Mapped[int] = mapped_column(Integer)
    categoria_calzado: Mapped[str] = mapped_column(String(150))
    socio_comercial: Mapped[str] = mapped_column(String(80))
    valor_miles_usd: Mapped[float] = mapped_column(Float)
    cantidad_pares: Mapped[int] = mapped_column(Integer)
    valor_usd: Mapped[float] = mapped_column(Float)
    valor_usd_por_par: Mapped[float] = mapped_column(Float)
    registro_valido: Mapped[bool] = mapped_column(Boolean, default=True)


class BitacoraLimpieza(Base):
    """Cada regla de limpieza aplicada al Excel y su efecto."""

    __tablename__ = "bitacora_limpieza"

    id: Mapped[int] = mapped_column(primary_key=True)
    regla: Mapped[str] = mapped_column(String(120))
    filas_afectadas: Mapped[int] = mapped_column(Integer)
    detalle: Mapped[str] = mapped_column(Text)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


# --- Esquema en estrella (Manaco_Caso_Solucion_y_Prototipo.md, sección 2) ----
# ``Producto`` ya cumple el rol de dim_producto, ``Tienda`` el de dim_tienda,
# ``Venta`` el de fact_ventas, ``Apertura``/``Cierre`` el de fact_inventario y
# ``ComercioExterior`` el de ref_comercio_exterior: no se duplican aquí.
# Las siguientes tablas completan las dimensiones y hechos que faltaban.


class DimFecha(Base):
    """Dimensión de calendario: una fila por día, con rasgos de estacionalidad."""

    __tablename__ = "dim_fecha"

    fecha: Mapped[date] = mapped_column(Date, primary_key=True)
    anio: Mapped[int] = mapped_column(Integer)
    mes: Mapped[int] = mapped_column(Integer)
    inicio_clases: Mapped[bool] = mapped_column(Boolean, default=False)
    feriado: Mapped[bool] = mapped_column(Boolean, default=False)


class FactProduccion(Base):
    """Lote de producción: pares fabricados y sus costos."""

    __tablename__ = "fact_produccion"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    lote: Mapped[str] = mapped_column(String(30))
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    pares: Mapped[int] = mapped_column(Integer)
    costo_insumos_bs: Mapped[float] = mapped_column(Float)
    costo_mano_obra_bs: Mapped[float] = mapped_column(Float)

    producto: Mapped[Producto] = relationship()


class FactCalidad(Base):
    """Defectos y devoluciones observados en un lote de producción."""

    __tablename__ = "fact_calidad"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    lote: Mapped[str] = mapped_column(String(30))
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    defectos: Mapped[int] = mapped_column(Integer, default=0)
    devoluciones: Mapped[int] = mapped_column(Integer, default=0)
    motivo: Mapped[str] = mapped_column(String(120), default="")

    producto: Mapped[Producto] = relationship()


class RefMercadoLocal(Base):
    """Referencia de precios de la competencia y tipo de cambio paralelo."""

    __tablename__ = "ref_mercado_local"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    ciudad: Mapped[str] = mapped_column(String(40))
    mercado: Mapped[str] = mapped_column(String(80))
    precio_competidor_bs: Mapped[float] = mapped_column(Float)
    tipo_cambio_paralelo: Mapped[float] = mapped_column(Float)


class LogIngesta(Base):
    """Registro de cada carga de datos recibida de una sucursal."""

    __tablename__ = "log_ingesta"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    sucursal: Mapped[str] = mapped_column(String(80))
    archivo: Mapped[str] = mapped_column(String(120))
    filas_leidas: Mapped[int] = mapped_column(Integer)
    filas_corregidas: Mapped[int] = mapped_column(Integer)
    filas_rechazadas: Mapped[int] = mapped_column(Integer)


# --- Módulo administrativo y de inventarios ----------------------------------
# ``Tienda`` (con ``tipo="almacén"``) ya cumple el rol de bodega/almacén: no se
# duplica aquí una entidad ``Almacen`` aparte.


class Proveedor(Base):
    """Proveedor de mercadería (compras al por mayor, insumos)."""

    __tablename__ = "proveedores"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    razon_social: Mapped[str] = mapped_column(String(160), default="")
    nit: Mapped[str] = mapped_column(String(30), default="")
    telefono: Mapped[str] = mapped_column(String(30), default="")
    email: Mapped[str] = mapped_column(String(120), default="")
    pais: Mapped[str] = mapped_column(String(60), default="Bolivia")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Inventario(Base):
    """Stock vigente de un producto en una tienda/almacén y su punto de reorden."""

    __tablename__ = "inventario"
    __table_args__ = (UniqueConstraint("producto_id", "tienda_id", name="uq_inventario_producto_tienda"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"), index=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tiendas.id"), index=True)
    stock_actual: Mapped[int] = mapped_column(Integer, default=0)
    stock_minimo: Mapped[int] = mapped_column(Integer, default=0)
    punto_reorden: Mapped[int] = mapped_column(Integer, default=0)
    proveedor_predeterminado_id: Mapped[int | None] = mapped_column(
        ForeignKey("proveedores.id"), nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    producto: Mapped[Producto] = relationship()
    tienda: Mapped[Tienda] = relationship()
    proveedor_predeterminado: Mapped["Proveedor | None"] = relationship()


class OrdenCompra(Base):
    """Orden de compra a un proveedor, manual o generada por alerta de stock."""

    __tablename__ = "ordenes_compra"

    id: Mapped[int] = mapped_column(primary_key=True)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id"))
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tiendas.id"))
    fecha_emision: Mapped[date] = mapped_column(Date, index=True)
    fecha_recepcion: Mapped[date | None] = mapped_column(Date, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="BORRADOR")
    origen: Mapped[str] = mapped_column(String(20), default="MANUAL")
    flete_bs: Mapped[float] = mapped_column(Float, default=0.0)
    arancel_bs: Mapped[float] = mapped_column(Float, default=0.0)
    subtotal_bs: Mapped[float] = mapped_column(Float, default=0.0)
    total_bs: Mapped[float] = mapped_column(Float, default=0.0)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    proveedor: Mapped[Proveedor] = relationship()
    tienda: Mapped[Tienda] = relationship()
    detalles: Mapped[list["DetalleOrdenCompra"]] = relationship(
        back_populates="orden_compra", cascade="all, delete-orphan")


class DetalleOrdenCompra(Base):
    """Línea de producto y cantidad dentro de una orden de compra."""

    __tablename__ = "detalle_orden_compra"

    id: Mapped[int] = mapped_column(primary_key=True)
    orden_compra_id: Mapped[int] = mapped_column(ForeignKey("ordenes_compra.id"))
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    cantidad: Mapped[int] = mapped_column(Integer)
    costo_unitario_bs: Mapped[float] = mapped_column(Float)
    cantidad_recibida: Mapped[int] = mapped_column(Integer, default=0)

    orden_compra: Mapped[OrdenCompra] = relationship(back_populates="detalles")
    producto: Mapped[Producto] = relationship()


class AlertaStock(Base):
    """Alerta de stock crítico (``stock_actual <= punto_reorden``) y su seguimiento."""

    __tablename__ = "alertas_stock"

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tiendas.id"))
    stock_actual: Mapped[int] = mapped_column(Integer)
    punto_reorden: Mapped[int] = mapped_column(Integer)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    atendida: Mapped[bool] = mapped_column(Boolean, default=False)
    orden_compra_id: Mapped[int | None] = mapped_column(ForeignKey("ordenes_compra.id"), nullable=True)

    producto: Mapped[Producto] = relationship()
    tienda: Mapped[Tienda] = relationship()
    orden_compra: Mapped["OrdenCompra | None"] = relationship()


# --- Módulo de machine learning: clientes, RFM y recomendaciones -------------


class Cliente(Base):
    """Cliente final, suficiente para segmentación RFM y trazabilidad de campañas."""

    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    documento: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)
    telefono: Mapped[str] = mapped_column(String(30), default="")
    email: Mapped[str] = mapped_column(String(120), default="")
    ciudad: Mapped[str] = mapped_column(String(40), default="")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class PerfilRfm(Base):
    """Último cálculo de Recencia, Frecuencia y Monto de un cliente, y su segmento."""

    __tablename__ = "perfiles_rfm"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), unique=True, index=True)
    recencia_dias: Mapped[int] = mapped_column(Integer)
    frecuencia: Mapped[int] = mapped_column(Integer)
    monto_total_bs: Mapped[float] = mapped_column(Float)
    score_r: Mapped[int] = mapped_column(Integer)
    score_f: Mapped[int] = mapped_column(Integer)
    score_m: Mapped[int] = mapped_column(Integer)
    segmento: Mapped[str] = mapped_column(String(20))
    calculado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    cliente: Mapped[Cliente] = relationship()


class RecomendacionLog(Base):
    """Auditoría de cada recomendación de venta cruzada mostrada, para medir conversión."""

    __tablename__ = "recomendaciones_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_base_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    producto_recomendado_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    metodo: Mapped[str] = mapped_column(String(20))
    soporte: Mapped[float | None] = mapped_column(Float, nullable=True)
    confianza: Mapped[float | None] = mapped_column(Float, nullable=True)
    lift: Mapped[float | None] = mapped_column(Float, nullable=True)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"), nullable=True)
    mostrada_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    aceptada: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    producto_base: Mapped[Producto] = relationship(foreign_keys=[producto_base_id])
    producto_recomendado: Mapped[Producto] = relationship(foreign_keys=[producto_recomendado_id])


# --- Módulo de marketing digital y promociones -------------------------------


class CampanaMarketing(Base):
    """Campaña de redes sociales con sus parámetros UTM y su cupón."""

    __tablename__ = "campanas_marketing"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    canal: Mapped[str] = mapped_column(String(20))
    codigo_cupon: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    utm_source: Mapped[str] = mapped_column(String(60))
    utm_medium: Mapped[str] = mapped_column(String(60), default="social")
    utm_campaign: Mapped[str] = mapped_column(String(80))
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    presupuesto_bs: Mapped[float] = mapped_column(Float, default=0.0)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)


class ReglaPromocion(Base):
    """Regla de descuento o combo evaluada por el motor de promociones en el carrito."""

    __tablename__ = "reglas_promocion"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    tipo: Mapped[str] = mapped_column(String(20))  # PORCENTAJE | MONTO_FIJO | COMBO_ESPECIAL
    valor: Mapped[float] = mapped_column(Float, default=0.0)
    producto_id: Mapped[int | None] = mapped_column(ForeignKey("productos.id"), nullable=True)
    categoria: Mapped[str | None] = mapped_column(String(30), nullable=True)
    cantidad_necesaria: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cantidad_gratis: Mapped[int | None] = mapped_column(Integer, nullable=True)
    campana_id: Mapped[int | None] = mapped_column(ForeignKey("campanas_marketing.id"), nullable=True)
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)

    producto: Mapped["Producto | None"] = relationship()
    campana: Mapped["CampanaMarketing | None"] = relationship()


class ConversionCampana(Base):
    """Conversión (venta) atribuida a una campaña, para calcular el ROAS."""

    __tablename__ = "conversiones_campana"

    id: Mapped[int] = mapped_column(primary_key=True)
    campana_id: Mapped[int] = mapped_column(ForeignKey("campanas_marketing.id"))
    venta_id: Mapped[int | None] = mapped_column(ForeignKey("ventas.id"), nullable=True)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"), nullable=True)
    monto_bs: Mapped[float] = mapped_column(Float)
    descuento_bs: Mapped[float] = mapped_column(Float, default=0.0)
    fecha: Mapped[date] = mapped_column(Date, index=True)

    campana: Mapped[CampanaMarketing] = relationship()


# --- Contabilidad: plan de cuentas y asientos (partida doble) ----------------


class CuentaContable(Base):
    """Cuenta del plan de cuentas mínimo usado por las integraciones automáticas."""

    __tablename__ = "cuentas_contables"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    tipo: Mapped[str] = mapped_column(String(20))  # ACTIVO | PASIVO | PATRIMONIO | INGRESO | GASTO
    naturaleza: Mapped[str] = mapped_column(String(10))  # DEUDORA | ACREEDORA


class AsientoContable(Base):
    """Encabezado de un asiento del libro diario, generado automáticamente."""

    __tablename__ = "asientos_contables"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    glosa: Mapped[str] = mapped_column(String(200))
    origen: Mapped[str] = mapped_column(String(20))  # COMPRA | PROMOCION | AJUSTE
    referencia_tipo: Mapped[str] = mapped_column(String(30), default="")
    referencia_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    detalles: Mapped[list["DetalleAsiento"]] = relationship(
        back_populates="asiento", cascade="all, delete-orphan")


class DetalleAsiento(Base):
    """Línea de debe/haber de un asiento contable."""

    __tablename__ = "detalle_asiento"

    id: Mapped[int] = mapped_column(primary_key=True)
    asiento_id: Mapped[int] = mapped_column(ForeignKey("asientos_contables.id"))
    cuenta_id: Mapped[int] = mapped_column(ForeignKey("cuentas_contables.id"))
    debe_bs: Mapped[float] = mapped_column(Float, default=0.0)
    haber_bs: Mapped[float] = mapped_column(Float, default=0.0)

    asiento: Mapped[AsientoContable] = relationship(back_populates="detalles")
    cuenta: Mapped[CuentaContable] = relationship()
