"""Configuración central de Manaco Data: rutas, constantes y reglas ajustables."""

from __future__ import annotations

import os
from pathlib import Path

# --- Rutas -------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = BASE_DIR / "data"
RAW_DIR: Path = DATA_DIR / "raw"
FOTOS_DIR: Path = DATA_DIR / "fotos"
MODELOS_DIR: Path = DATA_DIR / "modelos"
DB_PATH: Path = DATA_DIR / "manaco.db"
EXCEL_PATH: Path = RAW_DIR / "Base_de_Datos_MANACO.xlsx"
#: SQLite por defecto (cero configuración). Para usar el PostgreSQL de la arquitectura
#: propuesta en el caso, defina la variable de entorno DATABASE_URL, p. ej.:
#: postgresql+psycopg://usuario:clave@localhost:5432/manaco (requiere ``pip install "psycopg[binary]"``).
DATABASE_URL: str = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")

# --- Reglas de negocio -------------------------------------------------------
#: Diferencia (en pares, en valor absoluto) que todavía se considera "Correcto".
TOLERANCIA_DIFERENCIA: int = 0

ESTADO_CORRECTO = "Correcto"
ESTADO_FALTANTE = "Faltante"
ESTADO_SOBRANTE = "Sobrante"
ESTADOS: tuple[str, ...] = (ESTADO_CORRECTO, ESTADO_FALTANTE, ESTADO_SOBRANTE)

# --- Catálogo ----------------------------------------------------------------
CIUDADES: tuple[str, ...] = (
    "La Paz", "El Alto", "Cochabamba", "Santa Cruz",
    "Sucre", "Tarija", "Oruro", "Potosí",
)
TIPOS_TIENDA: tuple[str, ...] = ("tienda", "almacén")

#: Categoría interna de Manaco → código del Sistema Armonizado (6 dígitos).
CATEGORIAS_SA6: dict[str, int] = {
    "Deportivo": 640411,
    "Caucho y cuero": 640399,
    "Cuero": 640420,
    "Medias": 611595,
}
SA6_A_CATEGORIA: dict[int, str] = {v: k for k, v in CATEGORIAS_SA6.items()}

# --- Usuarios y permisos -----------------------------------------------------
ROL_ADMIN = "administrador"
ROL_ENCARGADO = "encargado"
ROL_GERENCIA = "gerencia"
ROLES: tuple[str, ...] = (ROL_ADMIN, ROL_ENCARGADO, ROL_GERENCIA)

#: Clave de página → roles que pueden verla.
PERMISOS: dict[str, tuple[str, ...]] = {
    "inicio": (ROL_ADMIN, ROL_GERENCIA),
    "apertura": (ROL_ADMIN, ROL_ENCARGADO),
    "ventas": (ROL_ADMIN, ROL_ENCARGADO),
    "cierre": (ROL_ADMIN, ROL_ENCARGADO),
    "historial": (ROL_ADMIN, ROL_GERENCIA),
    "tablero": (ROL_ADMIN, ROL_GERENCIA),
    "pronostico": (ROL_ADMIN, ROL_GERENCIA),
    "escenario": (ROL_ADMIN, ROL_GERENCIA),
    "entregables": (ROL_ADMIN, ROL_GERENCIA),
    "catalogo": (ROL_ADMIN,),
    "usuarios": (ROL_ADMIN,),
    "inventario": (ROL_ADMIN, ROL_ENCARGADO),
    "clientes": (ROL_ADMIN, ROL_GERENCIA),
    "recomendaciones": (ROL_ADMIN, ROL_ENCARGADO, ROL_GERENCIA),
    "marketing": (ROL_ADMIN, ROL_GERENCIA),
    "contabilidad": (ROL_ADMIN, ROL_GERENCIA),
}

ADMIN_USUARIO = "admin"
ADMIN_CONTRASENA = "manaco2026"

# --- Módulo administrativo y de inventarios -----------------------------------
ESTADO_OC_BORRADOR = "BORRADOR"
ESTADO_OC_APROBADA = "APROBADA"
ESTADO_OC_RECIBIDA = "RECIBIDA"
ESTADO_OC_CANCELADA = "CANCELADA"
ESTADOS_OC: tuple[str, ...] = (ESTADO_OC_BORRADOR, ESTADO_OC_APROBADA, ESTADO_OC_RECIBIDA, ESTADO_OC_CANCELADA)

ORIGEN_OC_MANUAL = "MANUAL"
ORIGEN_OC_ALERTA = "ALERTA_STOCK"
ORIGENES_OC: tuple[str, ...] = (ORIGEN_OC_MANUAL, ORIGEN_OC_ALERTA)

# --- Módulo de machine learning: segmentación RFM -----------------------------
SEGMENTO_VIP = "VIP"
SEGMENTO_FRECUENTE = "Frecuentes"
SEGMENTO_RIESGO = "En riesgo"
SEGMENTO_INACTIVO = "Inactivos"
SEGMENTO_NUEVO = "Nuevos"
SEGMENTOS_RFM: tuple[str, ...] = (
    SEGMENTO_VIP, SEGMENTO_FRECUENTE, SEGMENTO_RIESGO, SEGMENTO_INACTIVO, SEGMENTO_NUEVO,
)

#: Mínimo de ventas históricas por producto para confiar en Apriori/FP-Growth;
#: por debajo de esto se usa el respaldo por atributos (categoría, color, talla).
MINIMO_VENTAS_ASOCIACION: int = 20
SOPORTE_MINIMO_ASOCIACION: float = 0.01
CONFIANZA_MINIMA_ASOCIACION: float = 0.1

# --- Módulo de marketing digital y promociones --------------------------------
TIPO_PROMO_PORCENTAJE = "PORCENTAJE"
TIPO_PROMO_MONTO_FIJO = "MONTO_FIJO"
TIPO_PROMO_COMBO = "COMBO_ESPECIAL"
TIPOS_PROMOCION: tuple[str, ...] = (TIPO_PROMO_PORCENTAJE, TIPO_PROMO_MONTO_FIJO, TIPO_PROMO_COMBO)

CANALES_CAMPANA: tuple[str, ...] = ("TikTok", "Instagram", "Facebook", "Google")

# --- Contabilidad: plan de cuentas mínimo usado por las integraciones ---------
CUENTA_INVENTARIO = "1141"
CUENTA_CXP_PROVEEDORES = "2111"
CUENTA_DESCUENTOS_VENTA = "4121"
CUENTA_CAJA_BANCOS = "1111"

#: (código, nombre, tipo, naturaleza) — se siembra una sola vez en ``contabilidad.sembrar_plan_cuentas``.
PLAN_CUENTAS_BASE: tuple[tuple[str, str, str, str], ...] = (
    (CUENTA_CAJA_BANCOS, "Caja y bancos", "ACTIVO", "DEUDORA"),
    (CUENTA_INVENTARIO, "Inventario de mercaderías", "ACTIVO", "DEUDORA"),
    (CUENTA_CXP_PROVEEDORES, "Cuentas por pagar proveedores", "PASIVO", "ACREEDORA"),
    (CUENTA_DESCUENTOS_VENTA, "Descuentos sobre ventas", "INGRESO", "DEUDORA"),
)

# --- Visión por computadora --------------------------------------------------
MODELO_YOLO: str = "yolov8s-world.pt"
CLASES_YOLO: list[str] = ["shoe", "shoe box"]
UMBRAL_CONFIANZA: float = 0.25

# --- ETL ---------------------------------------------------------------------
COLUMNAS_EXCEL: tuple[str, ...] = (
    "País_reportante", "Flujo_comercial", "Año", "Código_SA6", "Categoría_calzado",
    "Socio_comercial", "Valor_miles_USD", "Cantidad_pares", "Valor_USD", "Valor_USD_por_par",
)
CLAVE_REGISTRO: list[str] = ["Flujo_comercial", "Año", "Código_SA6", "Socio_comercial"]
TOLERANCIA_CONSISTENCIA: float = 0.01

# --- Estilo ------------------------------------------------------------------
COLOR_ACENTO = "#B3261E"
COLOR_GRIS = "#A8A29E"
COLOR_GRIS_OSCURO = "#57534E"
COLOR_EXITO = "#2E7D32"
COLOR_ADVERTENCIA = "#E67E22"
