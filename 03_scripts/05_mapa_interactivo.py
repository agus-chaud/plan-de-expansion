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
from utils import RESULTADO_GPKG, MAPAS_INTERACTIVOS, CABA_CENTER, ZOOM_START, VARS_IVH


def main():
    print("=== FASE 5: Mapa interactivo ===")

    gdf = gpd.read_file(RESULTADO_GPKG)

    # Base map
    m = folium.Map(location=CABA_CENTER, zoom_start=ZOOM_START, tiles="CartoDB positron")

    # Capa IVH
    folium.Choropleth(
        geo_data=gdf.to_json(),
        data=gdf,
        columns=["LINK", "IVH"],
        key_on="feature.properties.LINK",
        fill_color="YlOrRd",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name="Índice de Vulnerabilidad Habitacional (IVH)",
        name="IVH",
    ).add_to(m)

    # Tooltip con variables individuales
    tooltip_fields = ["LINK"] + [v for v in VARS_IVH if v in gdf.columns] + ["IVH"]
    folium.GeoJson(
        gdf[tooltip_fields + ["geometry"]].to_json(),
        style_function=lambda x: {"fillOpacity": 0, "weight": 0},
        tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_fields),
    ).add_to(m)

    folium.LayerControl().add_to(m)

    output_path = MAPAS_INTERACTIVOS / "IVH_CABA.html"
    m.save(str(output_path))
    print(f"Guardado: {output_path}")
    print("Fase 5 completada.")


if __name__ == "__main__":
    main()
