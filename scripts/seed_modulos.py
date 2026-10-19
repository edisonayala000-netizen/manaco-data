"""Carga datos de demostración para los módulos de Inventario, ML y Marketing.

Es idempotente y se ejecuta *después* de ``seed_demo.py``: no borra ventas ni
catálogo, solo agrega proveedores, inventario con punto de reorden, clientes
(vinculados a ventas existentes para que RFM y ROAS tengan datos reales),
reglas de promoción y campañas de marketing digital.
Uso: ``python scripts/seed_modulos.py``
"""

from __future__ import annotations

import random
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import select  # noqa: E402

from src.config import TIPO_PROMO_COMBO, TIPO_PROMO_MONTO_FIJO, TIPO_PROMO_PORCENTAJE  # noqa: E402
from src.db import crear_tablas, obtener_sesion  # noqa: E402
from src.models import Cliente, Producto, Tienda, Venta  # noqa: E402
from src.services import compras, contabilidad, promociones, rfm  # noqa: E402

SEMILLA = 2026

PROVEEDORES = [
    ("Calzados del Sur S.R.L.", "Calzados del Sur Sociedad de Responsabilidad Limitada", "1023456019", "70011122",
     "ventas@calzadosdelsur.bo"),
    ("Importadora Andina", "Importadora Andina S.A.", "1045678021", "70022233", "contacto@andina.bo"),
    ("Cueros Illimani", "Cueros Illimani Ltda.", "1067890033", "70033344", "pedidos@cuerosillimani.bo"),
]

CLIENTES = [
    ("María Pérez", "4521367 LP", "71234567", "maria.perez@example.com", "La Paz"),
    ("Juan Condori", "6789012 CB", "71234568", "juan.condori@example.com", "Cochabamba"),
    ("Ana Rojas", "8912345 SC", "71234569", "ana.rojas@example.com", "Santa Cruz"),
    ("Carlos Mamani", "3456789 LP", "71234570", "carlos.mamani@example.com", "La Paz"),
    ("Lucía Fernández", "5678901 CB", "71234571", "lucia.fernandez@example.com", "Cochabamba"),
    ("Pedro Quispe", "7890123 SC", "71234572", "pedro.quispe@example.com", "Santa Cruz"),
    ("Daniela Choque", "2345678 LP", "71234573", "daniela.choque@example.com", "El Alto"),
    ("Rodrigo Flores", "9012345 CB", "71234574", "rodrigo.flores@example.com", "Cochabamba"),
    ("Valeria Gutiérrez", "1234567 SC", "71234575", "valeria.gutierrez@example.com", "Santa Cruz"),
    ("Javier Torrez", "6543210 LP", "71234576", "javier.torrez@example.com", "La Paz"),
    ("Sofía Vargas", "4321098 OR", "71234577", "sofia.vargas@example.com", "Oruro"),
    ("Miguel Aguilar", "8765432 PT", "71234578", "miguel.aguilar@example.com", "Potosí"),
]


def _sembrar_proveedores(s) -> list[int]:  # noqa: ANN001
    existentes = {p.nombre: p.id for p in s.scalars(select(compras.Proveedor)).all()}
    ids = []
    for nombre, razon_social, nit, telefono, email in PROVEEDORES:
        if nombre in existentes:
            ids.append(existentes[nombre])
            continue
        proveedor = compras.crear_proveedor(s, nombre, razon_social=razon_social, nit=nit, telefono=telefono,
                                            email=email)
        ids.append(proveedor.id)
    return ids


def _sembrar_inventario(s, proveedor_ids: list[int], rnd: random.Random) -> int:  # noqa: ANN001
    tiendas = s.scalars(select(Tienda)).all()
    productos = s.scalars(select(Producto)).all()
    alertas_generadas = 0
    for tienda in tiendas:
        for producto in productos:
            punto_reorden = rnd.randint(8, 15)
            stock_minimo = max(3, punto_reorden // 2)
            # ~1 de cada 4 filas nace bajo su punto de reorden, para mostrar alertas reales.
            bajo_reorden = rnd.random() < 0.25
            stock_inicial = rnd.randint(0, punto_reorden - 1) if bajo_reorden else rnd.randint(punto_reorden + 5,
                                                                                                punto_reorden + 40)
            proveedor_id = rnd.choice(proveedor_ids)
            registro = compras.obtener_o_crear_inventario(
                s, producto.id, tienda.id, stock_inicial, stock_minimo, punto_reorden, proveedor_id)
            if registro.stock_actual <= registro.punto_reorden:
                if compras.evaluar_alerta_stock(s, registro) is not None:
                    alertas_generadas += 1
    return alertas_generadas


def _sembrar_clientes(s) -> list[int]:  # noqa: ANN001
    existentes = {c.documento: c.id for c in s.scalars(select(Cliente)).all()}
    ids = []
    for nombre, documento, telefono, email, ciudad in CLIENTES:
        if documento in existentes:
            ids.append(existentes[documento])
            continue
        cliente = Cliente(nombre=nombre, documento=documento, telefono=telefono, email=email, ciudad=ciudad)
        s.add(cliente)
        s.flush()
        ids.append(cliente.id)
    return ids


def _vincular_ventas_a_clientes(s, cliente_ids: list[int], rnd: random.Random) -> int:  # noqa: ANN001
    """Asigna un cliente a las ventas que todavía no tienen uno, para que RFM tenga datos reales."""
    sin_cliente = s.scalars(select(Venta).where(Venta.cliente_id.is_(None))).all()
    for venta in sin_cliente:
        venta.cliente_id = rnd.choice(cliente_ids)
    s.flush()
    return len(sin_cliente)


def _sembrar_promociones(s) -> int:  # noqa: ANN001
    existentes = {r.nombre for r in s.scalars(select(promociones.ReglaPromocion)).all()}
    primera_venta = s.scalars(select(Venta.fecha).order_by(Venta.fecha)).first()
    inicio = primera_venta or date.today()
    creadas = 0

    def _crear(nombre: str, **kwargs) -> None:  # noqa: ANN003
        nonlocal creadas
        if nombre in existentes:
            return
        promociones.crear_regla_promocion(s, nombre, fecha_inicio=inicio, **kwargs)
        creadas += 1

    _crear("Descuento Deportivo 15%", tipo=TIPO_PROMO_PORCENTAJE, valor=15.0, categoria="Deportivo")
    _crear("Rebaja fija Cuero 50 Bs", tipo=TIPO_PROMO_MONTO_FIJO, valor=50.0, categoria="Cuero",
          cantidad_necesaria=2)
    _crear("Combo 3x2 Caucho y cuero", tipo=TIPO_PROMO_COMBO, categoria="Caucho y cuero",
          cantidad_necesaria=3, cantidad_gratis=1)
    _crear("Combo 3x2 Medias", tipo=TIPO_PROMO_COMBO, categoria="Medias",
          cantidad_necesaria=3, cantidad_gratis=1)
    _crear("Descuento Medias 20%", tipo=TIPO_PROMO_PORCENTAJE, valor=20.0, categoria="Medias")
    return creadas


def _sembrar_campanas(s) -> list[int]:  # noqa: ANN001
    existentes = {c.codigo_cupon: c.id for c in s.scalars(select(promociones.CampanaMarketing)).all()}
    primera_venta = s.scalars(select(Venta.fecha).order_by(Venta.fecha)).first()
    inicio = primera_venta or date.today()
    datos = [
        ("Rebaja de invierno TikTok", "TikTok", "INVIERNO20", "tiktok", "invierno_2026", "social", 2000.0),
        ("Lanzamiento Instagram Verano", "Instagram", "VERANO15", "instagram", "verano_2026", "social", 1500.0),
    ]
    ids = []
    for nombre, canal, cupon, utm_source, utm_campaign, utm_medium, presupuesto in datos:
        if cupon in existentes:
            ids.append(existentes[cupon])
            continue
        campana = promociones.crear_campana(s, nombre, canal, cupon, utm_source, utm_campaign, inicio,
                                            utm_medium=utm_medium, presupuesto_bs=presupuesto)
        ids.append(campana.id)
    return ids


def _sembrar_conversiones(s, campana_ids: list[int], rnd: random.Random) -> int:  # noqa: ANN001
    ya_registradas = {c.venta_id for c in s.scalars(select(promociones.ConversionCampana)).all()}
    candidatas = s.scalars(
        select(Venta).where(Venta.cliente_id.is_not(None)).order_by(Venta.fecha.desc()).limit(40)
    ).all()
    candidatas = [v for v in candidatas if v.id not in ya_registradas]
    rnd.shuffle(candidatas)
    creadas = 0
    for venta in candidatas[:12]:
        campana_id = rnd.choice(campana_ids)
        monto = round(venta.cantidad * venta.precio_unitario_bs, 2)
        promociones.registrar_conversion(s, campana_id, monto, venta.fecha, venta_id=venta.id,
                                         cliente_id=venta.cliente_id)
        creadas += 1
    return creadas


def main() -> None:
    rnd = random.Random(SEMILLA)
    crear_tablas()
    with obtener_sesion() as s:
        contabilidad.sembrar_plan_cuentas(s)
        proveedor_ids = _sembrar_proveedores(s)
        alertas = _sembrar_inventario(s, proveedor_ids, rnd)
        cliente_ids = _sembrar_clientes(s)
        vinculadas = _vincular_ventas_a_clientes(s, cliente_ids, rnd)
        rfm.actualizar_perfiles_rfm(s)
        reglas_creadas = _sembrar_promociones(s)
        campana_ids = _sembrar_campanas(s)
        conversiones = _sembrar_conversiones(s, campana_ids, rnd)

    print(f"✔ Módulos cargados: {len(PROVEEDORES)} proveedores, inventario con {alertas} alerta(s) de stock crítico.")
    print(f"  {len(CLIENTES)} clientes, {vinculadas} venta(s) vinculada(s) para RFM.")
    print(f"  {reglas_creadas} regla(s) de promoción nueva(s), {len(campana_ids)} campaña(s), "
          f"{conversiones} conversión(es) registrada(s).")
    print("  Plan de cuentas sembrado. Revise Inventario y compras, Clientes y segmentación, "
          "Recomendaciones, Marketing y promociones, y Contabilidad.")


if __name__ == "__main__":
    main()
