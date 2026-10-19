# Manaco Data

Control de inventario diario e inteligencia de mercado para la industria del calzado boliviana

Defensa de proyecto · Caso de estudio: Manaco

---

# El problema

- **Inventario sin control diario.** Las tiendas no saben si lo que cuentan al cerrar coincide con lo que debería haber, hasta el cierre contable mensual — cuando ya es tarde para investigar la causa.
- **Datos sin integrar.** Manaco no cruza su desempeño de ventas con el comportamiento del mercado externo de calzado: decide "a ciegas" frente a la competencia y al mercado informal.
- Consecuencia: mermas no detectadas a tiempo y decisiones de precio/producción sin respaldo de datos.

---

# Objetivo del proyecto

- Construir una plataforma web local que dé **control diario del inventario** (apertura → venta → cierre) con alertas automáticas.
- Integrar los **datos internos de ventas** con la **base de comercio exterior de calzado**, en un tablero que sustente decisiones.
- Entregar un sistema **real, funcional y demostrable**, no solo una maqueta.

---

# La solución: dos módulos

1. **Control de inventario por tienda**
   Apertura del saldo → ventas del día → cierre con conteo (foto + IA) → alerta automática de faltante o sobrante.

2. **Tablero de mercado**
   Limpieza y análisis del Excel de comercio exterior, cruzado con las ventas internas por categoría de producto.

---

# Tecnología utilizada

| Capa | Herramienta |
|---|---|
| Lenguaje | Python 3.11 |
| Interfaz web | Streamlit (multipágina) |
| Base de datos | SQLite + SQLAlchemy 2 |
| Datos | pandas, openpyxl |
| Gráficos | Plotly |
| Visión por computadora | Ultralytics YOLO-World (zero-shot) |
| Seguridad | bcrypt (hash de contraseñas) |
| Calidad | pytest |

---

# Arquitectura del sistema

```
app.py          -> Inicio, login y navegación por rol
pages/          -> Apertura, Ventas, Cierre y conteo,
                    Historial, Tablero, Catálogo, Usuarios
src/services/   -> inventario, vision (IA), etl, reportes
src/ui/         -> estilos y gráficos reutilizables
data/           -> Excel, fotos de evidencia, base SQLite
```

- Lógica de negocio **separada de la interfaz** → permite probarla con pytest sin levantar la web.

---

# Reglas de negocio del inventario

- **Saldo esperado** = saldo inicial − total vendido del día
- **Diferencia** = conteo final − saldo esperado
- Estado → `Correcto` · `Faltante` · `Sobrante`

Ejemplo real validado con pruebas automáticas:
Apertura **50** → Ventas **12** → Esperado **38** → Conteo **36**
→ Diferencia **−2** → *"Faltan 2 pares de MAN-DEP-001 en Tienda Prado (esperado 38, contado 36)"*

- No hay ventas sin apertura, ni ventas que superen el stock, ni cierres duplicados.

---

# Conteo de stock con inteligencia artificial

- Modelo **YOLO-World** (zero-shot): detecta "shoe" y "shoe box" sin entrenamiento previo con fotos de Manaco.
- La persona toma la foto (cámara o archivo) → la IA cuenta y marca los objetos → se convierte a **pares**.
- El umbral de confianza es ajustable; la imagen anotada queda como evidencia guardada.
- **La persona siempre tiene la última palabra:** puede corregir el conteo de la IA antes de guardar.

---

# Resiliencia: si la IA falla

- Sin internet o modelo no disponible → aviso claro y **conteo manual** como respaldo.
- Cero objetos detectados → se sugiere bajar el umbral o contar a mano.
- El sistema **nunca se cae** ni muestra errores técnicos al usuario.
- Se guardan siempre dos valores: el conteo de la IA y el conteo final confirmado.

---

# Roles y permisos

| Página | Administrador | Encargado | Gerencia |
|---|:---:|:---:|:---:|
| Inicio | Si | No | Si |
| Apertura / Ventas / Cierre | Si | Si | No |
| Historial | Si | No | Si |
| Tablero de mercado | Si | No | Si |
| Catálogo / Usuarios | Si | No | No |

- Solo el **administrador** puede anular un cierre, y siempre con un motivo auditado.

---

# Limpieza de datos (ETL)

- Excel de comercio exterior: **240 filas → 230 válidas, 10 descartadas**.
- 4 reglas aplicadas y registradas en bitácora:
  1. Validación de tipos y datos faltantes
  2. Separación de registros duplicados por socio "Mundo"
  3. Eliminación de claves repetidas (10 filas)
  4. Verificación de consistencia numérica
- Totales válidos: importación **17.055,8 M USD** · exportación **10.605,5 M USD**.

---

# Hallazgo clave del tablero de mercado

- La categoría **Deportivo importa ~3 veces lo que exporta** → fuerte dependencia de oferta externa.
- Cambiar la métrica de "Valor USD" a "Cantidad de pares" **cambia la conclusión** → el tablero deja elegir la métrica para evitar lecturas falsas.
- Cruce con datos internos: ventas de Manaco por categoría vs. comercio exterior por el mismo código SA6.

---

# Objetivos SMART y KPIs

| Objetivo | KPI |
|---|---|
| Menos del **5%** de cierres con diferencia por tienda en 3 meses | % de cierres `Correcto` |
| **100%** de tiendas con apertura–venta–cierre diario en el primer mes | Cierres hechos / aperturas del día |
| Pronóstico ajustado por mercado informal con menor error que el no ajustado | MAPE base vs. MAPE ajustado |

---

# Calidad y pruebas

- Pruebas automáticas con **pytest** sobre reglas de inventario, ETL y conversión a pares.
- Ejemplo de prueba obligatoria: 50 → 12 → 38 → 36 → diferencia −2.
- `python -m pytest` corre en verde antes de cada etapa del desarrollo.

---

# Limitaciones del sistema

- La base de comercio exterior es de **España**, no de Bolivia: sirve de referencia internacional, no de precio local.
- El valor por par es un **valor aduanero**, no el precio al consumidor.
- Sistema **local de un solo servidor** con SQLite: no pensado para muchos usuarios simultáneos en red.
- Datos de producción y pronóstico de largo plazo son **simulados**, no reales aún.

---

# Próximos pasos

- Ajustar (*fine-tuning*) un detector de IA con fotos reales de las tiendas Manaco.
- Integrar con el punto de venta para registrar ventas automáticamente.
- Migrar a PostgreSQL y desplegar en un servidor con HTTPS.
- Incorporar datos de comercio exterior de Bolivia (INE / Aduana Nacional).
- Reportes automáticos por correo y control de traspasos entre tiendas.

---

# Conclusiones

- Manaco Data pasa el control de inventario de **reactivo a preventivo**: detecta faltantes el mismo día, no al cierre mensual.
- Integra por primera vez los datos internos de ventas con el comportamiento del mercado externo.
- Es un sistema **real y probado**, no un prototipo visual: reglas de negocio con pruebas automáticas, roles con permisos reales y resiliencia ante fallos de la IA.

---

# Preguntas

Gracias.
