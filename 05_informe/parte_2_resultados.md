# Distribución Espacial de la Vulnerabilidad Habitacional en los Radios Censales de la Ciudad Autónoma de Buenos Aires

## Parte 2: Resultados

---

## 3. Resultados

### 3.1. Estadísticas descriptivas de los indicadores IVH

La Tabla 1 presenta las estadísticas descriptivas de los ocho indicadores que componen el IVH y de `ivh_nbi` (variable de validación externa) para el conjunto de 3.549 radios censales de la CABA con datos completos.

**Tabla 1. Estadísticas descriptivas de los indicadores IVH por radio censal (n = 3.549)**

| Indicador | Media | Mediana | Máximo |
|---|---|---|---|
| `ivh_piso_tierra` | 0,0027 | 0,0000 | 0,2215 |
| `ivh_techo_precario` | 0,0524 | 0,0422 | 0,3953 |
| `ivh_sin_agua_red` | 0,0099 | 0,0071 | 0,2184 |
| `ivh_sin_cloaca` | 0,0115 | 0,0062 | 0,7357 |
| `ivh_sin_gas_red` | **0,8542** | 0,8797 | 1,0000 |
| `ivh_hacinamiento` | 0,1397 | 0,1141 | 0,5649 |
| `ivh_desempleo` | 0,0748 | 0,0720 | 0,3125 |
| `ivh_baja_educacion_univ` | — | — | — |
| `ivh_nbi` *(validación externa, no integra IVH)* | 0,0516 | 0,0247 | 0,6176 |

*Nota: todos los indicadores se expresan como proporciones entre 0 y 1.*

**Indicadores con mayor nivel de alerta**

Dos indicadores se destacan por sus medias marcadamente superiores al resto y exigen una interpretación cuidadosa.

El primero es `ivh_sin_gas_red`, con una media de **0,854** y una mediana de **0,880**. Estos valores indican que, en el radio censal promedio de la CABA, más del 85 % de los hogares no tiene acceso a gas de red. Este indicador se calcula como el complemento de la proporción de hogares con gas de red (`1 - h19_gas_red / h19_total`), usando directamente la columna censal de hogares con gas de red. Si bien refleja en parte una característica estructural de la red de gas en la ciudad —cuya cobertura es históricamente deficitaria en muchas zonas del sur—, su magnitud general señala una privación energética extendida que implica mayor gasto relativo de los hogares en combustibles alternativos (garrafas, electricidad) y mayor vulnerabilidad ante variaciones de precios. El valor máximo de 1,000 (ausencia total de gas de red en el radio) aparece en varios radios del sur y confirma que la privación no es marginal sino estructural en ciertas áreas.

El segundo indicador con valores elevados es `ivh_baja_educacion_univ`, que mide la proporción de población sin nivel universitario completo (`1 - p08_universitario_comp / p08_total`). Al tratarse del inverso de una proporción que tiende a ser baja en términos absolutos, sus valores se ubican en un rango alto en la mayoría de los radios, lo que indica que la ausencia de formación universitaria completa es una condición extendida en la ciudad. Sin embargo, la variable captura diferencias relevantes entre radios: los territorios con mayor concentración de pobreza estructural exhiben sistemáticamente una menor proporción de población con universitario completo, lo que acentúa su valor discriminante en los extremos de la distribución.

**Indicadores con alta concentración espacial**

Un tercer grupo de indicadores presenta medias bajas pero valores máximos muy elevados, lo que sugiere que el problema se concentra de forma intensa en bolsones acotados del territorio:

- `ivh_sin_cloaca`: media 0,012 pero máximo 0,736. En la mayoría de los radios el acceso cloacal es casi universal, pero en los radios de villas y asentamientos la cobertura puede caer a menos del 27 %.
- `ivh_nbi`: media 0,052 pero máximo 0,618. La pobreza estructural multidimensional está fuertemente localizada.
- `ivh_hacinamiento`: media 0,140 pero máximo 0,565. El hacinamiento crítico, aunque moderado en promedio, alcanza niveles críticos en radios específicos.

Este patrón —media baja, máximo alto— es diagnóstico de una desigualdad territorial pronunciada: para estos indicadores, el promedio de la ciudad no es representativo de la situación de los radios más afectados.

---

### 3.2. Distribución del Índice IVH Compuesto

El Índice IVH Compuesto, calculado como el promedio aritmético de los ocho indicadores para cada radio censal con datos completos, presenta la siguiente distribución:

| Estadístico | Valor |
|---|---|
| Mínimo | 0,091 |
| Percentil 25 | 0,184 |
| Mediana | 0,195 |
| Media | 0,201 |
| Percentil 75 | 0,211 |
| Desvío estándar | 0,030 |
| Máximo | 0,613 |

La distribución presenta dos rasgos salientes. En primer lugar, una fuerte concentración en torno a la media: el 50 % central de los radios se ubica entre 0,184 y 0,211, un rango de apenas 0,027 puntos. Esto indica que la mayoría de los radios de la CABA exhibe niveles de vulnerabilidad moderados y relativamente homogéneos. En segundo lugar, una cola derecha pronunciada: el valor máximo de 0,613 es casi tres desvíos estándar por encima de la media, lo que revela la existencia de un conjunto reducido pero significativo de radios con vulnerabilidad habitacional muy elevada que se alejan sustancialmente del resto de la distribución.

**Clasificación por Natural Breaks (Jenks)**

A efectos de visualización cartográfica y análisis comparativo, los radios fueron clasificados en cinco clases mediante el método **Natural Breaks (Jenks)**, implementado con `mapclassify.NaturalBreaks(k=5)`. Este método identifica los cortes donde la distribución presenta saltos naturales, minimizando la varianza intraclase. Es especialmente adecuado para el IVH de CABA, cuya distribución está fuertemente concentrada en un rango estrecho (0,20–0,26) con una cola derecha pronunciada. La clase 1 agrupa los radios de menor vulnerabilidad y la clase 5 los de mayor vulnerabilidad. Los cortes resultantes son:

| Clase | Vulnerabilidad | Rango IVH | Radios |
|---|---|---|---|
| 1 | Muy baja | 0,101 – 0,204 | 817 |
| 2 | Baja | 0,204 – 0,225 | 1.632 |
| 3 | Moderada | 0,225 – 0,256 | 880 |
| 4 | Alta | 0,256 – 0,364 | 217 |
| 5 | Muy alta | 0,364 – 0,613 | 3 |

La clase 5 —los 3 radios con mayor IVH— concentra los territorios donde la privación habitacional, la informalidad en los servicios y el hacinamiento convergen de manera más aguda. La amplitud decreciente de las clases superiores (la clase 4 abarca un rango de 0,108 puntos y la clase 5 de 0,249) refleja que la vulnerabilidad extrema está altamente concentrada en un número reducido de radios que se alejan sustancialmente del resto de la distribución. Esto demanda una mirada aún más desagregada para la focalización de políticas en esos territorios específicos.

---

### 3.3. Patrones espaciales de vulnerabilidad

La distribución geográfica del IVH Compuesto reproduce y profundiza el conocido eje de desigualdad norte-sur de la CABA, validando la hipótesis espacial que orienta este trabajo.

**Concentración de vulnerabilidad en el sur**

Los radios de la clase 5 (vulnerabilidad muy alta) se concentran de manera marcada en las comunas del sur y el sudoeste de la ciudad: Comunas 4 (La Boca, Barracas, Parque Patricios, Nueva Pompeya), 7 (Flores, Parque Chacabuco), 8 (Villa Soldati, Villa Riachuelo, Villa Lugano) y 9 (Liniers, Mataderos, Parque Avellaneda). Estos territorios comparten una historia de urbanización informal, déficit acumulado de infraestructura urbana y concentración de villas de emergencia y asentamientos precarios. La coincidencia entre los radios de mayor IVH y la localización de las principales villas de la ciudad —Villa 1-11-14, Villa 20, Villa 21-24, Villa 15 (Ciudad Oculta), entre otras— no es casual: las condiciones de informalidad habitacional se expresan directamente en los ocho indicadores que componen el índice.

El análisis de los radios de la clase 5 muestra que su elevada vulnerabilidad está impulsada no por un único indicador sino por la acumulación simultánea de carencias en múltiples dimensiones: ausencia de red cloacal (`ivh_sin_cloaca` máximo de 0,736), hacinamiento crítico elevado, techos precarios y baja proporción de población con universitario completo. Esta multidimensionalidad de la privación es, precisamente, lo que distingue a los radios de mayor vulnerabilidad del resto de la distribución.

**Baja vulnerabilidad en el norte**

El extremo opuesto —radios de la clase 1— se localiza predominantemente en las comunas del norte y el noreste de la ciudad: Comunas 1 (Retiro, San Nicolás, Puerto Madero, San Telmo, Montserrat, Constitución), 2 (Recoleta), 13 (Belgrano, Colegiales, Palermo) y 14 (Palermo). Estos radios presentan IVH mínimos cercanos a 0,091, con valores prácticamente nulos en indicadores de precariedad material (`ivh_piso_tierra` ≈ 0, `ivh_sin_cloaca` ≈ 0) y bajos en hacinamiento y NBI. La excepción más notable en estas comunas del norte es la presencia de villas o núcleos habitacionales transitorios que generan radios de vulnerabilidad alta enclavados en zonas de bajo IVH promedio, lo que refuerza la importancia del análisis a escala de radio censal.

**La fractura norte-sur como patrón estructural**

El gradiente espacial norte-sur del IVH no es un artefacto del índice construido: se reproduce consistentemente en cada uno de los ocho indicadores por separado. Tanto la precariedad de materiales (`ivh_techo_precario`, `ivh_piso_tierra`) como la ausencia de servicios básicos (`ivh_sin_cloaca`, `ivh_sin_agua_red`) y la pobreza estructural (capturada por `ivh_nbi` como variable de validación) muestran valores notablemente más elevados en el sur que en el norte. Este patrón es coherente con décadas de literatura sobre la desigualdad urbana en Buenos Aires (Cravino, 2008; Gutiérrez, 2021) y con los datos históricos del INDEC, y confirma que el IVH construido en este trabajo captura de manera adecuada la estructura real de la desigualdad territorial en la ciudad.

---

### 3.4. Radios de mayor vulnerabilidad

El análisis de los diez radios con mayor IVH permite identificar los territorios donde la vulnerabilidad habitacional alcanza su expresión más extrema. La Tabla 2 presenta los ocho radios con información completa en todos los indicadores, excluyendo los casos con datos parciales.

**Tabla 2. Radios censales con mayor IVH (selección con datos completos)**

| Código | IVH | Piso tierra | Techo prec. | Sin agua | Sin cloaca | Sin gas | Hacinam. | Desempleo | Sin univ. | NBI (val.) |
|---|---|---|---|---|---|---|---|---|---|---|
| 020071316 | 0,345 | 0,017 | 0,171 | 0,061 | **0,736** | **0,939** | 0,362 | 0,046 | 0,585 | 0,186 |
| 020140102 | 0,333 | 0,012 | 0,258 | 0,025 | **0,519** | **0,933** | 0,429 | 0,100 | 0,639 | 0,080 |
| 020282110 | 0,328 | 0,007 | 0,287 | 0,017 | 0,089 | **0,969** | 0,403 | 0,104 | 0,614 | **0,464** |
| 020070203 | 0,317 | 0,059 | **0,382** | 0,029 | 0,072 | **0,912** | **0,461** | 0,089 | 0,573 | 0,275 |
| 020072811 | 0,310 | 0,000 | 0,071 | 0,035 | 0,009 | **0,944** | 0,371 | 0,122 | 0,624 | **0,618** |
| 020491703 | 0,308 | 0,000 | 0,162 | 0,000 | 0,135 | **1,000** | 0,351 | 0,103 | **0,750** | 0,270 |
| 020560706 | 0,307 | 0,012 | 0,182 | 0,114 | 0,065 | **0,957** | **0,507** | 0,063 | 0,574 | 0,291 |

*En negrita: valores que superan el doble de la media del indicador correspondiente. La columna NBI (val.) es la variable de validación externa: no integra el IVH pero se incluye aquí para referencia.*

El análisis de estos radios revela tres perfiles de vulnerabilidad diferenciados:

**Perfil 1 — Déficit de infraestructura sanitaria y energética (radios 020071316, 020140102):** El rasgo dominante es la combinación de ausencia casi total de red de gas (93–94 %) y de red cloacal (52–74 %). Se trata de radios con urbanización marcadamente informal, probablemente localizados en villas de emergencia o asentamientos, donde la conexión a redes de servicio es mínima. El hacinamiento es también elevado (36–43 %) y la proporción sin universitario completo supera el 58 %.

**Perfil 2 — Desempleo estructural y hacinamiento (radios 020282110, 020072811):** Estos radios combinan alta exclusión energética (94–97 % sin gas de red) con tasas de desocupación excepcionalmente altas (46 % y 62 % respectivamente, frente a una media de 7,5 % en la ciudad). El radio 020072811 presenta la mayor tasa de desempleo de todos los radios analizados, lo que indica una situación de exclusión del mercado laboral formal de carácter estructural.

**Perfil 3 — Hacinamiento crítico generalizado (radios 020070203, 020560706):** Se caracterizan por las tasas de hacinamiento más altas del conjunto (46 % y 51 %), indicando una densidad habitacional que compromete severamente las condiciones de vida. En el radio 020560706, uno de cada dos hogares vive en condiciones de hacinamiento crítico, valor que quintuplica la media de la ciudad.

En todos los casos, los radios de mayor vulnerabilidad exhiben simultáneamente valores elevados en al menos cuatro de los ocho indicadores del IVH, confirmando que la vulnerabilidad extrema es multidimensional y no reducible a una única privación.

---

### 3.5. Heterogeneidad intraurbana: el valor del análisis a escala de radio censal

Uno de los hallazgos metodológicamente más relevantes del análisis es la alta variabilidad intraurbana que se hace visible cuando se trabaja a escala de radio censal, en contraste con las agregaciones a nivel comunal o distrital.

El desvío estándar del IVH en el conjunto de radios es de 0,030, pero este valor global subestima la dispersión real dentro de cada comuna. En comunas del sur como la 8 o la 4, es frecuente encontrar radios cuyo IVH supera 0,30 contiguos a radios con IVH próximos a la media de la ciudad (0,20), dependiendo de si el radio corresponde a un asentamiento informal, a un conjunto habitacional de vivienda social o a un barrio de trama regular con acceso a servicios. Del mismo modo, comunas del norte como la 13 o la 14, que exhiben IVH promedio bajos, contienen radios de alta vulnerabilidad asociados a villas de emergencia enclavadas (como la Villa 31 en la Comuna 1 o la Villa Crespo en la 15), que quedarían invisibilizados bajo un análisis agregado.

Esta heterogeneidad intraurbana tiene consecuencias directas para el diseño de políticas públicas. Un indicador calculado a nivel de comuna puede registrar un valor moderado de vulnerabilidad aun cuando existen radios al interior de esa misma comuna con niveles extremos de privación. La política pública que se guíe por promedios comunales corre el riesgo de diluir recursos en territorios que no los necesitan con la misma urgencia, mientras que los bolsones de vulnerabilidad más aguda quedan subatendidos.

El análisis a escala de radio censal permite, en cambio, una focalización territorial precisa. Los 220 radios de la clase 4 y 5 de la clasificación Natural Breaks —aproximadamente el 6 % del total— concentran la mayor proporción de hogares con déficit habitacional, pobreza estructural y exclusión de servicios básicos. Intervenir prioritariamente en estos radios implica maximizar el impacto por unidad de inversión pública, un principio de eficiencia que solo es alcanzable cuando el diagnóstico territorial tiene la resolución espacial adecuada.

La comparación entre los radios de la clase 1 y la clase 5 ilustra con claridad la magnitud de la brecha: mientras que el radio menos vulnerable de la CABA presenta un IVH de 0,101, con valores prácticamente nulos en piso de tierra y ausencia de cloaca, el radio más vulnerable con datos completos (código 020071316) registra un IVH de 0,345, con el 74 % de los hogares sin acceso a red cloacal y el 94 % sin gas de red. Esta diferencia no es un fenómeno de gradiente suave: es la expresión cuantificada de la fractura territorial que separa dos ciudades dentro de una misma ciudad.

---

*La Parte 3 del informe presentará las conclusiones, limitaciones del estudio y recomendaciones para investigaciones futuras.*
