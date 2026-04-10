# Plan: Correcciones IVH — TP Plan de Expansión CABA

## Contexto

El TP calcula un Índice de Vulnerabilidad Habitacional (IVH) a nivel de radio censal para CABA usando datos del Censo 2022. El docente solicitó 6 correcciones metodológicas/técnicas. El pipeline es lineal: `01_descarga_y_limpieza.py` → `02_join_espacial.py` → `03_calculo_indicadores.py` → `04_mapas_estaticos.py` → `05_mapa_interactivo.py`.

---

## Fase 1 — Redefinición de variables (`01_descarga_y_limpieza.py`)

### 1.1 Variables por el positivo (todas)

**Problema**: Todas las variables están expresadas como "sin X" (ausencia del servicio).

**Cambio**: Calcular como "con X" (presencia del servicio). Renombrar variables de `ivh_sin_*` a `ivh_con_*`. Esto requiere usar el numerador correcto: hogares que SÍ tienen el servicio.

| Variable actual | Variable nueva | Numerador nuevo |
|----------------|----------------|-----------------|
| `ivh_sin_agua_red` | `ivh_con_agua_red` | `h14_red_publica / h14_total` |
| `ivh_sin_cloaca` | `ivh_con_cloaca` | `h18_red_publica / h18_total` |
| `ivh_sin_gas_red` | `ivh_con_gas_red` | `h19_gas_red / h19_total` |
| `ivh_piso_tierra` | `ivh_piso_adecuado` | `1 - ivh_piso_tierra` (o calcular directo) |
| `ivh_techo_precario` | `ivh_techo_adecuado` | `1 - ivh_techo_precario` |
| `ivh_hacinamiento` | `ivh_sin_hacinamiento` | `1 - ivh_hacinamiento` |
| `ivh_desempleo` | `ivh_con_empleo` | `ocupados / (ocupados + desocupados)` |
| `ivh_nbi` | → ver Fase 2 | — |

**Impacto en IVH**: Como variables positivas (alto = bueno), el IVH final se calcula como:
```python
IVH = 1 - mean(variables_positivas)
```
Esto mantiene la escala: IVH alto = más vulnerable.

### 1.2 Gas de red — verificar y corregir

**Problema**: "Sin gas de red nos quedó demasiado alto". La fórmula actual suma garrafa + pozo/planta + leña + electricidad + otro. Esto puede estar inflado porque en CABA "electricidad" como calefacción es una forma alternativa al gas, no necesariamente ausencia de red.

**Corrección**: Calcular usando el numerador directo de `h19_gas_red` (hogares con gas de red pública). El porcentaje de gas de red en CABA debe ser muy alto (≥80%) en la mayoría de radios.

```python
merged["ivh_con_gas_red"] = safe_div(merged["h19_gas_red"], merged["h19_total"])
```

### 1.3 Educación como variable binaria

**Cambio**: Eliminar `ivh_baja_educacion` (proporción con primaria como máximo). Reemplazar por proporción con **nivel universitario completo**.

```python
merged["ivh_con_educacion_univ"] = safe_div(
    merged["p08_universitario_comp"], merged["p08_total"]
)
```

Esta variable es positiva (alto = mejor situación educativa).

---

## Fase 2 — Correlación NBI + recálculo IVH (`03_calculo_indicadores.py`)

### 2.1 Análisis de correlación entre variables con NBI

**Problema**: El NBI del INDEC por definición ya incluye dimensiones de hacinamiento, condiciones habitacionales, saneamiento y educación — las mismas que nuestros indicadores individuales. Incluirlo en el promedio da doble peso a esas dimensiones.

**Acción**:
1. Calcular y printar/guardar la **matriz de correlación de Pearson** entre todos los indicadores y el NBI.
2. Basado en los coeficientes observados: si NBI tiene r > 0.7 con varias variables, excluirlo del IVH y usarlo como variable de **validación externa** del índice.
3. Agregar en el script un bloque de análisis de correlación con output a CSV/PNG.

```python
import seaborn as sns
corr_matrix = gdf[VARS_IVH].corr()
# guardar como heatmap en 04_mapas/correlacion_ivh.png
```

### 2.2 Recálculo del IVH con variables positivas

**Nuevo cálculo**:
```python
VARS_IVH = [
    "ivh_con_agua_red", "ivh_con_cloaca", "ivh_con_gas_red",
    "ivh_piso_adecuado", "ivh_techo_adecuado",
    "ivh_sin_hacinamiento", "ivh_con_empleo", "ivh_con_educacion_univ"
]
gdf["IVH"] = 1 - gdf[VARS_IVH].mean(axis=1)
```

### 2.3 Revisión de quintiles

**Problema**: `pd.qcut()` con `duplicates="drop"` puede generar menos de 5 categorías cuando hay muchos valores iguales, y los cortes automáticos no son intuitivos para comunicar los resultados.

**Corrección**: Explorar dos opciones y elegir la más adecuada para el análisis:
- **Opción A (mantener pd.qcut)**: Ajustar labels a `["Muy Baja", "Baja", "Media", "Alta", "Muy Alta"]` y documentar los cortes exactos en una tabla.
- **Opción B (Natural Breaks / Jenks)**: Usar `mapclassify.NaturalBreaks(y=gdf["IVH"], k=5)` para cortes que respeten la distribución real de los datos.

**Recomendación**: Natural Breaks (Jenks) es más apropiado para análisis geoespacial porque respeta los "saltos naturales" en la distribución. Requiere `pip install mapclassify`.

---

## Fase 3 — Capas espaciales (`04_mapas_estaticos.py` + `05_mapa_interactivo.py`)

### 3.1 Eliminar hipódromo, autódromo y aeropuerto

**Problema**: Son radios censales con superficies grandes y pocas/ninguna vivienda. Distorsionan los mapas visualmente y el cálculo de quintiles.

**Acción**: En `02_join_espacial.py` o `03_calculo_indicadores.py`, filtrar estos radios antes del cálculo del IVH. Identificarlos por:
- Criterio A: radios con `h14_total == 0` o muy bajo (< 10 viviendas)
- Criterio B: identificar por código de radio o nombre de fracción/radio censales específicas

```python
# Filtrar radios sin viviendas o con muy pocas
gdf = gdf[gdf["h14_total"] >= 10]
```

### 3.2 Agregar capas de contexto (avenidas, vías de tren, cementerios)

**Fuente**: OpenStreetMap vía librería `osmnx`.

**Capas a agregar**:
- **Avenidas principales**: `ox.graph_from_place("Buenos Aires, Argentina", network_type="drive")` filtrado por tipo "primary", "secondary"
- **Vías de tren**: `ox.geometries_from_place(place, tags={"railway": True})`
- **Cementerios**: `ox.geometries_from_place(place, tags={"landuse": "cemetery"})`

**Integración**:
- En `04_mapas_estaticos.py`: agregar estas capas como overlays en el mapa del IVH final
- En `05_mapa_interactivo.py`: agregar como `FeatureGroup` opcionales en Folium

```python
# Script auxiliar o dentro del 04/05
import osmnx as ox
place = "Ciudad Autónoma de Buenos Aires, Argentina"
railways = ox.geometries_from_place(place, tags={"railway": ["rail", "subway"]})
cemeteries = ox.geometries_from_place(place, tags={"landuse": "cemetery"})
# Para avenidas, filtrar red vial por tipo
```

---

## Archivos críticos a modificar

| Archivo | Cambios |
|---------|---------|
| `03_scripts/01_descarga_y_limpieza.py` | Variables positivas, gas de red, educación binaria |
| `03_scripts/02_join_espacial.py` | (Sin cambios, o agregar filtro de radios vacíos) |
| `03_scripts/03_calculo_indicadores.py` | Correlación NBI, nuevo IVH, revisión quintiles |
| `03_scripts/04_mapas_estaticos.py` | Capas OSM, eliminar radios grandes, ajustar títulos |
| `03_scripts/05_mapa_interactivo.py` | Capas OSM como FeatureGroups, tooltips actualizados |

---

## Verificación (cómo probar los cambios)

1. Correr `01_descarga_y_limpieza.py` y verificar que `datos_censo_CABA.csv` tenga las nuevas columnas `ivh_con_*` con valores entre 0 y 1 (deben estar mayoritariamente cerca de 1 para agua/cloaca/gas en CABA).
2. Correr `03_calculo_indicadores.py` y revisar el heatmap de correlación exportado — verificar que NBI tenga r > 0.6 con varias variables.
3. Verificar que el IVH final tenga la distribución esperada (radios de villas/sur CABA deben tener IVH alto).
4. Revisar el mapa interactivo HTML: deben verse las capas de tren/cementerios y no debe aparece el hipódromo/autódromo como polígonos distorsionantes.

---

## Dependencias nuevas a instalar

```bash
pip install osmnx mapclassify seaborn
```
