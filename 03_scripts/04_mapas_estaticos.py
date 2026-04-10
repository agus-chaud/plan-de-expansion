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

# Paths
ROOT = Path(__file__).parent.parent
INPUT_GPKG = ROOT / "02_datos_procesados" / "radios_CABA_ivh_final.gpkg"
MAPAS_ESTATICOS = ROOT / "04_mapas" / "estaticos"
MAPAS_ESTATICOS.mkdir(parents=True, exist_ok=True)

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


def generar_mapa(gdf: gpd.GeoDataFrame, columna: str, titulo: str):
    """Generar y guardar un mapa coroplético para una variable."""
    # Filtrar filas sin dato para esa columna
    gdf_plot = gdf[gdf[columna].notna()].copy()
    if len(gdf_plot) == 0:
        print(f"SKIP: '{columna}' no tiene datos validos")
        return

    fig, ax = plt.subplots(1, 1, figsize=(10, 12))
    gdf_plot.plot(
        column=columna,
        scheme="quantiles",
        k=5,
        cmap="YlOrRd",
        legend=True,
        ax=ax,
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

    for columna, titulo in COLUMNAS_TITULOS.items():
        if columna in gdf.columns:
            generar_mapa(gdf, columna, titulo)
        else:
            print(f"SKIP: columna '{columna}' no encontrada en el GeoPackage")

    print("Fase 4 completada.")


if __name__ == "__main__":
    main()
