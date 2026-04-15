"""
05_mapa_interactivo.py
======================
Fase 5: Generar mapa interactivo HTML con el IVH usando Folium.

Prerequisito: Haber ejecutado 03_calculo_indicadores.py

Salida:
  - 04_mapas/interactivos/IVH_CABA.html
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import geopandas as gpd
import folium

from osm_contexto import obtener_capas_contexto

# Paths
ROOT = Path(__file__).parent.parent
INPUT_GPKG = ROOT / "02_datos_procesados" / "radios_CABA_ivh_final.gpkg"
MAPAS_INTERACTIVOS = ROOT / "04_mapas" / "interactivos"
MAPAS_INTERACTIVOS.mkdir(parents=True, exist_ok=True)
LINK_EXCLUIR_RENDER: tuple[str, ...] = ("020141001", "020081207")

# Los 9 indicadores IVH
VARS_IVH = [
    "ivh_piso_tierra",
    "ivh_techo_precario",
    "ivh_sin_agua_red",
    "ivh_sin_cloaca",
    "ivh_sin_gas_red",
    "ivh_hacinamiento",
    "ivh_nbi",
    "ivh_desempleo",
    "ivh_baja_educacion",
]

CABA_CENTER = [-34.6037, -58.3816]
ZOOM_START = 12


def agregar_capas_osm_bajo_coropleta(m: folium.Map, capas: dict | None) -> None:
    """Polígonos (cementerios) debajo del IVH para que no tapen el coropleta."""
    if not capas:
        return
    fg_cem = folium.FeatureGroup(name="Cementerios (OSM)", show=False)
    cem = capas.get("cemeteries")
    if cem is not None and not cem.empty:
        folium.GeoJson(
            data=cem.to_json(),
            style_function=lambda _f: {
                "fillColor": "#bdbdbd",
                "color": "#757575",
                "weight": 0.4,
                "fillOpacity": 0.30,
                "opacity": 0.6,
            },
        ).add_to(fg_cem)
    fg_cem.add_to(m)


def agregar_capas_osm_sobre_coropleta(m: folium.Map, capas: dict | None) -> None:
    """Líneas (vías y avenidas) encima del relleno del IVH para que se vean."""
    if not capas:
        return
    fg_rail = folium.FeatureGroup(name="Vías férreas / subte / tranvía (OSM)", show=False)
    rail = capas.get("railways")
    if rail is not None and not rail.empty:
        folium.GeoJson(
            data=rail.to_json(),
            style_function=lambda _f: {
                "color": "#5d4037",
                "weight": 0.8,
                "opacity": 0.7,
            },
        ).add_to(fg_rail)
    fg_rail.add_to(m)

    fg_road = folium.FeatureGroup(name="Avenidas principales (OSM)", show=False)
    roads = capas.get("roads_major")
    if roads is not None and not roads.empty:
        folium.GeoJson(
            data=roads.to_json(),
            style_function=lambda _f: {
                "color": "#6d4c41",
                "weight": 0.45,
                "opacity": 0.5,
            },
        ).add_to(fg_road)
    fg_road.add_to(m)


def main():
    print("=== FASE 5: Mapa interactivo ===")
    print(f"Leyendo: {INPUT_GPKG}")
    gdf = gpd.read_file(INPUT_GPKG)
    print(f"Radios cargados: {len(gdf)}")
    if "LINK" in gdf.columns:
        n0 = len(gdf)
        gdf = gdf.loc[~gdf["LINK"].isin(LINK_EXCLUIR_RENDER)].copy()
        if len(gdf) != n0:
            print(
                f"Fallback render: excluidos {n0 - len(gdf)} radios manuales ({', '.join(LINK_EXCLUIR_RENDER)})"
            )

    # Folium necesita EPSG:4326 (WGS84)
    print("Reproyectando a EPSG:4326...")
    gdf = gdf.to_crs("EPSG:4326")

    # Eliminar filas sin IVH para evitar problemas en el choropleth
    gdf = gdf.dropna(subset=["IVH"])
    print(f"Radios con IVH valido: {len(gdf)}")

    # Columnas para tooltip: LINK + indicadores presentes + IVH + quintil
    vars_presentes = [v for v in VARS_IVH if v in gdf.columns]
    tooltip_fields = ["LINK"] + vars_presentes + ["IVH", "IVH_quintil"]
    # Redondear IVH a 4 decimales para mejor legibilidad
    gdf["IVH"] = gdf["IVH"].round(4)
    for v in vars_presentes:
        gdf[v] = gdf[v].round(4)

    # Mapa base
    m = folium.Map(location=CABA_CENTER, zoom_start=ZOOM_START, tiles="CartoDB positron")

    print("Capas de contexto OSM...")
    capas_osm = obtener_capas_contexto(ROOT)
    if capas_osm is None:
        print("  Sin capas OSM (sin caché y sin red o error en descarga).")
    else:
        agregar_capas_osm_bajo_coropleta(m, capas_osm)
        print("  Capas OSM: cementerios bajo el IVH; vías encima del IVH (panel de capas).")

    # Capa choropleth — usa GeoJSON de la geometria reproyectada
    folium.Choropleth(
        geo_data=gdf[["LINK", "geometry"]].to_json(),
        data=gdf[["LINK", "IVH"]],
        columns=["LINK", "IVH"],
        key_on="feature.properties.LINK",
        fill_color="YlOrRd",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name="Indice de Vulnerabilidad Habitacional (IVH)",
        name="IVH",
        nan_fill_color="lightgrey",
    ).add_to(m)

    if capas_osm is not None:
        agregar_capas_osm_sobre_coropleta(m, capas_osm)

    # Capa GeoJson transparente solo para tooltip
    aliases = ["Codigo"] + [v.replace("ivh_", "").replace("_", " ").title() for v in vars_presentes] + ["IVH", "Quintil"]
    folium.GeoJson(
        gdf[tooltip_fields + ["geometry"]].to_json(),
        style_function=lambda x: {"fillOpacity": 0, "weight": 0},
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=aliases,
            localize=True,
        ),
    ).add_to(m)

    folium.LayerControl().add_to(m)

    output_path = MAPAS_INTERACTIVOS / "IVH_CABA.html"
    m.save(str(output_path))
    print(f"Guardado: {output_path}")
    print("Fase 5 completada.")


if __name__ == "__main__":
    main()
