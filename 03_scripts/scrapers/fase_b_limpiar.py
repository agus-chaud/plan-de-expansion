"""
Fase B: Limpieza, normalización y creación de GeoDataFrame.

Pasos:
1. Leer supermercados_CABA.csv
2. Validar coordenadas (eliminar nulos y puntos fuera de CABA)
3. Crear GeoDataFrame con geometría Point en WGS84 (EPSG:4326)
4. Reproyectar a POSGAR 2007 Faja 3 (EPSG:5346) — CRS de los radios censales del IVH
5. Guardar como GeoPackage: supermercados_CABA.gpkg
6. Imprimir resumen
"""

from pathlib import Path

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

BASE_DIR = Path(__file__).parent.parent.parent
INPUT_CSV = BASE_DIR / "02_datos_procesados" / "supermercados" / "supermercados_CABA.csv"
OUTPUT_GPKG = BASE_DIR / "02_datos_procesados" / "supermercados" / "supermercados_CABA.gpkg"

# Bounding box de CABA (WGS84)
LAT_MIN = -34.70
LAT_MAX = -34.52
LON_MIN = -58.53
LON_MAX = -58.33

CRS_WGS84 = "EPSG:4326"
CRS_POSGAR = "EPSG:5346"  # POSGAR 2007 / Argentina Faja 3


def limpiar_coordenada(val) -> float | None:
    """Convierte a float o retorna None si el valor no es parseable o está vacío."""
    if val is None or str(val).strip() in ("", "None"):
        return None
    try:
        f = float(val)
        return f if f != 0.0 else None
    except (ValueError, TypeError):
        return None


def main():
    print("[INFO] Leyendo CSV unificado...")
    df = pd.read_csv(INPUT_CSV, encoding="utf-8")
    total_original = len(df)
    print(f"[INFO] Filas totales: {total_original}")
    print(f"[INFO] Columnas: {list(df.columns)}")

    # --- Paso 2: Validar coordenadas ---
    df["lat"] = df["lat"].apply(limpiar_coordenada)
    df["lon"] = df["lon"].apply(limpiar_coordenada)

    # Filas con coordenadas nulas
    mask_nulos = df["lat"].isna() | df["lon"].isna()
    n_nulos = mask_nulos.sum()
    if n_nulos > 0:
        print(f"[WARN] Descartadas {n_nulos} filas por lat/lon nulos:")
        print(df[mask_nulos][["marca", "nombre", "direccion"]].to_string(index=False))
    df = df[~mask_nulos].copy()

    # Filas fuera del bounding box de CABA
    mask_bbox = (
        (df["lat"] < LAT_MIN) | (df["lat"] > LAT_MAX) |
        (df["lon"] < LON_MIN) | (df["lon"] > LON_MAX)
    )
    n_bbox = mask_bbox.sum()
    if n_bbox > 0:
        print(f"[WARN] Descartadas {n_bbox} filas fuera del bounding box de CABA:")
        print(df[mask_bbox][["marca", "nombre", "direccion", "lat", "lon"]].to_string(index=False))
    df = df[~mask_bbox].copy()

    print(f"\n[INFO] Filas válidas tras limpieza: {len(df)}")
    print(f"[INFO] Total descartadas: {total_original - len(df)} "
          f"({n_nulos} nulos + {n_bbox} fuera de bbox)")

    # --- Paso 3: Crear GeoDataFrame en WGS84 ---
    geometrias = [Point(row["lon"], row["lat"]) for _, row in df.iterrows()]
    gdf = gpd.GeoDataFrame(df, geometry=geometrias, crs=CRS_WGS84)
    print(f"\n[INFO] GeoDataFrame creado — CRS: {gdf.crs}")

    # --- Paso 4: Reproyectar a POSGAR 2007 Faja 3 ---
    gdf_posgar = gdf.to_crs(CRS_POSGAR)
    print(f"[INFO] Reproyectado a {gdf_posgar.crs.name} ({CRS_POSGAR})")

    # --- Paso 5: Guardar GeoPackage ---
    OUTPUT_GPKG.parent.mkdir(parents=True, exist_ok=True)
    gdf_posgar.to_file(OUTPUT_GPKG, driver="GPKG", layer="supermercados")
    print(f"\n[OK] GeoPackage guardado en: {OUTPUT_GPKG}")

    # --- Paso 6: Resumen ---
    print("\n" + "=" * 50)
    print("RESUMEN FINAL")
    print("=" * 50)
    print(f"Total sucursales válidas: {len(gdf_posgar)}")
    print(f"CRS final: {gdf_posgar.crs.name} ({CRS_POSGAR})")
    print(f"\nSucursales por marca:")
    conteo = gdf_posgar["marca"].value_counts()
    for marca, n in conteo.items():
        print(f"  {marca}: {n}")
    print(f"\nDescartadas por coords nulas: {n_nulos}")
    print(f"Descartadas por bbox inválido: {n_bbox}")
    print(f"Total descartadas: {total_original - len(gdf_posgar)}")
    print()

    # Verificar que el gpkg se puede releer
    gdf_check = gpd.read_file(OUTPUT_GPKG, layer="supermercados")
    print(f"[OK] Verificación GeoPackage: {len(gdf_check)} features, CRS: {gdf_check.crs.name}")


if __name__ == "__main__":
    main()
