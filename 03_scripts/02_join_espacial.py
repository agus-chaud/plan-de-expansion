"""
02_join_espacial.py
===================
Fase 2: Unir la tabla de indicadores al GeoPackage de radios censales.

Prerequisito: Haber ejecutado 01_descarga_y_limpieza.py

Salida:
  - 02_datos_procesados/radios_CABA_indicadores.gpkg
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import geopandas as gpd
import pandas as pd
from utils import RADIOS_GPKG, INDICADORES_CSV, RESULTADO_GPKG


def main():
    print("=== FASE 2: Join espacial ===")

    # Cargar geometrias
    radios = gpd.read_file(RADIOS_GPKG)
    print(f"Radios cargados: {len(radios)}")

    # Cargar indicadores
    df = pd.read_csv(INDICADORES_CSV, dtype={"radio_id": str})
    print(f"Radios con datos: {len(df)}")

    # Join por codigo de radio
    resultado = radios.merge(df, left_on="LINK", right_on="radio_id", how="left")

    # Verificar cobertura
    sin_datos = resultado["radio_id"].isna().sum()
    if sin_datos > 0:
        print(f"ADVERTENCIA: {sin_datos} radios sin datos de indicadores")
    else:
        print("Join completo: todos los radios tienen datos")

    resultado.to_file(RESULTADO_GPKG, driver="GPKG")
    print(f"Guardado: {RESULTADO_GPKG}")
    print("Fase 2 completada.")


if __name__ == "__main__":
    main()
