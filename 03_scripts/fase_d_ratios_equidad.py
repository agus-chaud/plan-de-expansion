"""
Fase D — Análisis de Equidad Territorial: Supermercados vs IVH en CABA
=======================================================================
Calcula 4 ratios de equidad espacial entre clases IVH y acceso a supermercados.

Outputs:
    02_datos_procesados/supermercados/ratio1_supers_por_km2.csv
    02_datos_procesados/supermercados/ratio2_distancia_promedio.csv
    02_datos_procesados/supermercados/ratio3_marca_por_clase_ivh.csv
    02_datos_procesados/supermercados/ratio4_sin_cobertura.csv
    02_datos_procesados/radios_CABA_final.gpkg
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path
from scipy.spatial import cKDTree

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE = Path("C:/Users/Dell/Agus/2026/Plan de expansion")
RADIOS_PATH   = BASE / "02_datos_procesados/radios_CABA_con_supermercados.gpkg"
SUPERS_PATH   = BASE / "02_datos_procesados/supermercados/supermercados_CABA.gpkg"
OUT_DIR       = BASE / "02_datos_procesados/supermercados"
RADIOS_FINAL  = BASE / "02_datos_procesados/radios_CABA_final.gpkg"

OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
print("=" * 65)
print("FASE D — ANÁLISIS DE EQUIDAD TERRITORIAL SUPERMERCADOS / IVH")
print("=" * 65)

print("\nCargando datos...")
radios = gpd.read_file(RADIOS_PATH)
supers = gpd.read_file(SUPERS_PATH)

print(f"  Radios censales : {len(radios):,} registros  |  CRS: {radios.crs}")
print(f"  Supermercados   : {len(supers):,} registros  |  CRS: {supers.crs}")

# Aseguramos mismo CRS (proyectado, metros)
CRS_PROJ = radios.crs  # EPSG:22183 — Gauss Krüger Faja 3, metros
if supers.crs != CRS_PROJ:
    supers = supers.to_crs(CRS_PROJ)
    print(f"  Supermercados reproyectados a {CRS_PROJ}")

# IVH_quintil como string normalizado '1'..'5'
radios["IVH_quintil"] = radios["IVH_quintil"].astype(str).str.strip()

# ---------------------------------------------------------------------------
# RATIO 1 — Supermercados por km² por clase IVH
# ---------------------------------------------------------------------------
print("\n" + "-" * 65)
print("RATIO 1 — Supermercados por km² por clase IVH")
print("-" * 65)

# Área de cada radio en km²
radios["area_km2"] = radios.geometry.area / 1_000_000

# Spatial join: asignar a cada supermercado la clase IVH del radio donde cae
supers_en_radios = gpd.sjoin(
    supers,
    radios[["IVH_quintil", "geometry"]],
    how="left",
    predicate="within"
)

# Totales por clase IVH
area_por_clase = radios.groupby("IVH_quintil")["area_km2"].sum().rename("area_total_km2")
count_por_clase = supers_en_radios.groupby("IVH_quintil").size().rename("n_supers")

ratio1 = pd.DataFrame({
    "area_total_km2": area_por_clase,
    "n_supers": count_por_clase
}).fillna(0)
ratio1["n_supers"] = ratio1["n_supers"].astype(int)
ratio1["supers_por_km2"] = ratio1["n_supers"] / ratio1["area_total_km2"]
ratio1.index.name = "clase_IVH"
ratio1 = ratio1.reset_index().sort_values("clase_IVH")

# Desglose por marca
count_marca = (
    supers_en_radios.groupby(["IVH_quintil", "marca"])
    .size()
    .unstack(fill_value=0)
    .rename(columns=lambda c: f"n_{c}")
)
ratio1_full = ratio1.merge(count_marca.reset_index().rename(columns={"IVH_quintil": "clase_IVH"}),
                            on="clase_IVH", how="left").fillna(0)
# supers_por_km2 por marca
for col in [c for c in ratio1_full.columns if c.startswith("n_") and c != "n_supers"]:
    marca = col[2:]
    ratio1_full[f"{marca}_por_km2"] = ratio1_full[col] / ratio1_full["area_total_km2"]

ratio1_full.to_csv(OUT_DIR / "ratio1_supers_por_km2.csv", index=False)
print(ratio1_full[["clase_IVH", "area_total_km2", "n_supers", "supers_por_km2"]].to_string(index=False))
print("\nDesglose por marca (supers/km²):")
marcas_cols = [c for c in ratio1_full.columns if c.endswith("_por_km2") and c != "supers_por_km2"]
print(ratio1_full[["clase_IVH"] + marcas_cols].to_string(index=False))

# ---------------------------------------------------------------------------
# RATIO 2 — Distancia promedio al supermercado más cercano por radio
# ---------------------------------------------------------------------------
print("\n" + "-" * 65)
print("RATIO 2 — Distancia al supermercado más cercano (metros)")
print("-" * 65)

# Centroides de radios
centroides = radios.copy()
centroides["centroide"] = radios.geometry.centroid
centroide_coords = np.array([(g.x, g.y) for g in centroides["centroide"]])

# Coordenadas de supermercados
super_coords = np.array([(g.x, g.y) for g in supers.geometry])

# KD-Tree para búsqueda eficiente del vecino más cercano
tree = cKDTree(super_coords)
distancias, _ = tree.query(centroide_coords, k=1)

radios["dist_super_mas_cercano"] = distancias  # en metros

# Agregado por clase IVH
def pct25(x): return np.percentile(x, 25)
def pct75(x): return np.percentile(x, 75)

ratio2 = (
    radios.groupby("IVH_quintil")["dist_super_mas_cercano"]
    .agg(
        media="mean",
        mediana="median",
        p25=pct25,
        p75=pct75,
        n_radios="count"
    )
    .reset_index()
    .rename(columns={"IVH_quintil": "clase_IVH"})
    .sort_values("clase_IVH")
)

# Redondear para legibilidad
for col in ["media", "mediana", "p25", "p75"]:
    ratio2[col] = ratio2[col].round(1)

ratio2.to_csv(OUT_DIR / "ratio2_distancia_promedio.csv", index=False)
print(ratio2.to_string(index=False))

# ---------------------------------------------------------------------------
# RATIO 3 — Distribución de marca_voronoi por clase IVH
# ---------------------------------------------------------------------------
print("\n" + "-" * 65)
print("RATIO 3 — Marca más cercana (Voronoi) por clase IVH (%)")
print("-" * 65)

tabla_cruzada = (
    radios.groupby(["IVH_quintil", "marca_voronoi"])
    .size()
    .unstack(fill_value=0)
)
# Porcentajes sobre el total de radios de cada clase
ratio3_pct = tabla_cruzada.div(tabla_cruzada.sum(axis=1), axis=0).multiply(100).round(2)
ratio3_pct.index.name = "clase_IVH"
ratio3_pct = ratio3_pct.reset_index()

# También guardar conteos absolutos
ratio3_abs = tabla_cruzada.copy()
ratio3_abs.index.name = "clase_IVH"
ratio3_abs["total_radios"] = ratio3_abs.sum(axis=1)
ratio3_abs = ratio3_abs.reset_index()

ratio3_full = ratio3_pct.merge(
    ratio3_abs[["clase_IVH", "total_radios"]], on="clase_IVH"
)
ratio3_full.to_csv(OUT_DIR / "ratio3_marca_por_clase_ivh.csv", index=False)

print("Porcentaje de radios por marca más cercana (Voronoi):")
print(ratio3_pct.to_string(index=False))
print("\nTotal de radios por clase:")
print(ratio3_abs[["clase_IVH", "total_radios"] + [c for c in ratio3_abs.columns if c not in ["clase_IVH", "total_radios"]]].to_string(index=False))

# ---------------------------------------------------------------------------
# RATIO 4 — Radios sin cobertura (cobertura_buffer_500m == 0) por clase IVH
# ---------------------------------------------------------------------------
print("\n" + "-" * 65)
print("RATIO 4 — Radios sin supermercado a 500m por clase IVH")
print("-" * 65)

sin_cobertura = radios[radios["cobertura_buffer_500m"] == 0]
total_por_clase = radios.groupby("IVH_quintil").size().rename("total_radios")
sin_cob_por_clase = sin_cobertura.groupby("IVH_quintil").size().rename("radios_sin_cobertura")

ratio4 = pd.DataFrame({
    "total_radios": total_por_clase,
    "radios_sin_cobertura": sin_cob_por_clase
}).fillna(0).astype(int)
ratio4["pct_sin_cobertura"] = (ratio4["radios_sin_cobertura"] / ratio4["total_radios"] * 100).round(2)
ratio4.index.name = "clase_IVH"
ratio4 = ratio4.reset_index().sort_values("clase_IVH")

ratio4.to_csv(OUT_DIR / "ratio4_sin_cobertura.csv", index=False)
print(ratio4.to_string(index=False))

# ---------------------------------------------------------------------------
# Guardar GeoDataFrame final con dist_super_mas_cercano
# ---------------------------------------------------------------------------
print("\n" + "-" * 65)
print("Guardando radios_CABA_final.gpkg...")
radios.to_file(RADIOS_FINAL, driver="GPKG")
print(f"  Guardado en: {RADIOS_FINAL}")
print(f"  Columnas totales: {len(radios.columns)}")
print(f"  Nueva columna: dist_super_mas_cercano (min={radios['dist_super_mas_cercano'].min():.1f}m, "
      f"max={radios['dist_super_mas_cercano'].max():.1f}m, "
      f"media={radios['dist_super_mas_cercano'].mean():.1f}m)")

# ---------------------------------------------------------------------------
# Resumen ejecutivo
# ---------------------------------------------------------------------------
print("\n" + "=" * 65)
print("RESUMEN EJECUTIVO — EQUIDAD TERRITORIAL SUPERMERCADOS / IVH")
print("=" * 65)
print(f"\nClase IVH 1 (menor vulnerabilidad) -> Clase IVH 5 (mayor vulnerabilidad)")
print()

r1 = ratio1_full.sort_values("clase_IVH")
print(f"{'Clase':<8} {'Supers/km²':>12} {'Dist media (m)':>16} {'Sin cobertura %':>17}")
print("-" * 57)
for _, row in r1.iterrows():
    clase = row["clase_IVH"]
    spkm2 = row["supers_por_km2"]
    dist_row = ratio2[ratio2["clase_IVH"] == clase]
    dm = dist_row["media"].values[0] if len(dist_row) else float("nan")
    cob_row = ratio4[ratio4["clase_IVH"] == clase]
    pct_sin = cob_row["pct_sin_cobertura"].values[0] if len(cob_row) else float("nan")
    print(f"{clase:<8} {spkm2:>12.4f} {dm:>16.1f} {pct_sin:>16.1f}%")

print()
print(f"Brecha densidad (clase 1 / clase 5) : "
      f"{r1[r1['clase_IVH']=='1']['supers_por_km2'].values[0] / r1[r1['clase_IVH']=='5']['supers_por_km2'].values[0]:.2f}x")
d1 = ratio2[ratio2["clase_IVH"]=="1"]["media"].values[0]
d5 = ratio2[ratio2["clase_IVH"]=="5"]["media"].values[0]
print(f"Brecha distancia (clase 5 / clase 1) : {d5 / d1:.2f}x")

print("\nCSVs guardados en:", OUT_DIR)
print("=" * 65)
