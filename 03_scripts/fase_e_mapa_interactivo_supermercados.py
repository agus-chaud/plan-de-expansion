"""
Fase E — Mapa interactivo de equidad territorial: supermercados vs IVH en CABA
Genera: 04_mapas/interactivos/IVH_supermercados_CABA.html
"""

import os
import json
import warnings
import numpy as np
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import FloatImage
from branca.colormap import LinearColormap, StepColormap
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from osm_contexto import obtener_capas_contexto

warnings.filterwarnings("ignore")

# ─── Rutas ─────────────────────────────────────────────────────────────────────
BASE   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS  = os.path.join(BASE, "02_datos_procesados")
SALIDA = os.path.join(BASE, "04_mapas", "interactivos")
os.makedirs(SALIDA, exist_ok=True)
ROOT = Path(BASE)

# ─── Colores por marca ─────────────────────────────────────────────────────────
MARCA_COLORES = {
    "Carrefour": "#0066CC",
    "Coto":      "#CC0000",
    "Disco":     "#00AA44",
    "Jumbo":     "#FF6600",
}

# ─── Carga y reproyección a EPSG:4326 para Folium ─────────────────────────────
print("Cargando datos...")
CRS_4326 = "EPSG:4326"

radios  = gpd.read_file(os.path.join(DATOS, "radios_CABA_final.gpkg")).to_crs(CRS_4326)
supers  = gpd.read_file(os.path.join(DATOS, "supermercados", "supermercados_CABA.gpkg")).to_crs(CRS_4326)
voronoi = gpd.read_file(os.path.join(DATOS, "supermercados", "voronoi_CABA.gpkg")).to_crs(CRS_4326)
buffers = gpd.read_file(os.path.join(DATOS, "supermercados", "buffers_500m_CABA.gpkg")).to_crs(CRS_4326)

# Radios sin cobertura: cobertura_buffer_500m == 0
sin_cobertura = radios[radios["cobertura_buffer_500m"] == 0].copy()

# IVH quintil como numérico
radios["IVH_quintil_num"] = pd.to_numeric(radios["IVH_quintil"], errors="coerce")
sin_cobertura["IVH_quintil_num"] = pd.to_numeric(sin_cobertura["IVH_quintil"], errors="coerce")

print(f"  Radios: {len(radios)}")
print(f"  Supermercados: {len(supers)}")
print(f"  Voronoi: {len(voronoi)}")
print(f"  Buffers: {len(buffers)}")
print(f"  Sin cobertura: {len(sin_cobertura)}")

print("Cargando capas OSM de contexto...")
capas_osm = obtener_capas_contexto(ROOT)
if capas_osm is None:
    print("  Sin capas OSM (sin caché y sin red o error en descarga).")
else:
    print("  Capas OSM listas.")

# ─── Colormap IVH (YlOrRd, 5 clases) ─────────────────────────────────────────
IVH_COLORS = ["#FFFFB2", "#FECC5C", "#FD8D3C", "#F03B20", "#BD0026"]
IVH_LABELS = {1: "Clase 1 — Muy baja vulnerabilidad",
              2: "Clase 2 — Baja",
              3: "Clase 3 — Media",
              4: "Clase 4 — Alta",
              5: "Clase 5 — Muy alta vulnerabilidad"}

def color_ivh(quintil):
    try:
        q = int(quintil)
        return IVH_COLORS[q - 1]
    except (ValueError, TypeError, IndexError):
        return "#CCCCCC"

# ─── Inicializar mapa ─────────────────────────────────────────────────────────
print("\nCreando mapa Folium...")
mapa = folium.Map(
    location=[-34.6037, -58.3816],
    zoom_start=12,
    tiles="CartoDB positron",
    control_scale=True,
)

if capas_osm is not None:
    fg_cem = folium.FeatureGroup(name="Cementerios (OSM)", show=False)
    cem = capas_osm.get("cemeteries")
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
    fg_cem.add_to(mapa)

# ─── CAPA 1: IVH base (coroplético) ───────────────────────────────────────────
print("  Capa 1: IVH base...")

def style_ivh(feature):
    q = feature["properties"].get("IVH_quintil", None)
    return {
        "fillColor":   color_ivh(q),
        "color":       "#555555",
        "weight":      0.3,
        "fillOpacity": 0.6,
    }

def highlight_ivh(feature):
    return {"weight": 2, "color": "#333333", "fillOpacity": 0.85}

def tooltip_ivh(feature):
    return None  # usamos GeoJsonTooltip abajo

capa_ivh = folium.GeoJson(
    radios[["IVH_quintil", "IVH", "dist_super_mas_cercano",
             "marca_voronoi", "cobertura_buffer_500m", "geometry"]].to_json(),
    name="IVH — Índice de Vulnerabilidad Habitacional",
    style_function=style_ivh,
    highlight_function=highlight_ivh,
    tooltip=folium.GeoJsonTooltip(
        fields=["IVH_quintil", "IVH", "dist_super_mas_cercano",
                "marca_voronoi", "cobertura_buffer_500m"],
        aliases=["Clase IVH:", "Valor IVH:", "Dist. super más cercano (m):",
                 "Marca zona Voronoi:", "Cobertura 500m:"],
        localize=True,
        sticky=True,
        style="font-size: 12px;",
    ),
    zoom_on_click=False,
)
capa_ivh.add_to(mapa)

if capas_osm is not None:
    fg_rail = folium.FeatureGroup(name="Vías férreas / subte / tranvía (OSM)", show=False)
    rail = capas_osm.get("railways")
    if rail is not None and not rail.empty:
        folium.GeoJson(
            data=rail.to_json(),
            style_function=lambda _f: {
                "color": "#5d4037",
                "weight": 0.8,
                "opacity": 0.7,
            },
        ).add_to(fg_rail)
    fg_rail.add_to(mapa)

    fg_road = folium.FeatureGroup(name="Avenidas principales (OSM)", show=False)
    roads = capas_osm.get("roads_major")
    if roads is not None and not roads.empty:
        folium.GeoJson(
            data=roads.to_json(),
            style_function=lambda _f: {
                "color": "#6d4c41",
                "weight": 0.45,
                "opacity": 0.5,
            },
        ).add_to(fg_road)
    fg_road.add_to(mapa)

# ─── CAPA 2: Supermercados ────────────────────────────────────────────────────
print("  Capa 2: Supermercados...")

capa_supers = folium.FeatureGroup(name="Supermercados", show=True)

for _, row in supers.iterrows():
    marca  = row.get("marca", "Desconocida")
    nombre = row.get("nombre", "")
    direc  = row.get("direccion", "")
    color  = MARCA_COLORES.get(marca, "#888888")
    lat, lon = row.geometry.y, row.geometry.x

    popup_html = f"""
    <div style="font-family: Arial, sans-serif; font-size: 13px; min-width: 180px;">
        <b style="color:{color};">{marca}</b><br>
        <span>{nombre}</span><br>
        <small style="color:#666;">{direc}</small>
    </div>
    """

    folium.CircleMarker(
        location=[lat, lon],
        radius=6,
        color="white",
        weight=1.2,
        fill=True,
        fill_color=color,
        fill_opacity=0.9,
        popup=folium.Popup(popup_html, max_width=260),
        tooltip=f"{marca} — {nombre}",
    ).add_to(capa_supers)

capa_supers.add_to(mapa)

# ─── CAPA 3: Buffers 500m ─────────────────────────────────────────────────────
print("  Capa 3: Buffers 500m...")

capa_buffers = folium.FeatureGroup(name="Buffers 500m", show=False)

for _, row in buffers.iterrows():
    marca = row.get("marca", "Desconocida")
    color = MARCA_COLORES.get(marca, "#888888")
    folium.GeoJson(
        row.geometry.__geo_interface__,
        style_function=lambda feature, c=color: {
            "fillColor":   c,
            "color":       c,
            "weight":      0.5,
            "fillOpacity": 0.15,
        },
    ).add_to(capa_buffers)

capa_buffers.add_to(mapa)

# ─── CAPA 4: Voronoi ──────────────────────────────────────────────────────────
print("  Capa 4: Voronoi...")

capa_voronoi = folium.FeatureGroup(name="Zonas Voronoi por marca", show=False)

for _, row in voronoi.iterrows():
    marca = row.get("marca", "Desconocida")
    color = MARCA_COLORES.get(marca, "#888888")
    folium.GeoJson(
        row.geometry.__geo_interface__,
        style_function=lambda feature, c=color: {
            "fillColor":   c,
            "color":       c,
            "weight":      1.0,
            "fillOpacity": 0.05,
        },
        tooltip=f"Voronoi — {marca}",
    ).add_to(capa_voronoi)

capa_voronoi.add_to(mapa)

# ─── CAPA 5: Radios sin cobertura ─────────────────────────────────────────────
print("  Capa 5: Radios sin cobertura...")

def style_sin_cob(feature):
    return {
        "fillColor":   "#CC0000",
        "color":       "#660000",
        "weight":      1.0,
        "fillOpacity": 0.75,
    }

def highlight_sin_cob(feature):
    return {"weight": 2.5, "color": "#000000", "fillOpacity": 0.9}

capa_sin_cob = folium.GeoJson(
    sin_cobertura[["IVH_quintil", "IVH", "dist_super_mas_cercano",
                    "marca_voronoi", "geometry"]].to_json(),
    name="Radios sin cobertura 500m",
    style_function=style_sin_cob,
    highlight_function=highlight_sin_cob,
    tooltip=folium.GeoJsonTooltip(
        fields=["IVH_quintil", "IVH", "dist_super_mas_cercano", "marca_voronoi"],
        aliases=["Clase IVH:", "Valor IVH:", "Dist. super (m):", "Marca Voronoi:"],
        localize=True,
        sticky=True,
        style="font-size: 12px; background: #fff3f3;",
    ),
    show=True,
)
capa_sin_cob.add_to(mapa)

# ─── Leyenda HTML personalizada ───────────────────────────────────────────────
legend_html = """
<div style="
    position: fixed;
    bottom: 30px; right: 10px;
    width: 220px;
    background-color: white;
    border: 1px solid #ccc;
    border-radius: 6px;
    padding: 12px 14px;
    font-family: Arial, sans-serif;
    font-size: 12px;
    z-index: 1000;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
">
    <b style="font-size:13px;">IVH — Clases</b><br>
    <i style="background:#FFFFB2;width:14px;height:14px;display:inline-block;margin-right:6px;border:1px solid #aaa;"></i>Clase 1 — Muy baja<br>
    <i style="background:#FECC5C;width:14px;height:14px;display:inline-block;margin-right:6px;border:1px solid #aaa;"></i>Clase 2 — Baja<br>
    <i style="background:#FD8D3C;width:14px;height:14px;display:inline-block;margin-right:6px;border:1px solid #aaa;"></i>Clase 3 — Media<br>
    <i style="background:#F03B20;width:14px;height:14px;display:inline-block;margin-right:6px;border:1px solid #aaa;"></i>Clase 4 — Alta<br>
    <i style="background:#BD0026;width:14px;height:14px;display:inline-block;margin-right:6px;border:1px solid #aaa;"></i>Clase 5 — Muy alta<br>
    <br>
    <b style="font-size:13px;">Marcas</b><br>
    <i style="background:#0066CC;width:14px;height:14px;display:inline-block;margin-right:6px;border-radius:50%;"></i>Carrefour<br>
    <i style="background:#CC0000;width:14px;height:14px;display:inline-block;margin-right:6px;border-radius:50%;"></i>Coto<br>
    <i style="background:#00AA44;width:14px;height:14px;display:inline-block;margin-right:6px;border-radius:50%;"></i>Disco<br>
    <i style="background:#FF6600;width:14px;height:14px;display:inline-block;margin-right:6px;border-radius:50%;"></i>Jumbo<br>
    <br>
    <i style="background:#CC0000;width:14px;height:14px;display:inline-block;margin-right:6px;opacity:0.75;"></i>Sin cobertura 500m
</div>
"""
mapa.get_root().html.add_child(folium.Element(legend_html))

# ─── Título HTML ──────────────────────────────────────────────────────────────
titulo_html = """
<div style="
    position: fixed;
    top: 10px; left: 50%; transform: translateX(-50%);
    background: white;
    border: 1px solid #ccc;
    border-radius: 6px;
    padding: 8px 18px;
    font-family: Arial, sans-serif;
    font-size: 15px;
    font-weight: bold;
    z-index: 1000;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
    white-space: nowrap;
">
    Equidad territorial — Supermercados vs IVH en CABA
</div>
"""
mapa.get_root().html.add_child(folium.Element(titulo_html))

# ─── Layer control ────────────────────────────────────────────────────────────
folium.LayerControl(collapsed=False, position="topleft").add_to(mapa)

# ─── Guardar ──────────────────────────────────────────────────────────────────
out_html = os.path.join(SALIDA, "IVH_supermercados_CABA.html")
mapa.save(out_html)
print(f"\n  Guardado: {out_html}")
print("Fase E - Mapa interactivo completado.")
