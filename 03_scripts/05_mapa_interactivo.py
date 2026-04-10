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

# Paths
ROOT = Path(__file__).parent.parent
INPUT_GPKG = ROOT / "02_datos_procesados" / "radios_CABA_ivh_final.gpkg"
MAPAS_INTERACTIVOS = ROOT / "04_mapas" / "interactivos"
MAPAS_INTERACTIVOS.mkdir(parents=True, exist_ok=True)

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


def main():
    print("=== FASE 5: Mapa interactivo ===")
    print(f"Leyendo: {INPUT_GPKG}")
    gdf = gpd.read_file(INPUT_GPKG)
    print(f"Radios cargados: {len(gdf)}")

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
