# Data Mapping — Análisis Geoespacial CABA Censo 2022

Documento de referencia generado en la Parte 3.1 (exploración e inspección de archivos).
Describe qué archivo usar para cada indicador, cómo hacer los joins y qué pasos manuales requiere el usuario.

---

## 1. Cartografía: Shapefile de Radios Censales

### Archivo elegido

| Campo | Valor |
|---|---|
| Archivo | `01_datos_raw/cartografia/MGN_2022_radios/cabaxrdatos.shp` |
| Registros | 3.555 radios censales |
| Jurisdicción | CABA (todos con `PROV = "02"`) |
| CRS original | EPSG:22183 (Gauss-Krüger faja 3, Argentina, metros) |
| CRS de trabajo | EPSG:4326 (WGS84, grados — requerido por folium) |
| Columna de join | `LINK` (9 caracteres, ej: `020130302`) |

### Columnas disponibles en el shapefile

| Columna | Descripción |
|---|---|
| `LINK` | Código geográfico del radio (clave de join con REDATAM) |
| `PROV` | Código de provincia (siempre `"02"` en este shapefile) |
| `DEPTO` | Código de departamento/comuna |
| `FRAC` | Fracción censal |
| `RADIO` | Número de radio dentro de la fracción |
| `TIPO` | Tipo de radio censal |
| `VARONES` | Total de varones (datos tabulares incluidos) |
| `MUJERES` | Total de mujeres |
| `TOT_POB` | Población total por radio |
| `HOGARES` | Total de hogares |
| `VIV_PART` | Total de viviendas particulares |
| `VIV_PART_H` | Viviendas particulares habitadas |
| `AREA` | Área del polígono (en unidades del CRS original) |
| `PERIMETER` | Perímetro del polígono |

### Advertencia: LINK duplicados

Hay 2 pares de radios con LINK repetido (`020130104` y `020121607`). Cada par tiene geometrías distintas porque el radio quedó dividido en fragmentos al digitalizar. **Estrategia aplicada en el script**: `dissolve(by="LINK")` — une las geometrías y suma las columnas numéricas. Resultado final: 3.553 radios únicos.

### Archivos ZIP — no usar

Los ZIPs en la misma carpeta son duplicados del shapefile ya extraído:
- `Codgeo_CABA_con_datos.zip` → mismo que `cabaxrdatos.shp`
- `Codgeo_Pais_x_prov_datos.zip` → shapefile provincial (24 registros, no útil)
- `radios_censales_MGN2022.zip` → radios nacionales en EPSG:3857, requiere filtrar CABA — no tiene ventaja sobre el archivo ya disponible

---

## 2. Datos Censales: Fuentes por Indicador

### Hallazgo crítico: granularidad de los XLSX

Los 13 XLSX de `cuadros_CABA/` tienen granularidad máxima de **COMUNA** (15 comunas de CABA). **No sirven para análisis a nivel de radio censal.**

La fuente correcta para radio censal es **REDATAM con Base_VP** (`redatam_exports/Base_VP/`).

### Mapeo: Indicador → Fuente REDATAM

| Indicador IVH | Columna en script | Archivo RPF | Variable REDATAM | Categoría relevante | Fórmula |
|---|---|---|---|---|---|
| Hacinamiento crítico | `pct_hacinamiento` | `hogares_hacinamiento.rpf` | `HOGAR.H20_HACINA` | cat 6 = "Más de 3,00 p/c" | hogares cat6 / total hogares × 100 |
| Piso de tierra | `pct_piso_tierra` | `hogares_hacinamiento.rpf` | `HOGAR.H10` | cat 3 = "Tierra o ladrillo suelto" | hogares cat3 / total hogares × 100 |
| Sin agua de red | `pct_sin_agua_red` | *(agregar a rpf)* | `HOGAR.H14` | cat ≠ 1 (1 = "Red pública") | (1 − hogares cat1 / total) × 100 |
| Sin cloacas | `pct_sin_cloaca` | *(agregar a rpf)* | `HOGAR.H18` | cat ≠ 1 (1 = "A red pública cloaca") | (1 − hogares cat1 / total) × 100 |
| Sin gas de red | `ivh_sin_gas_red` | *(agregar a rpf)* | `HOGAR.H19` | cat = "Gas de red" (columna directa `h19_gas_red`) | `1 - safe_div(h19_gas_red, h19_total)` |
| Sin universitario completo | `ivh_baja_educacion_univ` | `educacion_por_radio.rpf` | `PERSONA.P08` | nivel = universitario completo (`p08_universitario_comp`) | `1 - safe_div(p08_universitario_comp, p08_total)` |
| NBI total *(validación externa)* | `ivh_nbi` | `hogares_nbi.rpf` | `HOGAR.NBI_TOT` | cat 1 = "Sí tiene NBI" | hogares NBI / total hogares — **no integra el IVH, solo validación** |

### Dimensiones del NBI disponibles en `hogares_nbi.rpf`

| Variable | Descripción |
|---|---|
| `HOGAR.NBI_HAC` | NBI por hacinamiento |
| `HOGAR.NBI_VIV` | NBI por vivienda inconveniente |
| `HOGAR.NBI_SAN` | NBI por condiciones sanitarias |
| `HOGAR.NBI_ESC` | NBI por escolaridad |
| `HOGAR.NBI_SUB` | NBI por capacidad de subsistencia |
| `HOGAR.NBI_TOT` | NBI total (al menos una dimensión) |

---

## 3. Clave de Join: CSV REDATAM ↔ Shapefile

```
CSV de REDATAM:    columna  REDCODEN   (ej: "020130302")
Shapefile CABA:    columna  LINK       (ej: "020130302")
```

Ambas son strings de 9 caracteres con el mismo formato. El join se hace con:

```python
resultado = radios.merge(df_indicadores, left_on="LINK", right_on="REDCODEN", how="left")
```

**Nota sobre `scripts_redatam.py`**: el script existente en `queries_redatam/` referencia `cod_indec` como nombre de columna del shapefile — eso es incorrecto. La columna real se llama `LINK`. El script `01_descarga_y_limpieza.py` ya usa la constante correcta `SHAPEFILE_LINK_COL = "LINK"` definida en `utils.py`.

---

## 4. Pasos Manuales en RedatamX (BLOQUEADOR para Parte 3.2)

Antes de ejecutar `01_descarga_y_limpieza.py` con datos reales, el usuario debe completar estos pasos en **RedatamX**:

### Paso 1 — Abrir RedatamX con Base_VP

1. Abrir RedatamX (portable, no requiere instalación)
2. Ir a **Archivo → Abrir base de datos**
3. Navegar a: `01_datos_raw/censo_2022/redatam_exports/Base_VP/`
4. Seleccionar el archivo `cpv2022.rxdb`

### Paso 2 — Ejecutar cada query .rpf

Para cada uno de los 5 archivos en `queries_redatam/`:

1. Ir a **Programa → Abrir** (o equivalente en RedatamX)
2. Seleccionar el archivo `.rpf`
3. Hacer clic en **Ejecutar** (o Run)
4. Cuando termine, **exportar como CSV**

### Paso 3 — Guardar los CSV

Guardar cada CSV exportado en:
```
01_datos_raw/censo_2022/redatam_exports/csv_output/
```

Nombres de archivo sugeridos (mantener el mismo nombre que el .rpf):
- `hogares_hacinamiento.csv`
- `hogares_nbi.csv`
- `educacion_por_radio.csv`
- `viviendas_por_radio.csv`
- `poblacion_basica.csv`

### Paso 4 — Verificar que los CSV tienen la columna REDCODEN

Antes de ejecutar los scripts Python, abrir uno de los CSV y confirmar que:
- Existe una columna llamada `REDCODEN` (o similar — puede variar según la versión de RedatamX)
- Los valores son strings de 9 dígitos tipo `020130302`
- Filtrar solo registros que empiezan con `"02"` (CABA)

Si la columna de código geográfico tiene otro nombre, actualizar la constante `REDATAM_JOIN_COL` en `utils.py`.

---

## 5. XLSX de Cuadros CABA — Uso para Validación

Aunque no sirven para el análisis principal (granularidad de comuna), los XLSX pueden usarse para **validar los resultados a nivel de comuna** contra los datos a nivel de radio una vez agregados.

### Archivos y su contenido

| Archivo | Variable censal | Indicador IVH relacionado | Tipo |
|---|---|---|---|
| `hogares_c1_1.xlsx` | Material de pisos y techo (`H10`, `H11-H12`) | `pct_piso_tierra` | Multi-hoja (1 hoja por comuna) |
| `hogares_c2_1.xlsx` | Provisión y procedencia del agua (`H13`, `H14`) | `pct_sin_agua_red` | Multi-hoja |
| `hogares_c3_1.xlsx` | Desagüe del inodoro + ubicación baño (`H18`, `H15`) | `pct_sin_cloaca` | Multi-hoja |
| `hogares_c4_1.xlsx` | Combustible para cocinar (`H19`) | `pct_sin_gas_red` | Hoja única |
| `hogares_c5_1.xlsx` | Cantidad habitaciones y baños (`H20`, `H16`) | Auxiliar hacinamiento | Multi-hoja |
| `hogares_c6_1.xlsx` | Régimen de tenencia (`H22`, `H23`) | No en IVH | Hoja única |
| `hogares_c7_1.xlsx` | Acceso a tecnología (`H24A-C`) | No en IVH | Multi-hoja |
| `vivienda_c1_1.xlsx` | Tipo vivienda × condición ocupación | Auxiliar NBI | Hoja única |
| `vivienda_c2_1.xlsx` | Viviendas por cantidad de hogares | Auxiliar | Hoja única |
| `vivienda_c3_1.xlsx` | Tipo de vivienda particular | Auxiliar NBI (casilla) | Hoja única |
| `educacion_c1_1.xlsx` | Asistencia escolar × sexo × edad | Auxiliar NBI escolaridad | Multi-hoja |
| `educacion_c2_1.xlsx` | Nivel al que asiste × sexo × edad | Auxiliar | Multi-hoja |
| `educacion_c3_1.xlsx` | Máximo nivel alcanzado + completitud | `pct_sin_secundario` | Multi-hoja |

### Cómo leer los XLSX en Python

```python
import pandas as pd

# Tipo A — hoja única (skiprows=0, código en columna 0)
df = pd.read_excel("hogares_c4_1.xlsx")
# Columna 0: código ("02" = CABA total, "02007" a "02105" = comunas)
# Columna 1: nombre de la comuna

# Tipo B — multi-hoja (una hoja por comuna)
xls = pd.ExcelFile("hogares_c3_1.xlsx")
# xls.sheet_names → ["Caratula", "Índice", "Cuadro 3.1", "Cuadro 3.1.1", ..., "Cuadro 3.1.15"]
# Cuadro 3.1 = CABA total; Cuadro 3.1.1 = Comuna 1; ...; Cuadro 3.1.15 = Comuna 15
df_caba = pd.read_excel("hogares_c3_1.xlsx", sheet_name="Cuadro 3.1")
df_c1   = pd.read_excel("hogares_c3_1.xlsx", sheet_name="Cuadro 3.1.1")
```

---

## 6. Estado al Cierre de Parte 3.1

| Entregable | Estado |
|---|---|
| `03_scripts/utils.py` | ✅ Actualizado con rutas y constantes reales |
| `03_scripts/01_descarga_y_limpieza.py` | ✅ Lógica real implementada (TODOs menores pendientes) |
| `data_mapping.md` | ✅ Este documento |
| `02_datos_procesados/radios_CABA.gpkg` | ⏳ Se genera al ejecutar el script |
| `02_datos_procesados/indicadores_por_radio.csv` | 🔴 Requiere CSV de REDATAM primero |
| `redatam_exports/csv_output/*.csv` | 🔴 **Acción manual requerida** — ejecutar queries en RedatamX |

### Próximo paso: Parte 3.2

Una vez que el usuario ejecute las queries en RedatamX y exporte los CSV:
1. Inspeccionar los CSV para ver los nombres exactos de columnas
2. Completar los TODOs en `01_descarga_y_limpieza.py` (`calcular_indicadores`)
3. Ejecutar el script y verificar el `.gpkg` resultante
4. Ejecutar `02_join_espacial.py`
