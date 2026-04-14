"""
Fase C — Voronoi + Buffer 500m + Join IVH
==========================================
Análisis de zonas de influencia de supermercados en CABA.
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.ops import unary_union, voronoi_diagram
from shapely.geometry import MultiPoint, mapping
import warnings

warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────
# 1. CARGA Y PREPARACIÓN
# ──────────────────────────────────────────────────────────────
print("Cargando datos...")

BASE = "C:/Users/Dell/Agus/2026/Plan de expansion"

supers = gpd.read_file(f"{BASE}/02_datos_procesados/supermercados/supermercados_CABA.gpkg")
radios = gpd.read_file(f"{BASE}/02_datos_procesados/radios_CABA_ivh_final.gpkg")

print(f"  Supermercados: {len(supers)} sucursales | CRS: {supers.crs.to_epsg()}")
print(f"  Radios: {len(radios)} radios censales | CRS: {radios.crs.to_epsg()}")

# Usar el CRS de los radios como referencia (EPSG:22183, en metros)
CRS_REF = radios.crs

if supers.crs != CRS_REF:
    print(f"  Reproyectando supermercados de EPSG:{supers.crs.to_epsg()} a EPSG:{CRS_REF.to_epsg()}...")
    supers = supers.to_crs(CRS_REF)

# Agregar ID único a supermercados
supers = supers.reset_index(drop=True)
supers["id_sucursal"] = supers.index

# Contorno de CABA (disolviendo todos los radios)
print("  Generando contorno de CABA...")
caba_boundary = radios.geometry.unary_union
print(f"  Contorno generado. Área CABA: {caba_boundary.area / 1e6:.2f} km²")

# ──────────────────────────────────────────────────────────────
# 2. VORONOI POR MARCA
# ──────────────────────────────────────────────────────────────
print("\nGenerando polígonos de Voronoi...")

# MultiPoint de todos los supermercados
points = MultiPoint(list(supers.geometry))

# Voronoi diagram — envelope extendido para cubrir CABA completa
envelope = caba_boundary.envelope.buffer(5000)  # 5km extra para evitar bordes
regions = voronoi_diagram(points, envelope=envelope)

# Extraer polígonos individuales
voronoi_polys = list(regions.geoms)
print(f"  Polígonos Voronoi generados: {len(voronoi_polys)}")

# Crear GeoDataFrame de Voronoi
voronoi_gdf = gpd.GeoDataFrame(
    geometry=voronoi_polys,
    crs=CRS_REF
)

# Clipear al contorno de CABA
voronoi_gdf["geometry"] = voronoi_gdf.geometry.intersection(caba_boundary)
voronoi_gdf = voronoi_gdf[~voronoi_gdf.geometry.is_empty].reset_index(drop=True)

# Spatial join: asignar cada Voronoi al supermercado más cercano
# Usamos el centroide de cada Voronoi para encontrar el super más cercano
voronoi_gdf["voronoi_idx"] = voronoi_gdf.index
voronoi_centroids = gpd.GeoDataFrame(
    {"voronoi_idx": voronoi_gdf.index, "geometry": voronoi_gdf.geometry.centroid},
    crs=CRS_REF
)

joined = gpd.sjoin_nearest(
    voronoi_centroids,
    supers[["id_sucursal", "marca", "nombre", "direccion", "geometry"]],
    how="left"
)

# sjoin_nearest puede generar duplicados si hay empates — quedarse con el primero por voronoi_idx
joined = joined.drop_duplicates(subset=["voronoi_idx"], keep="first")
joined = joined.set_index("voronoi_idx")

# Reconstruir con geometría original del Voronoi
voronoi_final = voronoi_gdf.drop(columns=["voronoi_idx"]).copy()
voronoi_final["id_sucursal"] = joined.loc[voronoi_final.index, "id_sucursal"].values
voronoi_final["marca"] = joined.loc[voronoi_final.index, "marca"].values
voronoi_final["nombre"] = joined.loc[voronoi_final.index, "nombre"].values
voronoi_final["direccion"] = joined.loc[voronoi_final.index, "direccion"].values

# Filtrar polígonos vacíos/nulos
voronoi_final = voronoi_final.dropna(subset=["id_sucursal"]).reset_index(drop=True)

print(f"  Voronoi finales: {len(voronoi_final)} polígonos")
marca_counts = voronoi_final["marca"].value_counts()
for marca, cnt in marca_counts.items():
    print(f"    {marca}: {cnt}")

# Guardar Voronoi
output_voronoi = f"{BASE}/02_datos_procesados/supermercados/voronoi_CABA.gpkg"
voronoi_final.to_file(output_voronoi, driver="GPKG")
print(f"  Guardado: {output_voronoi}")

# ──────────────────────────────────────────────────────────────
# 3. BUFFER 500m
# ──────────────────────────────────────────────────────────────
print("\nGenerando buffers de 500m...")

buffers = supers.copy()
buffers["geometry"] = buffers.geometry.buffer(500)

# Clipear al contorno de CABA
buffers["geometry"] = buffers.geometry.intersection(caba_boundary)
buffers = buffers[~buffers.geometry.is_empty].reset_index(drop=True)

print(f"  Buffers generados: {len(buffers)}")

# Área total cubierta (unión de todos los buffers)
union_buffers = buffers.geometry.unary_union
area_cubierta_km2 = union_buffers.area / 1e6
area_caba_km2 = caba_boundary.area / 1e6
pct_cubierta = (area_cubierta_km2 / area_caba_km2) * 100

print(f"  Área total cubierta: {area_cubierta_km2:.2f} km² ({pct_cubierta:.1f}% de CABA)")

# Guardar buffers
output_buffers = f"{BASE}/02_datos_procesados/supermercados/buffers_500m_CABA.gpkg"
buffers.to_file(output_buffers, driver="GPKG")
print(f"  Guardado: {output_buffers}")

# ──────────────────────────────────────────────────────────────
# 4. JOIN ESPACIAL CON IVH
# ──────────────────────────────────────────────────────────────
print("\nRealizando join espacial con IVH...")

radios_out = radios.copy()

# --- 4a. Join Voronoi → radios ---
# Usamos centroide de cada radio para determinar en qué Voronoi cae
print("  Calculando marca_voronoi por centroide de radio...")

radios_centroids = radios_out.copy()
radios_centroids["geometry"] = radios_centroids.geometry.centroid

join_voronoi = gpd.sjoin(
    radios_centroids[["LINK", "geometry"]],
    voronoi_final[["marca", "id_sucursal", "geometry"]],
    how="left",
    predicate="within"
)

# En caso de que algún centroide no caiga dentro (borde), usar sjoin_nearest
no_match_mask = join_voronoi["marca"].isna()
if no_match_mask.any():
    n_no_match = no_match_mask.sum()
    print(f"    {n_no_match} radios sin match por 'within', aplicando sjoin_nearest...")

    radios_no_match = radios_centroids[no_match_mask][["LINK", "geometry"]]
    join_nearest = gpd.sjoin_nearest(
        radios_no_match,
        voronoi_final[["marca", "id_sucursal", "geometry"]],
        how="left"
    )
    # Reemplazar NaN en join_voronoi con valores del nearest
    for idx in join_voronoi[no_match_mask].index:
        link_val = join_voronoi.loc[idx, "LINK"]
        nearest_row = join_nearest[join_nearest["LINK"] == link_val]
        if not nearest_row.empty:
            join_voronoi.loc[idx, "marca"] = nearest_row["marca"].values[0]
            join_voronoi.loc[idx, "id_sucursal"] = nearest_row["id_sucursal"].values[0]

# Asignar marca_voronoi a radios_out
# Alineamos por índice
marca_map = join_voronoi["marca"].values
id_map = join_voronoi["id_sucursal"].values

radios_out["marca_voronoi"] = marca_map
radios_out["id_sucursal_voronoi"] = id_map

print(f"  marca_voronoi asignado. Distribución:")
print(radios_out["marca_voronoi"].value_counts().to_string())

# --- 4b. Cobertura Buffer 500m por radio ---
print("  Calculando cobertura_buffer_500m por radio...")

# Unión de todos los buffers
union_buf = buffers.geometry.unary_union

# Para cada radio: área de intersección / área del radio
def calcular_cobertura(geom):
    try:
        inter = geom.intersection(union_buf)
        if geom.area > 0:
            return inter.area / geom.area
        return 0.0
    except Exception:
        return 0.0

radios_out["cobertura_buffer_500m"] = radios_out.geometry.apply(calcular_cobertura)

n_cobertura_50 = (radios_out["cobertura_buffer_500m"] > 0.5).sum()
n_sin_cobertura = (radios_out["cobertura_buffer_500m"] == 0.0).sum()
n_total_join = len(radios_out)

print(f"  Radios con cobertura > 50%: {n_cobertura_50}")
print(f"  Radios sin ninguna cobertura: {n_sin_cobertura}")

# Guardar radios con supermercados
output_radios = f"{BASE}/02_datos_procesados/radios_CABA_con_supermercados.gpkg"
radios_out.to_file(output_radios, driver="GPKG")
print(f"  Guardado: {output_radios}")

# ──────────────────────────────────────────────────────────────
# 5. RESUMEN FINAL
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 50)
print("=== FASE C — RESUMEN ===")
print(f"Voronoi: {len(voronoi_final)} polígonos generados")
for marca, cnt in marca_counts.items():
    print(f"  - {marca}={cnt}")
print(f"Buffer 500m: {len(buffers)} buffers generados")
print(f"  - Área total cubierta: {area_cubierta_km2:.2f} km² ({pct_cubierta:.1f}% del área de CABA)")
print(f"  - Radios con cobertura > 50%: {n_cobertura_50}")
print(f"  - Radios sin ninguna cobertura: {n_sin_cobertura}")
print(f"Join IVH completado: {n_total_join} radios con datos")
print("=" * 50)
