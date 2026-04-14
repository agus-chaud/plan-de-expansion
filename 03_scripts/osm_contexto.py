"""
osm_contexto.py
===============
Descarga (una vez) vías principales, ferrocarril/subte y cementerios desde
OpenStreetMap vía OSMnx, y los guarda en GeoPackage local para reutilizar en
mapas estáticos e interactivos sin repetir la descarga.
"""
from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

# Ciudad para consultas OSM (Nominatim)
PLACE_CABA = "Ciudad Autónoma de Buenos Aires, Argentina"

# Tipos de calle considerados “avenidas / vías rápidas” de contexto
HIGHWAY_MAJOR = frozenset({"motorway", "trunk", "primary", "secondary"})


def _highway_is_major(val: Any) -> bool:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    if isinstance(val, (list, tuple)):
        return any(str(x) in HIGHWAY_MAJOR for x in val)
    return str(val) in HIGHWAY_MAJOR


def cache_path(root: Path) -> Path:
    return root / "02_datos_procesados" / "osm_contexto_caba.gpkg"


def _read_layer(path: Path, layer: str) -> gpd.GeoDataFrame | None:
    try:
        return gpd.read_file(path, layer=layer)
    except Exception:
        return None


def cargar_desde_cache(root: Path) -> dict[str, gpd.GeoDataFrame] | None:
    """Si existe el GPKG con las tres capas, las devuelve; si no, None."""
    path = cache_path(root)
    if not path.is_file():
        return None
    out: dict[str, gpd.GeoDataFrame] = {}
    for layer in ("roads_major", "railways", "cemeteries"):
        gdf = _read_layer(path, layer)
        if gdf is None:
            return None
        out[layer] = gdf
    return out


def descargar_y_guardar(root: Path) -> dict[str, gpd.GeoDataFrame]:
    import osmnx as ox

    try:
        from osmnx.features import features_from_place as features_from_osm
    except ImportError:
        features_from_osm = ox.geometries_from_place

    ox.settings.use_cache = True

    path = cache_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        path.unlink()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # Red vial: aristas clasificadas primary/secondary (y trunk/motorway)
        G = ox.graph_from_place(PLACE_CABA, network_type="drive")
        _nodes, edges = ox.graph_to_gdfs(G)
    if edges.empty:
        roads_major = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    else:
        mask = edges["highway"].apply(_highway_is_major)
        roads_major = edges.loc[mask, ["geometry"]].copy()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        railways = features_from_osm(
            PLACE_CABA, tags={"railway": ["rail", "subway", "tram"]}
        )
        cemeteries = features_from_osm(
            PLACE_CABA, tags={"landuse": "cemetery"}
        )

    if railways is None or railways.empty:
        railways = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    if cemeteries is None or cemeteries.empty:
        cemeteries = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

    roads_major = roads_major.to_crs("EPSG:4326")
    railways = railways.to_crs("EPSG:4326")
    cemeteries = cemeteries.to_crs("EPSG:4326")

    roads_major.to_file(path, driver="GPKG", layer="roads_major")
    railways.to_file(path, driver="GPKG", layer="railways", mode="a")
    cemeteries.to_file(path, driver="GPKG", layer="cemeteries", mode="a")

    return {
        "roads_major": roads_major,
        "railways": railways,
        "cemeteries": cemeteries,
    }


def obtener_capas_contexto(
    root: Path, *, regenerar: bool = False
) -> dict[str, gpd.GeoDataFrame] | None:
    """
    Devuelve dict con claves roads_major, railways, cemeteries (WGS84),
    usando caché en disco salvo que regenerar=True.
    Si falla la descarga, devuelve None.
    """
    if not regenerar:
        cached = cargar_desde_cache(root)
        if cached is not None:
            return cached
    try:
        return descargar_y_guardar(root)
    except Exception as exc:
        print(f"  AVISO: no se pudieron obtener capas OSM ({exc})")
        return None
