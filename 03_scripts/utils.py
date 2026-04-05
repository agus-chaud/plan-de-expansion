"""
utils.py — Constantes de rutas del proyecto.
Importar desde cualquier script: from utils import RAW, PROCESADOS, ...
"""
from pathlib import Path

# Raiz del proyecto (dos niveles arriba de este archivo)
ROOT = Path(__file__).parent.parent

# Directorios principales
RAW = ROOT / "01_datos_raw"
PROCESADOS = ROOT / "02_datos_procesados"
SCRIPTS = ROOT / "03_scripts"
MAPAS = ROOT / "04_mapas"
INFORME = ROOT / "05_informe"

# Cartografia
RADIOS_RAW = RAW / "cartografia" / "MGN_2022_radios"
COMUNAS_RAW = RAW / "cartografia" / "comunas_CABA"
LIMITES_RAW = RAW / "cartografia" / "limites_CABA"

# Datos censales
CUADROS_CABA = RAW / "censo_2022" / "cuadros_CABA"
REDATAM_EXPORTS = RAW / "censo_2022" / "redatam_exports"
REDATAM_QUERIES = REDATAM_EXPORTS / "queries_redatam"
CSV_OUTPUT = REDATAM_EXPORTS / "csv_output"

# Datos procesados
RADIOS_GPKG = PROCESADOS / "radios_CABA.gpkg"
INDICADORES_CSV = PROCESADOS / "indicadores_por_radio.csv"
RESULTADO_GPKG = PROCESADOS / "radios_CABA_indicadores.gpkg"

# Mapas
MAPAS_ESTATICOS = MAPAS / "estaticos"
MAPAS_INTERACTIVOS = MAPAS / "interactivos"

# Configuracion de CRS
CRS_ORIGINAL = "EPSG:22183"   # Gauss-Kruger faja 3 (sistema oficial Argentina, metros)
CRS_PROCESAMIENTO = "EPSG:22184"  # Posgar 2007 / Argentina zona 4 (metros, para analisis)
CRS_FOLIUM = "EPSG:4326"      # WGS84 (grados, para folium)

# Configuracion general
CABA_LINK_PREFIX = "02"       # Prefijo del codigo de jurisdiccion CABA en el MGN
CABA_CENTER = [-34.6037, -58.3816]
ZOOM_START = 12

# Columnas de join entre fuentes
SHAPEFILE_LINK_COL = "LINK"       # Columna de join en el shapefile cabaxrdatos.shp
REDATAM_JOIN_COL = "REDCODEN"     # Columna de join en los CSV exportados de RedatamX

# Radios con LINK duplicado en el shapefile (fragmentos del mismo radio con geometrias distintas)
# Estrategia: disolver por LINK para obtener un poligono unico por radio
LINK_DUPLICADOS = ["020130104", "020121607"]

# Variables del IVH (Indice de Vulnerabilidad Habitacional)
VARS_IVH = [
    "pct_hacinamiento",
    "pct_sin_agua_red",
    "pct_sin_cloaca",
    "pct_piso_tierra",
    "pct_sin_secundario",
    "pct_sin_gas_red",
]
