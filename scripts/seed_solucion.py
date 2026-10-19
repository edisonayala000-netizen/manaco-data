"""Carga datos [Simulado] del esquema en estrella que falta: calendario, producción,
calidad, mercado local y bitácora de ingesta (Manaco_Caso_Solucion_y_Prototipo.md, sec. 2-3).

No hay 24 meses de historia real en el sistema (sólo ``DIAS = 90`` en seed_demo.py), así que
estas tablas se llenan con datos simulados y etiquetados como tales, igual que el prototipo
publicado en la sección 4 del documento. Reemplaza el contenido de las 5 tablas.
Uso: ``python scripts/seed_solucion.py`` (requiere haber corrido antes seed_demo.py).
"""

from __future__ import annotations

import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # símbolos ✔ en consolas Windows

from sqlalchemy import delete, select  # noqa: E402

from src.db import crear_tablas, obtener_sesion  # noqa: E402
from src.models import (  # noqa: E402
    DimFecha, FactCalidad, FactProduccion, LogIngesta, Producto, RefMercadoLocal,
)
from src.services.pronostico import NIVEL_BASE  # noqa: E402

MESES_HISTORIA = 24
SEMILLA = 2026

#: Feriados bolivianos de fecha fija (se omiten los movibles: Carnaval, Corpus Christi).
FERIADOS_FIJOS = {(1, 1), (1, 22), (5, 1), (8, 6), (11, 2), (12, 25)}

#: (ciudad, nombre del mercado) usados como referencia de precio informal/competencia.
MERCADOS = [
    ("La Paz", "Mercado Eloy Salmón"),
    ("Cochabamba", "La Cancha"),
    ("Santa Cruz", "La Ramada"),
]

SUCURSALES_LOG = [
    "Tienda Prado", "Tienda Heroínas", "Tienda Ventura",
    "Almacén La Paz", "Almacén Cochabamba", "Almacén Santa Cruz",
]

MOTIVOS_CALIDAD = ["Costura defectuosa", "Pegado de suela", "Talla incorrecta", "Mancha de material"]


def _mes_siguiente(d: date) -> date:
    return date(d.year + (d.month == 12), d.month % 12 + 1, 1)


def _poblar_dim_fecha(s, inicio: date, fin: date) -> int:  # noqa: ANN001
    s.execute(delete(DimFecha))
    filas = []
    dia = inicio
    while dia <= fin:
        filas.append(DimFecha(
            fecha=dia, anio=dia.year, mes=dia.month,
            inicio_clases=dia.month == 2,
            feriado=(dia.month, dia.day) in FERIADOS_FIJOS,
        ))
        dia += timedelta(days=1)
    s.add_all(filas)
    return len(filas)


def _poblar_produccion_y_calidad(
    s, rnd: random.Random, inicio: date, fin: date, productos: list[Producto],
) -> tuple[int, int]:  # noqa: ANN001
    s.execute(delete(FactCalidad))
    s.execute(delete(FactProduccion))
    produccion, calidad = [], []
    mes, n_lote = date(inicio.year, inicio.month, 1), 0
    por_linea = {cat: sum(1 for p in productos if p.categoria == cat) for cat in {p.categoria for p in productos}}
    while mes <= fin:
        for p in productos:
            n_lote += 1
            # Supuesto: cada línea produce cerca de su demanda base mensual (±15%), repartida entre sus
            # productos, para que la cobertura de producción del Prototipo de escenario sea comparable.
            base = NIVEL_BASE.get(p.categoria, 600) / por_linea[p.categoria]
            pares = max(20, round(base * rnd.uniform(0.85, 1.15)))
            lote = f"L{mes:%Y%m}-{n_lote:04d}"
            # Supuesto: el costo unitario (Producto.costo_bs) se reparte ~65% insumos / ~35% mano de obra.
            produccion.append(FactProduccion(
                fecha=mes, lote=lote, producto_id=p.id, pares=pares,
                costo_insumos_bs=round(pares * p.costo_bs * 0.65, 2),
                costo_mano_obra_bs=round(pares * p.costo_bs * 0.35, 2),
            ))
            defectos = round(pares * rnd.uniform(0.01, 0.05))
            if defectos:
                calidad.append(FactCalidad(
                    fecha=mes, lote=lote, producto_id=p.id,
                    defectos=defectos, devoluciones=round(defectos * rnd.uniform(0.2, 0.5)),
                    motivo=rnd.choice(MOTIVOS_CALIDAD),
                ))
        mes = _mes_siguiente(mes)
    s.add_all(produccion)
    s.add_all(calidad)
    return len(produccion), len(calidad)


def _poblar_mercado_local(s, rnd: random.Random, inicio: date, fin: date, productos: list[Producto]) -> int:  # noqa: ANN001
    s.execute(delete(RefMercadoLocal))
    precio_ref = sum(p.precio_venta_bs for p in productos) / len(productos)
    filas = []
    dia, tipo_cambio = inicio, 6.96
    while dia <= fin:
        # Supuesto: el tipo de cambio paralelo se modela como una caminata aleatoria lenta y creciente,
        # reflejando la escasez de dólares descrita en el caso (no es un dato oficial).
        tipo_cambio = max(6.96, tipo_cambio + rnd.uniform(-0.02, 0.06))
        for ciudad, mercado in MERCADOS:
            descuento_informal = rnd.uniform(0.80, 0.95)  # el mercado informal suele vender más barato
            filas.append(RefMercadoLocal(
                fecha=dia, ciudad=ciudad, mercado=mercado,
                precio_competidor_bs=round(precio_ref * descuento_informal * rnd.uniform(0.95, 1.05), 2),
                tipo_cambio_paralelo=round(tipo_cambio, 2),
            ))
        dia += timedelta(days=7)
    s.add_all(filas)
    return len(filas)


def _poblar_log_ingesta(s, rnd: random.Random, inicio: date, fin: date) -> int:  # noqa: ANN001
    s.execute(delete(LogIngesta))
    filas = []
    mes = date(inicio.year, inicio.month, 1)
    while mes <= fin:
        for sucursal in SUCURSALES_LOG:
            leidas = rnd.randint(150, 400)
            filas.append(LogIngesta(
                fecha=mes, sucursal=sucursal, archivo=f"{sucursal.lower().replace(' ', '_')}_{mes:%Y%m}.csv",
                filas_leidas=leidas,
                filas_corregidas=round(leidas * rnd.uniform(0.0, 0.08)),
                filas_rechazadas=round(leidas * rnd.uniform(0.0, 0.03)),
            ))
        mes = _mes_siguiente(mes)
    s.add_all(filas)
    return len(filas)


def main() -> None:
    """Genera 24 meses de historia simulada para el esquema en estrella."""
    rnd = random.Random(SEMILLA)
    crear_tablas()
    fin = date.today() - timedelta(days=1)
    inicio = fin - timedelta(days=30 * MESES_HISTORIA)

    with obtener_sesion() as s:
        productos = list(s.scalars(select(Producto)))
        if not productos:
            print("⚠ No hay productos; corra primero scripts/seed_demo.py.")
            return

        n_fechas = _poblar_dim_fecha(s, inicio, fin)
        n_prod, n_cal = _poblar_produccion_y_calidad(s, rnd, inicio, fin, productos)
        n_mercado = _poblar_mercado_local(s, rnd, inicio, fin, productos)
        n_log = _poblar_log_ingesta(s, rnd, inicio, fin)

    print(f"✔ Esquema en estrella [Simulado] cargado ({inicio:%m/%Y} a {fin:%m/%Y}):")
    print(f"  dim_fecha: {n_fechas} días · fact_produccion: {n_prod} lotes · fact_calidad: {n_cal} incidencias")
    print(f"  ref_mercado_local: {n_mercado} registros · log_ingesta: {n_log} registros")
    print("  Estos datos son simulados y están etiquetados como [Simulado] en las páginas que los usan;")
    print("  no provienen de ventas/producción reales de Manaco.")


if __name__ == "__main__":
    main()
