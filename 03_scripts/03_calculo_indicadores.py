"""
03_calculo_indicadores.py
=========================
Fase 3: Calcular el Indice de Vulnerabilidad Habitacional (IVH).

Normaliza cada variable entre 0 y 1 (Min-Max) y promedia para obtener el IVH.
Mayor IVH = mayor vulnerabilidad.

Prerequisito: Haber ejecutado 02_join_espacial.py

Salida:
  - Actualiza 02_datos_procesados/radios_CABA_indicadores.gpkg con columna IVH
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import geopandas as gpd
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from utils import RESULTADO_GPKG, VARS_IVH


def calcular_ivh(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Normalizar variables y calcular el IVH."""
    # TODO: verificar que todas las variables de VARS_IVH existen en el GDF
    vars_presentes = [v for v in VARS_IVH if v in gdf.columns]
    if len(vars_presentes) < len(VARS_IVH):
        faltantes = set(VARS_IVH) - set(vars_presentes)
        print(f"ADVERTENCIA: faltan columnas: {faltantes}")

    scaler = MinMaxScaler()
    gdf[[f"{v}_norm" for v in vars_presentes]] = scaler.fit_transform(gdf[vars_presentes])
    gdf["IVH"] = gdf[[f"{v}_norm" for v in vars_presentes]].mean(axis=1)
    return gdf


def main():
    print("=== FASE 3: Calculo de IVH ===")
    gdf = gpd.read_file(RESULTADO_GPKG)
    gdf = calcular_ivh(gdf)
    print(f"IVH calculado. Rango: {gdf['IVH'].min():.3f} — {gdf['IVH'].max():.3f}")
    gdf.to_file(RESULTADO_GPKG, driver="GPKG")
    print("Fase 3 completada.")


if __name__ == "__main__":
    main()
