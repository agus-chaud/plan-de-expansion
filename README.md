# Análisis Geoespacial de Calidad de Vida en CABA — Censo 2022

Análisis de la distribución espacial de indicadores de calidad de vida en la Ciudad Autónoma de Buenos Aires (CABA) a nivel de radio censal, utilizando datos del Censo Nacional de Población, Hogares y Viviendas 2022 del INDEC. El proyecto calcula un Índice de Vulnerabilidad Habitacional (IVH) compuesto y lo visualiza mediante mapas coropléticos estáticos e interactivos.

---

## Estructura del proyecto

```
Plan de expansion/
├── 01_datos_raw/                        # Datos originales sin modificar
│   ├── censo_2022/
│   │   ├── cuadros_CABA/               # XLS/XLSX descargados de INDEC (vivienda, hogares, educación)
│   │   └── redatam_exports/            # CSV exportados desde REDATAM Online
│   └── cartografia/
│       ├── MGN_2022_radios/            # Shapefile de radios censales (Marco Geoestadístico Nacional)
│       ├── comunas_CABA/               # Shapefile de límites de comunas de CABA
│       └── limites_CABA/               # Shapefile del límite exterior de CABA
├── 02_datos_procesados/                 # Datos limpios y enriquecidos (generados por scripts)
├── 03_scripts/                          # Scripts Python en orden de ejecución
├── 04_mapas/
│   ├── estaticos/                       # Mapas PNG de salida
│   └── interactivos/                    # Mapas HTML interactivos
├── 05_informe/
│   └── figuras/                         # Figuras exportadas para el informe final
├── README.md
└── requirements.txt
```

---

## Descarga de datos (PASO FUNDAMENTAL — hacer primero)

Antes de ejecutar cualquier script, descargá todos los insumos necesarios manualmente.

### 1. Cartografia censal — Marco Geoestadístico Nacional 2022 (MGN)

- URL: https://www.indec.gob.ar/indec/web/Institucional-Indec-Codgeo
- Descargar el Marco Geoestadístico Nacional 2022 (shapefile de radios censales).
- Guardar y descomprimir en: `01_datos_raw/cartografia/MGN_2022_radios/`
- El archivo clave es `radios.shp` (junto con `.dbf`, `.shx`, `.prj`).

**Respaldo IGN** (si el link de INDEC no funciona):
- URL: https://www.ign.gob.ar/NuestrasActividades/InformacionGeoespacial/CapasSIG

### 2. Cuadros censales CABA

- URL: https://www.indec.gob.ar/indec/web/Nivel4-Tema-2-41-165
- Descargar los archivos XLS/XLSX correspondientes a CABA para las siguientes temáticas:
  - Viviendas (tipo y materiales)
  - Hogares (hacinamiento, servicios)
  - Educación (nivel de instrucción)
  - Servicios básicos (agua, cloacas, gas)
- Guardar en: `01_datos_raw/censo_2022/cuadros_CABA/`

### 3. REDATAM Online — datos a nivel radio censal

- URL: https://redatam.indec.gob.ar/
- Seleccionar: Censo 2022 → Ciudad Autónoma de Buenos Aires → nivel radio censal.
- Exportar las variables de interés como CSV.
- Guardar en: `01_datos_raw/censo_2022/redatam_exports/`

### 4. Comunas CABA

- URL: https://data.buenosaires.gob.ar/dataset/comunas
- Descargar el shapefile de comunas del portal de datos abiertos de GCBA.
- Guardar en: `01_datos_raw/cartografia/comunas_CABA/`

---

## Instalación del entorno Python

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

> En Linux/macOS: `.venv/bin/activate`

---

## Ejecución de scripts (en orden)

Los scripts deben ejecutarse secuencialmente. Cada uno depende del output del anterior.

```bash
# 1. Descarga y limpieza de datos crudos
python 03_scripts/01_descarga_y_limpieza.py

# 2. Join espacial: une indicadores al shapefile de radios censales
python 03_scripts/02_join_espacial.py

# 3. Cálculo del IVH y normalización de indicadores
python 03_scripts/03_calculo_indicadores.py

# 4. Generación de mapas coropléticos estáticos (PNG)
python 03_scripts/04_mapas_estaticos.py

# 5. Generación del mapa interactivo (HTML con Folium/Plotly)
python 03_scripts/05_mapa_interactivo.py
```

| Script | Descripción |
|--------|-------------|
| `01_descarga_y_limpieza.py` | Filtra radios de CABA, limpia y normaliza los XLS del INDEC |
| `02_join_espacial.py` | Une los datos tabulares al shapefile por código de radio censal |
| `03_calculo_indicadores.py` | Calcula el IVH como promedio normalizado de los 7 indicadores |
| `04_mapas_estaticos.py` | Genera mapas PNG por indicador y para el IVH |
| `05_mapa_interactivo.py` | Genera `IVH_CABA.html` con capas interactivas y tooltips |

---

## Variables de calidad de vida analizadas

| Variable | Descripción |
|----------|-------------|
| Hacinamiento crítico | % de hogares con más de 3 personas por cuarto |
| Vivienda precaria | % de hogares en rancho, casilla, pieza de inquilinato u otro tipo precario |
| Piso de tierra | % de viviendas con piso de tierra o ladrillo suelto |
| Sin agua de red | % de hogares sin acceso a red pública de agua corriente |
| Sin red cloacal | % de hogares sin conexión a red cloacal |
| Sin gas de red | % de hogares sin acceso a red de gas natural |
| Sin secundario completo | % de población de 25 años o más sin secundario completo |
| **IVH** | **Índice de Vulnerabilidad Habitacional**: promedio normalizado (0–1) de las 7 variables anteriores |

> A mayor valor del IVH, mayor vulnerabilidad habitacional en ese radio censal.

---

## Entregables

| Producto | Ubicación |
|----------|-----------|
| Mapas coropléticos PNG (por indicador y IVH) | `04_mapas/estaticos/` |
| Mapa interactivo con capas y tooltips | `04_mapas/interactivos/IVH_CABA.html` |
| Informe final con análisis y conclusiones | `05_informe/informe_final.docx` |
| Figuras del informe (alta resolución) | `05_informe/figuras/` |
