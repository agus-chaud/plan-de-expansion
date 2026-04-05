"""
04_mapas_estaticos.py
=====================
Fase 4: Generar mapas coropléticos estaticos (PNG) por variable y para el IVH.

Prerequisito: Haber ejecutado 03_calculo_indicadores.py

Salida:
  - 04_mapas/estaticos/*.png (uno por variable + IVH)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import geopandas as gpd
import matplotlib.pyplot as plt
from utils import RESULTADO_GPKG, MAPAS_ESTATICOS, VARS_IVH


TITULOS = {
    "pct_hacinamiento": "Hacinamiento crítico",
    "pct_sin_agua_red": "Hogares sin agua de red",
    "pct_sin_cloaca": "Hogares sin cloacas",
    "pct_piso_tierra": "Viviendas con piso de tierra",
    "pct_sin_secundario": "Población sin secundario completo",
    "pct_sin_gas_red": "Hogares sin gas de red",
    "IVH": "Índice de Vulnerabilidad Habitacional (IVH)",
}


def generar_mapa(gdf: gpd.GeoDataFrame, columna: str, titulo: str):
    """Generar y guardar un mapa coroplético para una variable."""
    fig, ax = plt.subplots(1, 1, figsize=(10, 12))
    gdf.plot(
        column=columna,
        scheme="quantiles",
        k=5,
        cmap="YlOrRd",
        legend=True,
        legend_kwds={"label": titulo, "orientation": "horizontal"},
        ax=ax,
        missing_kwds={"color": "lightgrey", "label": "Sin datos"},
    )
    ax.set_title(f"{titulo}\nCABA — Censo 2022", fontsize=14, pad=12)
    ax.axis("off")
    output_path = MAPAS_ESTATICOS / f"{columna}.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Guardado: {output_path}")


def main():
    print("=== FASE 4: Mapas estaticos ===")
    gdf = gpd.read_file(RESULTADO_GPKG)
    variables = VARS_IVH + ["IVH"]
    for var in variables:
        if var in gdf.columns:
            generar_mapa(gdf, var, TITULOS.get(var, var))
        else:
            print(f"SKIP: columna '{var}' no encontrada")
    print("Fase 4 completada.")


if __name__ == "__main__":
    main()
