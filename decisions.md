# Decisiones Técnicas del Proyecto — Plan de Expansión

Este documento registra las decisiones técnicas tomadas durante el desarrollo del proyecto de análisis geoespacial de calidad de vida urbana en CABA. Para cada decisión se documentan las alternativas consideradas y la justificación técnica que llevó a la elección final.

---

## Tabla de resumen

| ID  | Decisión                                       | Resultado elegido                          |
|-----|------------------------------------------------|--------------------------------------------|
| D01 | Jurisdicción de análisis                       | CABA (Ciudad Autónoma de Buenos Aires)     |
| D02 | Herramienta principal de análisis              | Python (geopandas + matplotlib + folium)   |
| D03 | Formato de datos procesados                    | GeoPackage (.gpkg)                         |
| D04 | Sistema de referencia de coordenadas           | POSGAR 2007 para análisis + WGS84 para viz |
| D05 | Variables de calidad de vida                   | 7 indicadores en 3 dimensiones             |
| D06 | Normalización del IVH                          | Min-Max scaling entre 0 y 1               |
| D07 | Clasificación de mapas coropléticos            | Cuantiles con 5 clases (quintiles)         |
| D08 | Estructura de scripts                          | Pipeline secuencial numerado (01_, 02_...) |

---

## Detalle de decisiones

---

### D01 — Jurisdicción elegida: CABA

**Decisión**: Usar CABA (Ciudad Autónoma de Buenos Aires) como jurisdicción de análisis.

**Alternativas consideradas**:
- GBA (Gran Buenos Aires)
- La Matanza
- Rosario

**Justificación técnica**: CABA presenta una combinación de factores que la hacen ideal para este trabajo. Cuenta con alta densidad de radios censales (aproximadamente 3.500), lo que permite análisis a escala fina. Existe un fuerte contraste socioeconómico entre el norte y el sur de la ciudad (Palermo vs. Lugano/villas), lo que hace que los indicadores de calidad de vida tengan varianza significativa y sean informativos. Los datos del INDEC están bien estructurados y documentados para esta jurisdicción, y las capas de comunas están disponibles en el portal Buenos Aires Data con metadatos completos. La escala geográfica es manejable para un trabajo académico sin sacrificar representatividad.

---

### D02 — Herramienta principal: Python sobre R/QGIS

**Decisión**: Python con el stack geopandas + matplotlib + folium como herramienta principal de análisis y visualización.

**Alternativas consideradas**:
- R con sf + tmap + ggplot2
- QGIS (análisis visual puro)

**Justificación técnica**: Python permite un flujo de trabajo completamente reproducible y scripteable desde la limpieza de datos hasta la visualización final, sin intervención manual en ningún paso intermedio. `geopandas` es actualmente el estándar de facto para GIS en Python y cuenta con amplia documentación y comunidad activa. R con `tmap` sería técnicamente equivalente pero implicaría cambiar de ecosistema para quienes trabajan principalmente en Python, incrementando la curva de entrada para revisores. QGIS se utiliza únicamente para verificación visual inicial de capas y no forma parte del pipeline de procesamiento — esto garantiza que todos los resultados sean completamente reproducibles desde código.

---

### D03 — Formato de datos procesados: GeoPackage (.gpkg)

**Decisión**: Guardar todos los datos procesados en formato GeoPackage.

**Alternativas consideradas**:
- Shapefile (.shp)
- GeoJSON
- Parquet con geometría (GeoParquet)

**Justificación técnica**: GeoPackage es un formato moderno basado en SQLite que se distribuye como un único archivo, eliminando la complejidad de gestionar los 4 a 6 archivos que componen un shapefile (.shp, .dbf, .prj, .shx, etc.). Además, no impone la limitación de 10 caracteres en nombres de columnas que tiene el shapefile, lo que permite nombrar las variables de forma descriptiva sin abreviaciones crípticas. GeoPackage es el formato recomendado por el Open Geospatial Consortium (OGC) para el intercambio de datos vectoriales. Los datos crudos del INDEC se reciben en formato shapefile y se conservan en ese formato original; la conversión a .gpkg aplica únicamente a los datos procesados generados por el pipeline.

---

### D04 — Sistema de referencia de coordenadas: doble CRS

**Decisión**: Usar POSGAR 2007 (EPSG:22184) para análisis espacial y WGS84 (EPSG:4326) para visualización interactiva.

**Alternativas consideradas**:
- Solo WGS84 para todas las operaciones

**Justificación técnica**: POSGAR 2007 es el sistema de referencia oficial de Argentina, expresado en metros, lo que es indispensable para cualquier cálculo de área, distancia o densidad que se realice en fases posteriores del proyecto. Realizar estos cálculos en WGS84 (grados decimales) introduciría errores métricos no triviales a la latitud de Buenos Aires. Sin embargo, `folium` —la librería usada para el mapa interactivo— requiere coordenadas en WGS84 para renderizar sobre tiles de Leaflet. Los scripts del pipeline realizan la conversión automáticamente según el contexto: proyectan a POSGAR 2007 antes de análisis y reprojectan a WGS84 antes de exportar para visualización.

---

### D05 — Variables de calidad de vida: 7 indicadores en 3 dimensiones

**Decisión**: Usar 7 variables agrupadas en tres dimensiones: habitacional, servicios básicos y educación.

**Alternativas consideradas**:
- Solo NBI (Necesidades Básicas Insatisfechas), si INDEC lo publica a nivel de radio censal
- Agregar dimensiones de salud y empleo

**Justificación técnica**: Las 7 variables seleccionadas son relevadas directamente en el Censo 2022 a nivel de vivienda u hogar, lo que garantiza disponibilidad y desagregación por radio censal. Son reconocidas internacionalmente como proxies válidos de calidad de vida urbana por organismos como CEPAL y Banco Mundial. El Censo Nacional no releva ingresos ni situación laboral detallada, por lo que las dimensiones de empleo y salud no pueden incorporarse sin recurrir a fuentes externas (EPH, SISA), lo que introduciría problemas de cobertura geográfica y temporalidad distintos. Si INDEC publica el indicador NBI desagregado por radio censal para el Censo 2022, se evaluará su incorporación como variable adicional o de validación del IVH.

---

### D06 — Normalización del IVH: Min-Max entre 0 y 1

**Decisión**: Normalizar cada variable con Min-Max scaling antes de promediar para construir el Índice de Vulnerabilidad Habitacional (IVH).

**Alternativas consideradas**:
- Z-score (estandarización con media 0 y desviación estándar 1)
- Percentiles
- Pesos diferenciales por variable (ponderación experta)

**Justificación técnica**: La normalización Min-Max produce valores en el rango [0, 1] que son interpretables directamente: 0 representa el radio censal con mejor desempeño en esa variable dentro del dataset, y 1 el de peor desempeño. Esta interpretabilidad es importante para la comunicación de resultados académicos. El Z-score produciría valores negativos y positivos centrados en cero, lo que dificulta la comunicación a audiencias no especializadas y complica la construcción de un índice compuesto. Para este trabajo introductorio, se asignan pesos iguales a todas las variables, evitando la necesidad de justificar una ponderación diferencial que requeriría análisis de expertos o datos adicionales. En fases futuras, se puede explorar Análisis de Componentes Principales (ACP) para derivar pesos basados en la varianza explicada por cada variable.

---

### D07 — Clasificación de mapas coropléticos: Cuantiles con 5 clases

**Decisión**: Usar clasificación por cuantiles (quintiles) para los mapas estáticos coropléticos.

**Alternativas consideradas**:
- Jenks Natural Breaks
- Equal Interval (intervalos iguales)
- Standard Deviation (desviación estándar)

**Justificación técnica**: La clasificación por cuantiles garantiza que cada clase contenga el mismo número de radios censales, produciendo mapas visualmente equilibrados aun cuando la distribución de los datos sea asimétrica —lo que ocurre con frecuencia en indicadores de vulnerabilidad, donde muchos radios concentran valores similares en los extremos. Equal Interval produce clases de igual amplitud numérica pero puede resultar en algunas clases con muy pocos o ningún polígono si la distribución no es uniforme. Standard Deviation es útil para comunicar desviaciones respecto a la media pero no es intuitivo para audiencias generales. Jenks Natural Breaks minimiza la varianza intra-clase y maximiza la inter-clase, siendo más preciso para identificar agrupamientos reales —para el mapa del IVH compuesto se evaluará adicionalmente esta clasificación, dado que el IVH puede presentar una distribución más continua y uniforme que las variables individuales.

---

### D08 — Estructura de scripts: pipeline secuencial numerado

**Decisión**: Organizar el código en scripts independientes numerados (01_, 02_, ...) con entrada y salida explícitas entre etapas.

**Alternativas consideradas**:
- Un único notebook Jupyter con todo el análisis
- Un script monolítico
- Un Makefile con targets por etapa

**Justificación técnica**: Los scripts numerados son reproducibles, fáciles de inspeccionar individualmente por revisores o evaluadores, y permiten ejecutar solo una fase del pipeline sin reprocesar todo desde cero (por ejemplo, regenerar los mapas sin volver a limpiar los datos). Cada script recibe archivos de entrada definidos y produce archivos de salida documentados, lo que hace el flujo de datos explícito y verificable. Un Jupyter notebook mezcla código ejecutable con resultados embebidos, lo que complica el control de versiones (los outputs quedan en el JSON del .ipynb) y dificulta la reutilización modular. Un script monolítico es difícil de depurar y de explicar en un contexto académico. Un Makefile sería ideal para proyectos más grandes pero agrega complejidad de infraestructura innecesaria para este alcance.

---

*Documento generado el 2026-04-03. Las decisiones se actualizan a medida que avanza el proyecto.*
