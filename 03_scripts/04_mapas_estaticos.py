"""
04_mapas_estaticos.py
=====================
Fase 4: Generar mapas coropléticos estaticos (PNG) usando el IVH final.

Prerequisito: Haber ejecutado 03_calculo_indicadores.py

Salida:
  - 04_mapas/estaticos/*.png
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")  # backend sin ventana

from osm_contexto import obtener_capas_contexto

# Paths
ROOT = Path(__file__).parent.parent
INPUT_GPKG = ROOT / "02_datos_procesados" / "radios_CABA_ivh_final.gpkg"
MAPAS_ESTATICOS = ROOT / "04_mapas" / "estaticos"
MAPAS_ESTATICOS.mkdir(parents=True, exist_ok=True)
LINK_EXCLUIR_RENDER: tuple[str, ...] = ("020141001", "020081207")

# Columnas a graficar y sus titulos
COLUMNAS_TITULOS = {
    "IVH": "Indice de Vulnerabilidad Habitacional (IVH)",
    "ivh_nbi": "NBI — Necesidades Basicas Insatisfechas",
    "ivh_hacinamiento": "Hacinamiento critico",
    "ivh_piso_tierra": "Viviendas con piso de tierra",
    "ivh_techo_precario": "Techo precario",
    "ivh_sin_agua_red": "Hogares sin agua de red",
    "ivh_sin_cloaca": "Hogares sin cloacas",
    "ivh_sin_gas_red": "Hogares sin gas de red",
    "ivh_desempleo": "Desempleo",
    "ivh_baja_educacion": "Baja educacion",
}


def trazar_capas_contexto(
    ax,
    crs_destino,
    capas: dict | None,
) -> None:
    """Dibuja cementerios, vías y avenidas OSM debajo del coropleta."""
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


def generar_mapa(
    gdf: gpd.GeoDataFrame,
    columna: str,
    titulo: str,
    capas: dict | None = None,
):
    """Generar y guardar un mapa coroplético para una variable."""
    # Filtrar filas sin dato para esa columna
    gdf_plot = gdf[gdf[columna].notna()].copy()
    if len(gdf_plot) == 0:
        print(f"SKIP: '{columna}' no tiene datos validos")
        return

    fig, ax = plt.subplots(1, 1, figsize=(10, 12))
    trazar_capas_contexto(ax, gdf_plot.crs, capas)
    gdf_plot.plot(
        column=columna,
        scheme="quantiles",
        k=5,
        cmap="YlOrRd",
        legend=True,
        ax=ax,
        zorder=3,
        missing_kwds={"color": "lightgrey", "label": "Sin datos"},
    )
    ax.set_title(f"{titulo}\nCABA — Censo 2022", fontsize=13, pad=12)
    ax.axis("off")
    output_path = MAPAS_ESTATICOS / f"{columna}.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Guardado: {output_path}")


def main():
    print("=== FASE 4: Mapas estaticos ===")
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

    print("Capas de contexto OSM (cementerios, vías, avenidas)...")
    capas_osm = obtener_capas_contexto(ROOT)
    if capas_osm is None:
        print("  Mapas sin capas OSM (sin caché y sin red o error en descarga).")
    else:
        print("  Capas OSM listas (desde caché o descarga).")

    for columna, titulo in COLUMNAS_TITULOS.items():
        if columna in gdf.columns:
            generar_mapa(gdf, columna, titulo, capas=capas_osm)
        else:
            print(f"SKIP: columna '{columna}' no encontrada en el GeoPackage")

    print("Fase 4 completada.")


if __name__ == "__main__":
    main()
