"""
01_descarga_y_limpieza.py
=========================
Fase 1: Preparar cartografia de CABA y cargar CSV de REDATAM.

PREREQUISITO MANUAL (antes de ejecutar este script):
  El usuario debe ejecutar las 5 queries .rpf en RedatamX:
    - redatam_exports/queries_redatam/hogares_hacinamiento.rpf
    - redatam_exports/queries_redatam/hogares_nbi.rpf
    - redatam_exports/queries_redatam/educacion_por_radio.rpf
    - redatam_exports/queries_redatam/viviendas_por_radio.rpf
    - redatam_exports/queries_redatam/poblacion_basica.rpf
  Exportar los resultados como CSV en: redatam_exports/csv_output/

Salida:
  - 02_datos_procesados/radios_CABA.gpkg   (geometrias de CABA limpias)
  - 02_datos_procesados/indicadores_por_radio.csv  (si los CSV de REDATAM existen)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import geopandas as gpd
import pandas as pd
from utils import (
    RADIOS_RAW, PROCESADOS, CSV_OUTPUT, CRS_FOLIUM, CRS_ORIGINAL,
    SHAPEFILE_LINK_COL, REDATAM_JOIN_COL, LINK_DUPLICADOS, VARS_IVH,
    REDATAM_QUERIES,
)


def cargar_radios_caba() -> gpd.GeoDataFrame:
    """Cargar shapefile de radios de CABA y resolver duplicados de LINK."""
    shp_path = RADIOS_RAW / "cabaxrdatos.shp"
    print(f"Leyendo shapefile: {shp_path}")

    gdf = gpd.read_file(shp_path)
    print(f"CRS original: {gdf.crs}")
    print(f"Registros totales: {len(gdf)}")

    # Verificar duplicados de LINK
    duplicados = gdf[gdf[SHAPEFILE_LINK_COL].isin(LINK_DUPLICADOS)]
    if not duplicados.empty:
        print(f"Duplicados LINK encontrados: {duplicados[SHAPEFILE_LINK_COL].tolist()}")
        # Disolver por LINK: unir geometrias de fragmentos del mismo radio
        gdf = gdf.dissolve(by=SHAPEFILE_LINK_COL, aggfunc={
            'VARONES': 'sum', 'MUJERES': 'sum', 'TOT_POB': 'sum',
            'HOGARES': 'sum', 'VIV_PART': 'sum', 'VIV_PART_H': 'sum',
            'PROV': 'first', 'DEPTO': 'first', 'FRAC': 'first',
            'RADIO': 'first', 'TIPO': 'first'
        }).reset_index()
        print(f"Registros tras dissolve: {len(gdf)}")

    # Reproyectar a WGS84 para compatibilidad con folium
    gdf = gdf.to_crs(CRS_FOLIUM)
    print(f"CRS final: {gdf.crs}")
    return gdf


def verificar_csv_redatam() -> bool:
    """Verificar si los CSV de REDATAM ya fueron exportados."""
    csvs = list(CSV_OUTPUT.glob("*.csv"))
    if not csvs:
        print("\n" + "=" * 60)
        print("BLOQUEADOR: No se encontraron CSV en csv_output/")
        print("Ejecutar en RedatamX los siguientes archivos .rpf:")
        for rpf in REDATAM_QUERIES.glob("*.rpf"):
            print(f"  - {rpf.name}")
        print(f"\nExportar resultados a: {CSV_OUTPUT}")
        print("=" * 60 + "\n")
        return False
    print(f"CSV de REDATAM encontrados: {[c.name for c in csvs]}")
    return True


def cargar_csv_redatam(nombre_csv: str) -> pd.DataFrame:
    """Cargar un CSV exportado de RedatamX. Ajustar encoding si falla."""
    ruta = CSV_OUTPUT / nombre_csv
    for enc in ["utf-8", "latin-1", "utf-8-sig"]:
        try:
            df = pd.read_csv(ruta, encoding=enc)
            df[REDATAM_JOIN_COL] = df[REDATAM_JOIN_COL].astype(str).str.zfill(9)
            df = df[df[REDATAM_JOIN_COL].str.startswith("02")]  # Solo CABA
            print(f"CSV '{nombre_csv}' cargado ({len(df)} radios, encoding: {enc})")
            return df
        except (UnicodeDecodeError, KeyError):
            continue
    raise ValueError(f"No se pudo cargar {nombre_csv} con ningun encoding conocido")


def calcular_indicadores(df_hog: pd.DataFrame, df_edu: pd.DataFrame) -> pd.DataFrame:
    """
    Calcular los 7 indicadores del IVH a partir de los CSV de REDATAM.

    NOTA: Los nombres exactos de columnas dependen del formato de exportacion de RedatamX.
    Revisar los CSV exportados y ajustar los nombres de columna si es necesario.
    Los comentarios indican la variable REDATAM correspondiente.
    """
    result = pd.DataFrame()
    result[REDATAM_JOIN_COL] = df_hog[REDATAM_JOIN_COL]

    total_hog = df_hog["TOTAL_HOGARES"]  # TODO: ajustar nombre de columna real

    # pct_hacinamiento: HOGAR.H20_HACINA == 6 ("Mas de 3 personas por cuarto")
    # TODO: ajustar nombre de columna tras ver el CSV real
    result["pct_hacinamiento"] = df_hog.get("HACIN_6", 0) / total_hog * 100

    # pct_piso_tierra: HOGAR.H10 == 3 ("Tierra o ladrillo suelto")
    result["pct_piso_tierra"] = df_hog.get("H10_3", 0) / total_hog * 100

    # pct_sin_agua_red: HOGAR.H14 != 1 (1 = "Red publica agua corriente")
    result["pct_sin_agua_red"] = (1 - df_hog.get("H14_1", 0) / total_hog) * 100

    # pct_sin_cloaca: HOGAR.H18 != 1 (1 = "A red publica cloaca")
    result["pct_sin_cloaca"] = (1 - df_hog.get("H18_1", 0) / total_hog) * 100

    # pct_sin_gas_red: HOGAR.H19 != 2 (2 = "Gas de red")
    result["pct_sin_gas_red"] = (1 - df_hog.get("H19_2", 0) / total_hog) * 100

    # pct_sin_secundario: PERSONA.NIVEL_ED < secundario completo, edad >= 25
    # TODO: ajustar tras ver el CSV de educacion_por_radio
    total_25 = df_edu.get("POB_25MAS", 1)
    result["pct_sin_secundario"] = (1 - df_edu.get("SECUND_COMPLETO", 0) / total_25) * 100

    return result


def main():
    print("=== FASE 1: Preparacion cartografia + carga de datos ===\n")

    # 1. Cargar y limpiar radios de CABA
    radios_caba = cargar_radios_caba()
    salida_gpkg = PROCESADOS / "radios_CABA.gpkg"
    radios_caba.to_file(salida_gpkg, driver="GPKG")
    print(f"\nGuardado: {salida_gpkg}")

    # 2. Verificar CSV de REDATAM
    if not verificar_csv_redatam():
        print("Ejecutar las queries en RedatamX y volver a ejecutar este script.")
        return

    # 3. Cargar y calcular indicadores
    # TODO: reemplazar nombres de CSV con los reales exportados por RedatamX
    df_hog = cargar_csv_redatam("hogares_hacinamiento.csv")
    df_edu = cargar_csv_redatam("educacion_por_radio.csv")
    df_indicadores = calcular_indicadores(df_hog, df_edu)

    salida_csv = PROCESADOS / "indicadores_por_radio.csv"
    df_indicadores.to_csv(salida_csv, index=False)
    print(f"\nGuardado: {salida_csv}")
    print(f"Indicadores calculados para {len(df_indicadores)} radios")
    print("\nFase 1 completada.")


if __name__ == "__main__":
    main()
