"""
Fase E — Mapas estáticos de equidad territorial: supermercados vs IVH en CABA
Genera 4 mapas en 04_mapas/estaticos/supermercados/
"""

import os
import warnings
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.cm import get_cmap
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from osm_contexto import obtener_capas_contexto

warnings.filterwarnings("ignore")

# ─── Rutas ────────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(BASE, "02_datos_procesados")
SALIDA = os.path.join(BASE, "04_mapas", "estaticos", "supermercados")
os.makedirs(SALIDA, exist_ok=True)
ROOT = Path(BASE)

# ─── Colores por marca ─────────────────────────────────────────────────────────
MARCA_COLORES = {
    "Carrefour": "#0066CC",
    "Coto":      "#CC0000",
    "Disco":     "#00AA44",
    "Jumbo":     "#FF6600",
}

# ─── Carga de datos ────────────────────────────────────────────────────────────
print("Cargando datos...")
radios  = gpd.read_file(os.path.join(DATOS, "radios_CABA_final.gpkg"))
supers  = gpd.read_file(os.path.join(DATOS, "supermercados", "supermercados_CABA.gpkg"))
voronoi = gpd.read_file(os.path.join(DATOS, "supermercados", "voronoi_CABA.gpkg"))

r1 = pd.read_csv(os.path.join(DATOS, "supermercados", "ratio1_supers_por_km2.csv"))
r2 = pd.read_csv(os.path.join(DATOS, "supermercados", "ratio2_distancia_promedio.csv"))
r3 = pd.read_csv(os.path.join(DATOS, "supermercados", "ratio3_marca_por_clase_ivh.csv"))
r4 = pd.read_csv(os.path.join(DATOS, "supermercados", "ratio4_sin_cobertura.csv"))

# Unificar CRS — trabajar en EPSG:22183 (el de radios y voronoi)
CRS_BASE = radios.crs
supers = supers.to_crs(CRS_BASE)

# Radios sin cobertura (cobertura_buffer_500m == 0)
sin_cobertura = radios[radios["cobertura_buffer_500m"] == 0].copy()

print(f"  Radios: {len(radios)}")
print(f"  Supermercados: {len(supers)}")
print(f"  Voronoi: {len(voronoi)}")
print(f"  Radios sin cobertura: {len(sin_cobertura)}")

# ─── UTILIDADES ───────────────────────────────────────────────────────────────
def quitar_ejes(ax):
    ax.set_axis_off()

def agregar_norte(ax, x=0.97, y=0.97):
    ax.annotate("N", xy=(x, y), xycoords="axes fraction",
                fontsize=12, fontweight="bold", ha="center", va="center",
                xytext=(x, y - 0.05),
                arrowprops=dict(arrowstyle="->", lw=1.5))


def trazar_capas_contexto(ax, crs_destino, capas: dict | None) -> None:
    """Capas OSM con el mismo estilo que 04_mapas_estaticos.py."""
    if not capas:
        return
    z = 0
    cem = capas.get("cemeteries")
    if cem is not None and not cem.empty:
        cem.to_crs(crs_destino).plot(
            ax=ax,
            facecolor="#bdbdbd",
            edgecolor="#757575",
            alpha=0.35,
            linewidth=0.2,
            zorder=z,
        )
        z += 1
    rail = capas.get("railways")
    if rail is not None and not rail.empty:
        rail.to_crs(crs_destino).plot(
            ax=ax, color="#5d4037", linewidth=0.6, alpha=0.7, zorder=z
        )
        z += 1
    roads = capas.get("roads_major")
    if roads is not None and not roads.empty:
        roads.to_crs(crs_destino).plot(
            ax=ax, color="#6d4c41", linewidth=0.22, alpha=0.5, zorder=z
        )


print("Capas de contexto OSM (cementerios, vías, avenidas)...")
capas_osm = obtener_capas_contexto(ROOT)
if capas_osm is None:
    print("  Mapas sin capas OSM (sin caché y sin red o error en descarga).")
else:
    print("  Capas OSM listas (desde caché o descarga).")

# ─── MAPA 1: Distancia al supermercado más cercano ────────────────────────────
print("\nGenerando Mapa 1 — Distancia al supermercado más cercano...")

fig, ax = plt.subplots(1, 1, figsize=(14, 10))
fig.patch.set_facecolor("#F8F8F8")
ax.set_facecolor("#D6EAF8")
trazar_capas_contexto(ax, radios.crs, capas_osm)

radios.plot(
    ax=ax,
    column="dist_super_mas_cercano",
    cmap="RdYlGn_r",
    legend=True,
    legend_kwds={
        "label": "Distancia (metros)",
        "orientation": "vertical",
        "shrink": 0.6,
        "pad": 0.01,
    },
    missing_kwds={"color": "lightgrey"},
    edgecolor="none",
    linewidth=0,
)

# Puntos de supermercados coloreados por marca
for marca, color in MARCA_COLORES.items():
    sub = supers[supers["marca"] == marca]
    sub.plot(ax=ax, color=color, markersize=20, marker="o",
             zorder=5, label=marca, edgecolor="white", linewidth=0.5)

# Leyenda de marcas
handles = [mpatches.Patch(color=c, label=m) for m, c in MARCA_COLORES.items()]
ax.legend(handles=handles, title="Marca", loc="lower left",
          framealpha=0.9, fontsize=9)

ax.set_title("Distancia al supermercado más cercano — CABA",
             fontsize=14, fontweight="bold", pad=12)
quitar_ejes(ax)
plt.tight_layout()
out1 = os.path.join(SALIDA, "mapa1_distancia_supermercado.png")
plt.savefig(out1, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close()
print(f"  Guardado: {out1}")

# ─── MAPA 2: Zonas de influencia por marca (Voronoi) ─────────────────────────
print("\nGenerando Mapa 2 — Voronoi por marca...")

fig, ax = plt.subplots(1, 1, figsize=(14, 10))
fig.patch.set_facecolor("#F8F8F8")
ax.set_facecolor("#D6EAF8")
trazar_capas_contexto(ax, radios.crs, capas_osm)

# Base: límite de radios
radios.dissolve().boundary.plot(ax=ax, color="grey", linewidth=0.5, zorder=1)

# Voronoi coloreado por marca
for marca, color in MARCA_COLORES.items():
    sub = voronoi[voronoi["marca"] == marca]
    sub.plot(ax=ax, color=color, alpha=0.45, edgecolor="white",
             linewidth=0.3, zorder=2)

# Puntos supermercados (negro, pequeños)
supers.plot(ax=ax, color="black", markersize=8, marker="o", zorder=5,
            edgecolor="white", linewidth=0.3)

# Leyenda marcas
handles = [mpatches.Patch(color=c, label=m, alpha=0.8)
           for m, c in MARCA_COLORES.items()]
ax.legend(handles=handles, title="Marca", loc="lower left",
          framealpha=0.9, fontsize=9)

ax.set_title("Zonas de influencia por marca — CABA",
             fontsize=14, fontweight="bold", pad=12)
quitar_ejes(ax)
plt.tight_layout()
out2 = os.path.join(SALIDA, "mapa2_voronoi_marcas.png")
plt.savefig(out2, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close()
print(f"  Guardado: {out2}")

# ─── MAPA 3: Radios sin cobertura 500m sobre IVH ─────────────────────────────
print("\nGenerando Mapa 3 — Radios sin cobertura sobre IVH...")

# Paleta para IVH_quintil (1=bajo, 5=alto)
IVH_CMAP = ListedColormap(get_cmap("YlOrRd", 5)(np.linspace(0, 1, 5)))
BOUNDS = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
NORM   = BoundaryNorm(BOUNDS, IVH_CMAP.N)

radios_plot = radios.copy()
radios_plot["IVH_quintil_num"] = pd.to_numeric(radios_plot["IVH_quintil"], errors="coerce")

fig, ax = plt.subplots(1, 1, figsize=(14, 10))
fig.patch.set_facecolor("#F8F8F8")
ax.set_facecolor("#D6EAF8")
trazar_capas_contexto(ax, radios_plot.crs, capas_osm)

# Coroplético base IVH
radios_plot.plot(
    ax=ax,
    column="IVH_quintil_num",
    cmap=IVH_CMAP,
    norm=NORM,
    edgecolor="none",
    linewidth=0,
    legend=False,
    missing_kwds={"color": "lightgrey"},
)

# Resaltar radios sin cobertura
sin_cobertura.plot(
    ax=ax,
    color="#8B0000",
    edgecolor="black",
    linewidth=0.6,
    zorder=4,
    label="Sin cobertura 500m",
)

# Leyenda IVH manual
ivh_colors = [get_cmap("YlOrRd")(i / 4) for i in range(5)]
ivh_handles = [mpatches.Patch(color=ivh_colors[i], label=f"Clase {i+1}")
               for i in range(5)]
ivh_handles.append(
    mpatches.Patch(color="#8B0000", label="Sin cobertura a 500m",
                   edgecolor="black", linewidth=0.8)
)
ax.legend(handles=ivh_handles, title="IVH / Cobertura",
          loc="lower left", framealpha=0.9, fontsize=9)

ax.set_title("Radios sin supermercado a 500m sobre IVH — CABA",
             fontsize=14, fontweight="bold", pad=12)
quitar_ejes(ax)
plt.tight_layout()
out3 = os.path.join(SALIDA, "mapa3_sin_cobertura_ivh.png")
plt.savefig(out3, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close()
print(f"  Guardado: {out3}")

# ─── MAPA 4: Subplots de ratios ────────────────────────────────────────────────
print("\nGenerando Mapa 4 — Subplots de ratios...")

CLASE_LABELS = [f"Clase {i}" for i in range(1, 6)]
BAR_COLOR    = "#4472C4"
PALETTE      = [MARCA_COLORES[m] for m in ["Carrefour", "Coto", "Disco", "Jumbo"]]

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.patch.set_facecolor("#FAFAFA")
fig.suptitle("Ratios de accesibilidad a supermercados por clase IVH — CABA",
             fontsize=14, fontweight="bold", y=1.01)

# ── Subplot 1: supers/km² por clase IVH ──
ax1 = axes[0, 0]
ax1.bar(CLASE_LABELS, r1["supers_por_km2"], color=BAR_COLOR, edgecolor="white", linewidth=0.5)
ax1.set_title("Ratio 1: Supermercados por km²", fontweight="bold", fontsize=11)
ax1.set_xlabel("Clase IVH")
ax1.set_ylabel("Supers / km²")
ax1.set_ylim(0, r1["supers_por_km2"].max() * 1.15)
for i, v in enumerate(r1["supers_por_km2"]):
    ax1.text(i, v + 0.01, f"{v:.2f}", ha="center", va="bottom", fontsize=8)
ax1.grid(axis="y", alpha=0.3)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

# ── Subplot 2: distancia promedio por clase IVH ──
ax2 = axes[0, 1]
ax2.bar(CLASE_LABELS, r2["media"], color="#E07B39", edgecolor="white", linewidth=0.5)
ax2.set_title("Ratio 2: Distancia promedio al super más cercano", fontweight="bold", fontsize=11)
ax2.set_xlabel("Clase IVH")
ax2.set_ylabel("Distancia (metros)")
ax2.set_ylim(0, r2["media"].max() * 1.15)
for i, v in enumerate(r2["media"]):
    ax2.text(i, v + 5, f"{v:.0f} m", ha="center", va="bottom", fontsize=8)
ax2.grid(axis="y", alpha=0.3)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

# ── Subplot 3: stacked barplot % marca por clase IVH ──
ax3 = axes[1, 0]
marcas = ["Carrefour", "Coto", "Disco", "Jumbo"]
bottom = np.zeros(len(r3))
for marca, color in zip(marcas, PALETTE):
    valores = r3[marca].values
    ax3.bar(CLASE_LABELS, valores, bottom=bottom, color=color,
            label=marca, edgecolor="white", linewidth=0.3)
    # Etiquetas solo si el segmento es suficientemente grande
    for i, (b, v) in enumerate(zip(bottom, valores)):
        if v > 5:
            ax3.text(i, b + v / 2, f"{v:.0f}%", ha="center", va="center",
                     fontsize=7.5, color="white", fontweight="bold")
    bottom += valores
ax3.set_title("Ratio 3: Distribución de marca por clase IVH", fontweight="bold", fontsize=11)
ax3.set_xlabel("Clase IVH")
ax3.set_ylabel("% radios por marca dominante (Voronoi)")
ax3.set_ylim(0, 110)
ax3.legend(title="Marca", loc="upper right", fontsize=8, framealpha=0.8)
ax3.grid(axis="y", alpha=0.3)
ax3.spines["top"].set_visible(False)
ax3.spines["right"].set_visible(False)

# ── Subplot 4: % sin cobertura por clase IVH ──
ax4 = axes[1, 1]
colores_r4 = plt.cm.Reds(np.linspace(0.3, 0.9, len(r4)))
bars = ax4.bar(CLASE_LABELS, r4["pct_sin_cobertura"], color=colores_r4,
               edgecolor="white", linewidth=0.5)
ax4.set_title("Ratio 4: % radios sin cobertura a 500m", fontweight="bold", fontsize=11)
ax4.set_xlabel("Clase IVH")
ax4.set_ylabel("% sin supermercado a 500m")
ax4.set_ylim(0, r4["pct_sin_cobertura"].max() * 1.15)
for i, v in enumerate(r4["pct_sin_cobertura"]):
    ax4.text(i, v + 0.5, f"{v:.1f}%", ha="center", va="bottom", fontsize=8)
ax4.grid(axis="y", alpha=0.3)
ax4.spines["top"].set_visible(False)
ax4.spines["right"].set_visible(False)

plt.tight_layout()
out4 = os.path.join(SALIDA, "ratios_resumen.png")
plt.savefig(out4, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close()
print(f"  Guardado: {out4}")

print("\nFase E - Mapas estaticos completados.")
print(f"  Directorio: {SALIDA}")
