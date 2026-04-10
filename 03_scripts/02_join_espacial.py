"""
02_join_espacial.py
===================
Fase 3.3: Unir la tabla de indicadores IVH al shapefile de radios censales CABA.

Prerequisito: Haber ejecutado 01_descarga_y_limpieza.py (genera datos_censo_CABA.csv)

Entradas:
  - 01_datos_raw/cartografia/MGN_2022_radios/cabaxrdatos.shp  (geometrias)
  - 02_datos_procesados/datos_censo_CABA.csv                  (indicadores IVH, 3820 filas x 92 cols)

Salida:
  - 02_datos_procesados/radios_CABA_ivh.gpkg

Nota sobre el join:
  El shapefile usa codigos DEPTO secuenciales (001-015 para las 15 comunas de CABA),
  mientras que el CSV usa el codigo INDEC completo donde DEPTO = sequencial * 7
  (ej: DEPTO 1 del shapefile -> DEPTO 007 en CSV, DEPTO 13 -> 091, etc.)
  La transformacion es: codigo_csv = '02' + str(int(DEPTO)*7).zfill(3) + FRAC + RADIO
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import geopandas as gpd
import pandas as pd
from utils import RADIOS_RAW, PROCESADOS, CABA_LINK_PREFIX


def build_codigo_indec(row):
    """Convierte los componentes del shapefile al codigo INDEC del CSV."""
    depto_indec = str(int(row["DEPTO"]) * 7).zfill(3)
    return "02" + depto_indec + row["FRAC"].zfill(2) + row["RADIO"].zfill(2)


def main():
    print("=== FASE 3.3: Join espacial ===")

    # --- Rutas ---
    shp_path = RADIOS_RAW / "cabaxrdatos.shp"
    csv_path = PROCESADOS / "datos_censo_CABA.csv"
    output_path = PROCESADOS / "radios_CABA_ivh.gpkg"

    # --- Cargar shapefile y filtrar CABA ---
    print(f"Cargando shapefile: {shp_path}")
    radios = gpd.read_file(shp_path)
    radios = radios[radios["LINK"].str.startswith(CABA_LINK_PREFIX)].copy()
    print(f"  Radios CABA en shapefile: {len(radios)}")
    print(f"  CRS original: {radios.crs}")

    # --- Construir clave de join compatible con el CSV ---
    # El shapefile tiene DEPTO secuencial (001-015), el CSV usa DEPTO INDEC (multiplo de 7)
    radios["codigo_join"] = radios.apply(build_codigo_indec, axis=1)

    # --- Cargar CSV de indicadores IVH ---
    print(f"Cargando CSV: {csv_path}")
    df = pd.read_csv(csv_path, dtype={"codigo": str})
    print(f"  Filas en CSV: {len(df)}  |  Columnas: {len(df.columns)}")

    # --- Join ---
    resultado = radios.merge(df, left_on="codigo_join", right_on="codigo", how="left")

    # --- Verificar cobertura ---
    sin_datos = resultado["codigo"].isna().sum()
    total = len(resultado)
    if sin_datos > 0:
        print(f"ADVERTENCIA: {sin_datos}/{total} radios sin datos en el CSV "
              f"(probablemente zonas institucionales sin poblacion)")
    else:
        print("Join completo: todos los radios tienen datos del CSV")

    # --- Limpiar columna auxiliar ---
    resultado = resultado.drop(columns=["codigo_join"])

    # --- Guardar resultado ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    resultado.to_file(output_path, driver="GPKG")

    # --- Reporte final ---
    print(f"\n--- Resultado guardado: {output_path} ---")
    print(f"  CRS: {resultado.crs}")
    print(f"  Filas (radios): {len(resultado)}")
    print(f"  Tipo de geometria: {resultado.geom_type.unique().tolist()}")
    print(f"  Columnas totales: {len(resultado.columns)}")
    print("Fase 3.3 completada.")


if __name__ == "__main__":
    main()
