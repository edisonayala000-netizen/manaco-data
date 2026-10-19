# Manaco Data

Plataforma web **local** para la empresa boliviana de calzado **Manaco**. Resuelve estos problemas del caso de estudio:

1. **Inventario sin control diario.** Registra la apertura, las ventas y el cierre de stock de pares de zapatos en cada tienda, cuenta el stock con una **foto** (IA YOLO-World) y **alerta** cuando lo contado no coincide con lo esperado.
2. **Compras y reposición sin punto de reorden.** Un stock administrativo paralelo (`Inventario`) dispara alertas y, si hay proveedor predeterminado, una orden de compra automática; al recibirla se prorratea el flete/arancel en el costo (*landed cost*) y se registra el asiento contable.
3. **Datos sin integrar.** Un **tablero de mercado** analiza la base de comercio exterior de calzado (Excel) junto con las ventas internas registradas en el sistema.
4. **Venta cruzada y segmentación manuales.** Un motor de recomendación (reglas de asociación FP-Growth/Apriori con respaldo por atributos) sugiere productos complementarios, y la segmentación RFM clasifica clientes en VIP, Frecuentes, En riesgo, Inactivos o Nuevos.
5. **Promociones y campañas sin trazabilidad.** Reglas de descuento (porcentaje, monto fijo, combo) se evalúan sobre el carrito; las campañas con cupón y UTM registran conversiones y su ROAS, con el descuento reflejado en el libro diario.

Un **libro diario de partida doble** (`src/services/contabilidad.py`) registra automáticamente las compras recibidas y los descuentos por promoción, y expone un balance de comprobación.

Tecnología: Python 3.11 · Streamlit · SQLite + SQLAlchemy 2 · pandas · Plotly · Ultralytics YOLO-World · mlxtend (FP-Growth/Apriori) · bcrypt · pytest.

---

## Instalación con Anaconda

Abra **Anaconda Prompt** (o PowerShell con `conda init powershell` ya ejecutado) en la carpeta del proyecto:

```bash
conda env create -f environment.yml
conda activate manaco
python scripts/init_db.py      # crea las tablas, carga el Excel y el usuario admin
python scripts/seed_demo.py    # (opcional) 3 tiendas, 12 productos y 30 días de operación
python scripts/seed_solucion.py  # (opcional) 24 meses [Simulado] para Pronóstico y Prototipo; siempre después de seed_demo
python scripts/seed_modulos.py   # (opcional) proveedores, inventario con alertas, clientes, promociones y campañas; después de seed_demo
streamlit run app.py
```

Se abre en el navegador en `http://localhost:8501`. Para usarlo desde el celular (tomar la foto), conéctelo a la misma red Wi-Fi y abra la dirección *Network URL* que muestra Streamlit.

> La primera vez que se usa el conteo por foto se descargan el modelo `yolov8s-world.pt` (~25 MB) y el modelo de texto CLIP (~340 MB) en `data/modelos/` (en esta computadora ya están descargados). Se necesita internet solo esa vez. Si no hay conexión, el sistema sigue funcionando con el conteo manual.

### Usuarios de prueba

| Usuario | Contraseña | Rol |
| --- | --- | --- |
| `admin` | `manaco2026` | administrador (ve todo) |
| `encargado` | `manaco2026` | encargado (apertura, ventas, cierre) — lo crea `seed_demo.py` |
| `gerencia` | `manaco2026` | gerencia (inicio, historial, tablero) — lo crea `seed_demo.py` |

⚠️ **Cambie estas contraseñas** en la página *Usuarios* antes de usar el sistema con datos reales.

---

## Páginas

| Página | Rol | Qué hace |
| --- | --- | --- |
| **Inicio** | admin, gerencia | Cuatro KPI del día (pares en apertura, vendidos, cierres hechos/pendientes, alertas activas), la lista de alertas pendientes y el gráfico de diferencias de los últimos 30 días. |
| **Apertura** | admin, encargado | Registra el saldo inicial por fecha, tienda y producto. Propone el conteo del cierre de ayer. Permite abrir todos los productos de una tienda a la vez. |
| **Ventas** | admin, encargado | Formulario rápido de venta, tabla de ventas del día y stock disponible en tiempo real (saldo inicial − vendido). |
| **Cierre y conteo** | admin, encargado | Muestra inicial, vendido y esperado; recibe la foto (cámara o archivo), cuenta con IA, permite corregir a mano y guarda el cierre con su alerta de color. |
| **Historial** | admin, gerencia | Planilla de cierres con filtros y colores por estado; permite ver la foto de evidencia y descargar un **Excel** con formato y hoja de resumen. |
| **Tablero de mercado** | admin, gerencia | KPI y 3 gráficos del comercio exterior limpio (240 registros válidos), filtros, selector de métrica, limitaciones de los datos, diccionario de datos, descarga de la tabla depurada en Excel y la pestaña *Datos internos*. |
| **Catálogo** | admin | Alta, edición y baja (desactivación) de productos y tiendas. |
| **Usuarios** | admin | Alta de usuarios, roles, desactivación y cambio de contraseña. |
| **Pronóstico de demanda** | admin, gerencia | Pronóstico mensual por línea, con y sin ajuste por mercado informal, y su error (MAPE) en un backtest. Datos **[Simulado]**. |
| **Prototipo de escenario** | admin, gerencia | Controles de tipo de cambio paralelo y presión informal que mueven 5 indicadores frente a metas **[Supuesto]**. Necesita `seed_solucion.py`. |
| **Entregables escritos** | admin, gerencia | Los 4 textos del caso: problemas prioritarios, síntesis ejecutiva, ficha de propuesta y recomendación ejecutiva. |
| **Inventario y compras** | admin, encargado | Proveedores, stock con punto de reorden y alertas, órdenes de compra (borrador → aprobada → recibida) con prorrateo de flete/arancel. |
| **Clientes y segmentación** | admin, gerencia | Alta de clientes y tabla de segmentos RFM (Recencia, Frecuencia, Monto) con recálculo manual. |
| **Recomendaciones** | admin, encargado, gerencia | Top-3 de venta cruzada por producto (reglas de asociación o respaldo por atributos), registro de aceptación y tasa de conversión. |
| **Marketing y promociones** | admin, gerencia | Reglas de descuento (porcentaje, monto fijo, combo), campañas con cupón/UTM y su ROAS, y un simulador de carrito. |
| **Contabilidad** | admin, gerencia | Libro diario y balance de comprobación generados automáticamente por compras y descuentos. |

### Reglas de inventario

- **Saldo esperado** = saldo inicial − total vendido del día.
- **Diferencia** = conteo final − saldo esperado → `Correcto` (0 o dentro de la tolerancia), `Faltante` (negativa) o `Sobrante` (positiva).
- No hay ventas sin apertura, ni ventas que superen el stock, ni cierres sin apertura.
- Un cierre guardado no se repite; solo el administrador lo anula, indicando un motivo (queda en `anulaciones_cierre`).
- La tolerancia se ajusta en `src/config.py` (`TOLERANCIA_DIFERENCIA`, por defecto 0).

Ejemplo: apertura 50, ventas 12 → esperado 38; conteo 36 → diferencia −2 → **"Faltan 2 pares de MAN-DEP-001 en Tienda Prado (esperado 38, contado 36)"**.

### Compras, recomendación, RFM y promociones

- **Reorden automático.** Cuando el stock administrativo baja al punto de reorden (`compras.evaluar_alerta_stock`), se crea una alerta y, si el producto tiene proveedor predeterminado, una orden de compra en borrador por el doble del punto de reorden.
- **Costo de reposición (*landed cost*).** Al recibir una orden (`compras.recibir_orden_compra`) el flete y el arancel se prorratean entre las líneas según su peso en el subtotal, se actualiza `Producto.costo_bs` y se registra el asiento Debe Inventario / Haber Cuentas por pagar.
- **Recomendación.** `recomendacion.recomendar` agrupa las ventas en "cestas" (fecha, tienda, cliente) y aplica FP-Growth/Apriori; si un producto no tiene al menos `MINIMO_VENTAS_ASOCIACION` cestas o ninguna regla lo cubre, recomienda por atributos (misma categoría y, si alcanza, mismo color), ordenado por popularidad.
- **RFM.** `rfm.calcular_rfm` puntúa Recencia, Frecuencia y Monto en una escala 1–5 por quintiles y clasifica el segmento: Nuevos (una compra reciente), VIP (R, F y M altos), En riesgo (compraba seguido, ya no), Inactivos (ni uno ni lo otro) o Frecuentes.
- **Promociones.** `promociones.evaluar_carrito` aplica, sobre las reglas vigentes en la fecha, descuentos por porcentaje, monto fijo (con cantidad mínima) o combo (regala las unidades más baratas del grupo). Un cupón de campaña habilita además sus reglas exclusivas.
- **Campañas.** Cada conversión con cupón genera su enlace UTM y, si hubo descuento, el asiento Debe Descuentos sobre ventas / Haber Caja y bancos; el ROAS es el monto generado sobre el presupuesto.

### Limpieza del Excel

`src/services/etl.py` aplica y registra en `bitacora_limpieza`:
1. Validación de tipos y faltantes (0 faltantes).
2. Separación de registros con socio "Mundo" (0 en la base actual).
3. Claves repetidas (Flujo, Año, Código SA6, Socio): 20 filas comparten clave con valores distintos; se marcan y se conservan para validarlas con la fuente → **240 → 240 válidas, 0 descartadas**.
4. Consistencia `Valor_USD ≈ Valor_miles_USD × 1000` y `Valor_USD_por_par ≈ Valor_USD / Cantidad_pares`.

Totales válidos: importación **18.506,1 M USD**, exportación **10.917,3 M USD**.

La pestaña *Limpieza de datos* del tablero muestra el **diccionario de datos** (tipo, significado, valores observados y faltantes de las 10 columnas) y permite **descargar la tabla depurada** en Excel (`src/services/diccionario.py`, `src/services/reportes.py`).

---

## Guion de demo (2 minutos)

Antes: `python scripts/seed_demo.py`, `python scripts/seed_solucion.py` y `streamlit run app.py`. Ingrese como `admin`.

1. **Inicio (15 s).** Muestre los KPI y las alertas pendientes de la última semana: "el sistema detecta faltantes cada día".
2. **Apertura (20 s).** Tienda Prado → pestaña *Toda la tienda*: los saldos ya vienen propuestos desde el cierre de ayer → *Abrir 12 productos*.
3. **Ventas (20 s).** Venda 2 pares de `MAN-DEP-001`; el stock disponible baja al instante. Intente vender más de lo disponible: aparece el error claro.
4. **Foto (30 s).** *Cierre y conteo* → `MAN-DEP-001` → *Cámara* (o suba una foto de zapatos) → *Contar con IA*: se ven los recuadros numerados, el conteo y la confianza.
5. **Alerta (15 s).** Corrija el conteo final a 2 menos que el esperado → *Calcular y guardar cierre* → aparece la alerta roja "Faltan 2 pares…".
6. **Historial (10 s).** Filtre por estado *Faltante*, seleccione la fila para ver la foto y descargue el Excel.
7. **Tablero (10 s).** 240 registros válidos, los 3 gráficos y el cambio de métrica Valor USD / Cantidad de pares: por categoría el orden se mantiene, pero cambia el ranking de socios (República Checa entra al top 6 por pares).

---

## Estructura

```
app.py                 Inicio, login y navegación por rol
pages/                 Apertura, Ventas, Cierre y conteo, Historial, Tablero, Catálogo, Usuarios,
                       Pronóstico de demanda, Prototipo de escenario, Entregables escritos,
                       Inventario y compras, Clientes y segmentación, Recomendaciones,
                       Marketing y promociones, Contabilidad
src/config.py          Rutas, constantes, permisos y tolerancia
src/db.py, models.py   SQLite + SQLAlchemy
src/auth.py            Login, roles y bcrypt
src/services/          inventario (reglas), vision (YOLO-World), etl (Excel), diccionario (diccionario de datos),
                       reportes (Excel de salida: cierres y tabla depurada), pronostico,
                       compras (proveedores, reorden, órdenes de compra), recomendacion (FP-Growth/Apriori),
                       rfm (segmentación), promociones (carrito y campañas), contabilidad (libro diario)
src/ui/                estilos (CSS y tarjetas KPI), graficos (Plotly), comunes (selectores)
scripts/               init_db.py, seed_demo.py, seed_solucion.py (datos [Simulado]),
                       seed_modulos.py (compras, clientes, promociones y campañas),
                       generar_docx_solucion.py (Word de la solución), capturar_pantallas.py
tests/                 pytest: inventario, ETL, diccionario y tabla depurada, conteo por foto, pronóstico,
                       compras, recomendación, RFM, promociones y contabilidad
data/                  raw/ (Excel), fotos/ (evidencia), modelos/ (pesos YOLO), manaco.db
```

Pruebas: `python -m pytest`

---

## Limitaciones

- La base de comercio exterior es de **España**, no de Bolivia; sirve como referencia internacional.
- El **valor por par** es un valor aduanero, no el precio al consumidor.
- La **cobertura por año es desigual** (28 a 82 registros por año), así que no se sacan tendencias entre años.
- El conteo por foto con YOLO-World es *zero-shot*: funciona mejor con zapatos o cajas bien separados, buena luz y vista frontal. Con pilas apretadas conviene contar cajas o corregir a mano.
- Es un sistema local de un solo servidor con SQLite; no está pensado para muchos usuarios simultáneos en red.

## Próximos pasos

- Ajustar (*fine-tuning*) un detector con fotos reales de las tiendas Manaco.
- Integrar con el punto de venta para registrar ventas automáticamente.
- Migrar a PostgreSQL y desplegar en un servidor de la empresa con HTTPS.
- Incorporar datos de comercio exterior de Bolivia (INE / Aduana Nacional).
- Reportes automáticos por correo y control de traspasos entre tiendas.

## Publicar en Streamlit Community Cloud

1. Entre a [share.streamlit.io](https://share.streamlit.io) con su cuenta de GitHub → **Create app**.
2. Repositorio `edisonayala000-netizen/manaco-data`, rama `main`, archivo `app.py`; en *Advanced settings* elija **Python 3.11** → **Deploy**.
3. La primera vez que se abre, si la base no tiene usuarios, `app.py` ejecuta solo `init_db.py`, `seed_demo.py` y `seed_solucion.py` (Excel, usuario `admin`, datos de demo y datos [Simulado]).

`packages.txt` instala las librerías del sistema que necesita OpenCV, y `requirements.txt` usa PyTorch para CPU. En el plan gratuito los datos se reinician cuando la app se reinicia, y el conteo por foto puede no caber en la memoria disponible; en ese caso el sistema avisa y deja el conteo manual.

## Diseño y capturas

La identidad visual (paleta, tipografías Plus Jakarta Sans e Inter, íconos Material, tarjetas, banners y alertas) está centralizada en `src/ui/estilos.py`; los gráficos usan la plantilla Plotly `manaco` de `src/ui/graficos.py`. Para regenerar las capturas de `docs/capturas/`:

```bash
pip install playwright
streamlit run app.py --server.headless true --server.port 8502   # en otra terminal
python scripts/capturar_pantallas.py
```
