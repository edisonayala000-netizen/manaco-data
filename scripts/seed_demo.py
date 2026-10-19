"""Carga datos de demostración: 3 tiendas, 16 productos y 90 días (3 meses) de operación.

Reemplaza tiendas, productos, aperturas, ventas y cierres existentes.
Uso: ``python scripts/seed_demo.py``
"""

from __future__ import annotations

import random
import sys
from datetime import date, time, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # símbolos ✔ en consolas Windows

from sqlalchemy import delete, select  # noqa: E402

from src.auth import crear_usuario  # noqa: E402
from src.config import CATEGORIAS_SA6, ESTADO_CORRECTO, ROL_ENCARGADO, ROL_GERENCIA  # noqa: E402
from src.db import crear_tablas, obtener_sesion  # noqa: E402
from src.models import (  # noqa: E402
    AlertaStock, AnulacionCierre, Apertura, Cierre, ConversionCampana, DetalleOrdenCompra, FactCalidad,
    FactProduccion, Inventario, OrdenCompra, Producto, RecomendacionLog, Tienda, Usuario, Venta,
)
from src.services import inventario as inv  # noqa: E402

DIAS = 90
SEMILLA = 2026

TIENDAS = [
    ("Tienda Prado", "La Paz", "tienda"),
    ("Tienda Heroínas", "Cochabamba", "tienda"),
    ("Tienda Ventura", "Santa Cruz", "tienda"),
]

# código, nombre, categoría, talla, color, precio Bs, costo Bs
PRODUCTOS = [
    ("MAN-DEP-001", "Zapatilla Runner Pro", "Deportivo", "40", "Negro", 389, 215),
    ("MAN-DEP-002", "Zapatilla Urbana Flex", "Deportivo", "38", "Blanco", 329, 180),
    ("MAN-DEP-003", "Zapatilla Escolar Sport", "Deportivo", "35", "Azul", 249, 135),
    ("MAN-DEP-004", "Zapatilla Trail Andes", "Deportivo", "42", "Gris", 459, 260),
    ("MAN-CYC-001", "Botín Escolar Clásico", "Caucho y cuero", "36", "Negro", 279, 150),
    ("MAN-CYC-002", "Zapato Casual Illimani", "Caucho y cuero", "41", "Café", 349, 190),
    ("MAN-CYC-003", "Bota de Trabajo Minera", "Caucho y cuero", "42", "Negro", 429, 245),
    ("MAN-CYC-004", "Mocasín Confort", "Caucho y cuero", "39", "Marrón", 299, 165),
    ("MAN-CUE-001", "Zapato de Vestir Ejecutivo", "Cuero", "41", "Negro", 529, 295),
    ("MAN-CUE-002", "Zapato Oxford Elegance", "Cuero", "40", "Café", 579, 320),
    ("MAN-CUE-003", "Ballerina Cuero Dama", "Cuero", "37", "Rojo", 399, 210),
    ("MAN-CUE-004", "Botín Chelsea Cuero", "Cuero", "39", "Negro", 619, 345),
    ("MAN-MED-001", "Media Deportiva Running", "Medias", "35-38", "Negro", 39, 18),
    ("MAN-MED-002", "Media Deportiva Running", "Medias", "39-42", "Blanco", 39, 18),
    ("MAN-MED-003", "Media Casual Algodón", "Medias", "35-38", "Gris", 29, 12),
    ("MAN-MED-004", "Media Casual Algodón", "Medias", "39-42", "Café", 29, 12),
]

OBSERVACIONES_FALTANTE = ["Posible venta no registrada", "Par extraviado en vitrina", "Revisar cámara de seguridad"]
OBSERVACIONES_SOBRANTE = ["Devolución no registrada", "Traspaso recibido sin registrar"]


def _usuario_demo(sesion, usuario: str, nombre: str, rol: str) -> int:  # noqa: ANN001
    existente = sesion.scalar(select(Usuario).where(Usuario.usuario == usuario))
    if existente:
        return existente.id
    return crear_usuario(sesion, nombre, usuario, "manaco2026", rol).id


def main() -> None:
    """Genera la operación simulada de los últimos 90 días / 3 meses (hasta ayer)."""
    rnd = random.Random(SEMILLA)
    crear_tablas()
    hoy = date.today()
    inicio = hoy - timedelta(days=DIAS)

    with obtener_sesion() as s:
        # Las tablas de seed_modulos.py (inventario, alertas, órdenes, conversiones) referencian
        # productos/tiendas/ventas: hay que limpiarlas primero para poder re-sembrar desde cero.
        for modelo in (
            ConversionCampana, RecomendacionLog, AlertaStock, DetalleOrdenCompra, OrdenCompra, Inventario,
            Venta, Cierre, Apertura, AnulacionCierre, FactCalidad, FactProduccion, Producto, Tienda,
        ):
            s.execute(delete(modelo))
        encargado_id = _usuario_demo(s, "encargado", "Encargado de Tienda", ROL_ENCARGADO)
        _usuario_demo(s, "gerencia", "Gerencia Comercial", ROL_GERENCIA)

        tiendas = [Tienda(nombre=n, ciudad=c, tipo=t) for n, c, t in TIENDAS]
        productos = [
            Producto(codigo_modelo=cod, nombre=nom, categoria=cat, codigo_sa6=CATEGORIAS_SA6[cat],
                     talla=talla, color=color, precio_venta_bs=precio, costo_bs=costo)
            for cod, nom, cat, talla, color, precio, costo in PRODUCTOS
        ]
        s.add_all(tiendas + productos)
        s.flush()

        # Popularidad relativa por producto y tamaño relativo por tienda.
        demanda = {p.id: rnd.uniform(1.0, 4.5) for p in productos}
        escala = {t.id: f for t, f in zip(tiendas, (1.3, 1.0, 1.15))}
        stock = {(t.id, p.id): rnd.randint(30, 60) for t in tiendas for p in productos}
        alertas = 0

        for d in range(DIAS):
            dia = inicio + timedelta(days=d)
            fin_de_semana = dia.weekday() >= 5
            for t in tiendas:
                for p in productos:
                    saldo = stock[(t.id, p.id)]
                    if saldo < 15:  # reposición desde el almacén
                        saldo += rnd.randint(24, 36)
                    inv.registrar_apertura(s, dia, t.id, p.id, saldo, encargado_id)

                    media = demanda[p.id] * escala[t.id] * (1.4 if fin_de_semana else 1.0)
                    por_vender = min(saldo, max(0, round(rnd.gauss(media, 1.3))))
                    while por_vender > 0:
                        cantidad = min(por_vender, rnd.choice((1, 1, 1, 2)))
                        hora = time(rnd.randint(9, 20), rnd.randint(0, 59))
                        descuento = rnd.choice((1.0, 1.0, 1.0, 0.9))
                        inv.registrar_venta(s, dia, t.id, p.id, cantidad, round(p.precio_venta_bs * descuento, 2),
                                            encargado_id, hora)
                        por_vender -= cantidad

                    esperado = inv.resumen_dia(s, dia, t.id, p.id).saldo_esperado
                    azar = rnd.random()
                    if azar < 0.05 and esperado >= 2:
                        conteo, obs = esperado - rnd.choice((1, 2)), rnd.choice(OBSERVACIONES_FALTANTE)
                    elif azar < 0.07:
                        conteo, obs = esperado + 1, rnd.choice(OBSERVACIONES_SOBRANTE)
                    else:
                        conteo, obs = esperado, ""
                    cierre = inv.registrar_cierre(s, dia, t.id, p.id, conteo, encargado_id, observacion=obs)
                    # Las alertas antiguas ya se revisaron; quedan pendientes las de la última semana.
                    if cierre.estado != ESTADO_CORRECTO:
                        alertas += 1
                        cierre.alerta_atendida = (hoy - dia).days > 7
                    stock[(t.id, p.id)] = conteo

        n_ventas = s.query(Venta).count()
        pendientes = len(inv.alertas_pendientes(s))

    print(f"✔ Demo cargada: {len(TIENDAS)} tiendas, {len(PRODUCTOS)} productos, {DIAS} días "
          f"({inicio:%d/%m/%Y} al {hoy - timedelta(days=1):%d/%m/%Y}).")
    print(f"  {n_ventas} ventas, {DIAS * len(TIENDAS) * len(PRODUCTOS)} cierres, "
          f"{alertas} con diferencia ({pendientes} alertas pendientes).")
    print("  Usuarios demo: encargado / manaco2026 · gerencia / manaco2026")
    print("  Hoy queda libre para hacer la demo en vivo: apertura → venta → foto → cierre.")
    print("⚠ Este script borró los datos [Simulado] de producción y calidad. Ejecute ahora")
    print("  python scripts/seed_solucion.py para que el Prototipo de escenario tenga datos.")


if __name__ == "__main__":
    main()
