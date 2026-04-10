# Distribución Espacial de la Vulnerabilidad Habitacional en los Radios Censales de la Ciudad Autónoma de Buenos Aires

## Parte 1: Introducción, Área de Estudio, Fuentes de Datos y Metodología

---

## 1. Introducción

La Ciudad Autónoma de Buenos Aires (CABA) constituye uno de los territorios urbanos más complejos y desiguales de América Latina. A pesar de concentrar los niveles más altos de ingreso per cápita y de acceso a servicios del país, su trama urbana alberga profundas asimetrías territoriales: villas de emergencia con carencias habitacionales severas coexisten a escasos kilómetros de barrios con indicadores comparables a los de ciudades europeas. Esta heterogeneidad intraurbana rara vez queda capturada por estadísticas agregadas a nivel comunal o distrital, lo que justifica el análisis a escalas espaciales más finas. El radio censal —unidad mínima de relevamiento del Instituto Nacional de Estadística y Censos (INDEC)— permite desagregar la información a un nivel de detalle que hace visible la inequidad en su expresión territorial más concreta.

El presente trabajo se propone analizar la distribución espacial de la vulnerabilidad habitacional en los radios censales de la CABA a partir de los datos del Censo Nacional de Población, Hogares y Viviendas 2022 (INDEC). La pregunta central que orienta el análisis es: **¿Cómo se distribuyen espacialmente los indicadores de vulnerabilidad habitacional en los radios censales de la Ciudad Autónoma de Buenos Aires?** Para responderla, se construye un Índice de Vulnerabilidad Habitacional (IVH) compuesto por ocho indicadores que capturan distintas dimensiones del déficit habitacional, la precariedad de los servicios básicos, el hacinamiento y la educación. El resultado es una cartografía de la vulnerabilidad a escala sub-barrial que puede orientar políticas públicas focalizadas.

---

## 2. Área de Estudio

La Ciudad Autónoma de Buenos Aires es la capital federal de la República Argentina y se ubica en la margen occidental del Río de la Plata, con una superficie de aproximadamente 202 km². Según el Censo Nacional 2022 (INDEC), la ciudad cuenta con una población de 3.120.612 habitantes, distribuidos en 15 comunas y aproximadamente 3.820 radios censales. Se trata del distrito más densamente poblado del país y, al mismo tiempo, el de mayor producto bruto geográfico per cápita. Sin embargo, esta riqueza agregada convive con bolsones de pobreza estructural localizados principalmente en el sur de la ciudad —en comunas como la 4, la 7, la 8 y la 9—, donde se concentran las villas de emergencia, los asentamientos informales y los barrios con mayor déficit de infraestructura urbana. La CABA resulta, por todo ello, un caso de estudio privilegiado para el análisis de la desigualdad intraurbana: su extensión reducida, su densa trama catastral y la disponibilidad de datos censales desagregados permiten examinar con alta resolución espacial los patrones de distribución de la vulnerabilidad habitacional.

---

## 3. Fuentes de Datos

### 3.1. Censo Nacional de Población, Hogares y Viviendas 2022 — INDEC

La fuente primaria de información es el Censo Nacional de Población, Hogares y Viviendas 2022, relevado por el INDEC. Los datos a nivel de radio censal fueron extraídos mediante el portal de consultas en línea **REDATAM CPV2022** (`https://redatam.indec.gob.ar`), que permite generar tabulados personalizados con variables de vivienda, hogar y población desagregadas hasta el nivel de radio censal.

Las variables seleccionadas cubren cinco dimensiones analíticas:

| Dimensión | Variables censales utilizadas |
|---|---|
| Calidad de la vivienda | Material del piso; material del techo |
| Servicios básicos | Procedencia del agua; desagüe del servicio sanitario; combustible para cocinar |
| Hacinamiento | Cantidad de personas por cuarto |
| Necesidades Básicas Insatisfechas | NBI (al menos 1 indicador) |
| Educación y empleo | Nivel educativo máximo alcanzado; condición de actividad económica |

La selección de estas variables responde a su reconocida pertinencia teórica en la medición del déficit habitacional y la pobreza multidimensional (INDEC, 2022), así como a su disponibilidad para todos los radios censales de la CABA en el operativo 2022.

### 3.2. Cartografía Censal — INDEC

La cartografía de radios censales de la CABA fue obtenida del portal de información geográfica del INDEC en formato shapefile (`cabaxrdatos.shp`). El sistema de referencia de coordenadas utilizado es **EPSG:22183** (POSGAR 94 / Argentina 3), proyección plana en metros adecuada para cálculos de área y distancia en el territorio continental argentino.

El shapefile contiene la geometría poligonal de los radios censales junto con el identificador único de radio (`link` o código de 9 dígitos), que se utilizó como clave de unión (*join*) con los tabulados estadísticos extraídos de REDATAM. La unión espacial se realizó en Python mediante la biblioteca `geopandas`, cruzando el campo `link` del shapefile con el identificador de radio presente en cada CSV de REDATAM. El resultado fue un GeoDataFrame con 3.555 radios con geometría válida y datos censales completos.

---

## 4. Metodología

### 4.1. Extracción y preparación de datos

Los datos censales se obtuvieron mediante seis consultas independientes en el portal REDATAM CPV2022, generando seis archivos CSV, cada uno correspondiente a un bloque de variables. Cada consulta fue parametrizada para obtener la distribución de frecuencias de la variable seleccionada desagregada por radio censal de la CABA. Los archivos fueron procesados en Python con la biblioteca `pandas`, normalizando los nombres de columnas, eliminando registros con valores nulos o inconsistentes, y consolidando todos los bloques en una única tabla maestra a nivel de radio censal.

### 4.2. Construcción de los indicadores IVH

A partir de la tabla maestra se calcularon ocho indicadores de vulnerabilidad habitacional (IVH), todos expresados como **proporciones entre 0 y 1** (donde 0 indica ausencia de vulnerabilidad y 1 indica vulnerabilidad máxima en esa dimensión). La formulación general de cada indicador es:

> *IVH_i = hogares (o personas) en condición de vulnerabilidad en la dimensión i / total de hogares (o personas) del radio*

Adicionalmente, se calcula `ivh_nbi` (proporción con al menos 1 NBI) que se conserva en el GeoDataFrame como **variable de validación externa** pero no integra el promedio del IVH compuesto, dado que presenta multicolinealidad con otras variables del índice (ver Sección 4.3).

Los ocho indicadores que componen el IVH y su justificación teórica son los siguientes:

| Indicador | Descripción | Justificación |
|---|---|---|
| `ivh_piso_tierra` | Proporción de hogares con piso de tierra o ladrillo suelto | El piso de tierra es uno de los indicadores clásicos de precariedad estructural de la vivienda (INDEC, NBI) |
| `ivh_techo_precario` | Proporción con techos de cartón, caña, tabla o material sin cubierta asfáltica | Indicador directo de déficit en la calidad constructiva de la vivienda |
| `ivh_sin_agua_red` | Proporción sin conexión a red de agua potable | El acceso al agua por red es un derecho básico y un indicador de integración urbana |
| `ivh_sin_cloaca` | Proporción sin conexión a red cloacal | La ausencia de desagüe cloacal genera riesgos sanitarios y es marcador de informalidad urbana |
| `ivh_sin_gas_red` | Proporción de hogares sin gas de red (calculado como complemento de hogares con gas de red sobre total: `1 - h19_gas_red / h19_total`) | Refleja exclusión de la infraestructura energética formal y mayor gasto relativo en energía |
| `ivh_hacinamiento` | Proporción con hacinamiento crítico (≥1,5 personas por cuarto) | El hacinamiento crítico compromete la salud, la privacidad y el desarrollo de los habitantes |
| `ivh_desempleo` | Tasa de desocupación (desocupados / activos) | El desempleo es un determinante clave de la capacidad de acceso y mantenimiento de la vivienda |
| `ivh_baja_educacion_univ` | Proporción de hogares sin nivel universitario completo (inverso de la proporción con universitario completo sobre población total: `1 - p08_universitario_comp / p08_total`) | La ausencia de educación universitaria completa se asocia a mayor precariedad laboral y menor capacidad de inserción en el mercado formal |

### 4.3. Construcción del Índice IVH compuesto

El índice compuesto se calculó como el **promedio aritmético simple** de los ocho indicadores:

> *IVH = (ivh_piso_tierra + ivh_techo_precario + ivh_sin_agua_red + ivh_sin_cloaca + ivh_sin_gas_red + ivh_hacinamiento + ivh_desempleo + ivh_baja_educacion_univ) / 8*

La variable `ivh_nbi` fue evaluada como candidata pero se excluyó del promedio por presentar multicolinealidad con otras dimensiones ya capturadas en el índice: correlación r = 0,72 con `ivh_hacinamiento` y r = 0,45 con `ivh_techo_precario`. El NBI por definición incluye componentes de hacinamiento, condiciones habitacionales y saneamiento; incorporarlo generaría doble peso sobre esas dimensiones sin aportar información independiente. Se conserva en el GeoDataFrame como variable de validación externa: permite verificar que el IVH construido correlaciona con la medida oficial de pobreza estructural del INDEC.

La decisión de utilizar ponderación igualitaria para los ocho indicadores que integran el IVH responde a un criterio de neutralidad analítica: en ausencia de evidencia empírica que justifique asignar mayor peso a alguna dimensión en particular, se otorga igual importancia a cada una. Este enfoque es coherente con la perspectiva multidimensional de la pobreza y el déficit habitacional, que reconoce que ningún indicador aislado captura la complejidad del fenómeno (Sen, 1999; INDEC, 2022).

El IVH resultante tiene un rango de 0,10 a 0,61 para los radios de la CABA, con una media de 0,22. Para facilitar la visualización cartográfica y la comparación entre radios, el índice fue clasificado en **cinco clases** mediante el método **Natural Breaks (Jenks)**, implementado con `mapclassify.NaturalBreaks(k=5)`. Este método minimiza la varianza intraclase e identifica los cortes donde la distribución presenta saltos naturales, lo que resulta más adecuado que los quintiles de igual frecuencia para una distribución fuertemente asimétrica como la del IVH —donde la mayoría de los radios se concentra en un rango estrecho (0,18–0,26) y una cola derecha con pocos radios de vulnerabilidad muy alta se extiende hasta 0,61. La clase 1 corresponde a vulnerabilidad muy baja y la clase 5 a vulnerabilidad muy alta.

### 4.4. Integración espacial

La unión entre los datos estadísticos y la cartografía censal se realizó mediante un *merge* entre el GeoDataFrame del shapefile `cabaxrdatos.shp` y el DataFrame con los indicadores IVH, utilizando el código de radio censal como clave. El resultado fue un GeoDataFrame georreferenciado con 3.555 radios válidos (de los 3.820 totales; la diferencia corresponde a radios sin población residente o con geometría no disponible en la cartografía oficial del INDEC). Todo el procesamiento fue realizado en **Python 3**, utilizando las bibliotecas `pandas` (manipulación de datos tabulares), `geopandas` (operaciones geoespaciales y cartografía) y `matplotlib`/`contextily` (visualización de mapas).

---

## Referencias

- INDEC (2022). *Censo Nacional de Población, Hogares y Viviendas 2022*. Instituto Nacional de Estadística y Censos. Buenos Aires, Argentina.
- INDEC (2022). *Cartografía y áreas estadísticas: shapefile de radios censales, Ciudad Autónoma de Buenos Aires*. Instituto Nacional de Estadística y Censos.
- INDEC (s.f.). *REDATAM CPV2022 — Portal de consultas en línea*. Recuperado de https://redatam.indec.gob.ar
- Sen, A. (1999). *Development as Freedom*. Oxford University Press.
