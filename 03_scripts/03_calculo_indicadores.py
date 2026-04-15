"""
03_calculo_indicadores.py
=========================
Fase 3: Calcular el Indice de Vulnerabilidad Habitacional (IVH).

Promedia igual peso los 8 indicadores ivh_* seleccionados (sin NBI por
multicolinealidad) y clasifica por Natural Breaks (Jenks) en 5 clases.
Mayor IVH = mayor vulnerabilidad.

Prerequisito: Haber ejecutado 02_join_espacial.py

Salida:
  - 02_datos_procesados/radios_CABA_ivh_final.gpkg
  - 04_mapas/correlacion_variables_ivh.png
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import mapclassify

# Paths
ROOT = Path(__file__).parent.parent
INPUT_GPKG  = ROOT / "02_datos_procesados" / "radios_CABA_ivh.gpkg"
OUTPUT_GPKG = ROOT / "02_datos_procesados" / "radios_CABA_ivh_final.gpkg"
MAPAS_DIR   = ROOT / "04_mapas"

# ---------------------------------------------------------------------------
# Variables candidatas para el IVH (incluye ivh_nbi solo para correlacion)
# ---------------------------------------------------------------------------
VARS_CANDIDATAS = [
    "ivh_piso_tierra",
    "ivh_techo_precario",
    "ivh_sin_agua_red",
    "ivh_sin_cloaca",
    "ivh_sin_gas_red",
    "ivh_hacinamiento",
    "ivh_nbi",           # excluida del promedio, conservada para validacion
    "ivh_desempleo",
    "ivh_baja_educacion_univ",  # derivada de ivh_con_educacion_univ (invertida)
]

# ivh_nbi se EXCLUYE del promedio del IVH porque el NBI incorpora por definicion
# dimensiones de hacinamiento, condiciones habitacionales, saneamiento y educacion.
# Incluirlo daria doble peso a esas dimensiones (multicolinealidad alta, r > 0.6
# con varias otras variables). Se conserva la columna para validacion visual.
VARS_IVH = [
    "ivh_piso_tierra",
    "ivh_techo_precario",
    "ivh_sin_agua_red",
    "ivh_sin_cloaca",
    "ivh_sin_gas_red",
    "ivh_hacinamiento",
    "ivh_desempleo",
    "ivh_baja_educacion_univ",
]

# Radios con muy pocas viviendas (p. ej. hipódromo, aeropuerto) distorsionan IVH y quintiles.
MIN_VIVIENDAS_POR_RADIO = 10

# Criterio B: exclusion manual por LINK del MGN cuando el criterio A no alcanza.
# Derivados de join espacial OSM -> radios (aeroparque + autodromo).
LINK_EXCLUIR_MANUAL: tuple[str, ...] = (
    "020141001",  # Aeroparque Jorge Newbery
    "020081207",  # Autodromo Oscar y Juan Galvez
)


def filtrar_radios_base_habitacional(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Excluye radios sin base habitacional suficiente (viviendas_tot/h14_total < umbral) y,
    opcionalmente, LINK listados en LINK_EXCLUIR_MANUAL.
    """
    n0 = len(gdf)
    columna_viviendas = None
    if "viviendas_tot" in gdf.columns:
        columna_viviendas = "viviendas_tot"
    elif "h14_total" in gdf.columns:
        columna_viviendas = "h14_total"

    if columna_viviendas is None:
        print(
            "  ADVERTENCIA: no hay viviendas_tot ni h14_total; no se aplica filtro por viviendas."
        )
        gdf_out = gdf.copy()
    else:
        viviendas = pd.to_numeric(gdf[columna_viviendas], errors="coerce")
        mask = viviendas.fillna(0) >= MIN_VIVIENDAS_POR_RADIO
        if LINK_EXCLUIR_MANUAL and "LINK" in gdf.columns:
            mask = mask & ~gdf["LINK"].isin(LINK_EXCLUIR_MANUAL)
        gdf_out = gdf.loc[mask].copy()

    excluidos = n0 - len(gdf_out)
    detalle = (
        f"{columna_viviendas} >= {MIN_VIVIENDAS_POR_RADIO}"
        if columna_viviendas is not None
        else "sin columna de viviendas"
    )
    print(f"  Filtro base habitacional ({detalle}): {n0} -> {len(gdf_out)} radios ({excluidos} excluidos)")
    if LINK_EXCLUIR_MANUAL:
        print(f"  Exclusiones manuales activas (LINK): {', '.join(LINK_EXCLUIR_MANUAL)}")
    return gdf_out


def preparar_variable_educacion(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Asegura que exista ivh_baja_educacion_univ (mayor = mas vulnerable).

    Casos posibles segun el estado del pipeline:
      A) ivh_con_educacion_univ presente (script 01 actualizado ya ejecutado):
         Se invierte -> ivh_baja_educacion_univ = 1 - ivh_con_educacion_univ
      B) Solo ivh_baja_educacion_univ ya existe: no hace nada.
      C) Solo ivh_baja_educacion presente (GeoPackage generado con version antigua
         del script 01): se usa directamente como fallback renombrando en memoria.
    """
    if "ivh_con_educacion_univ" in gdf.columns:
        gdf["ivh_baja_educacion_univ"] = 1 - gdf["ivh_con_educacion_univ"]
        print("  ivh_baja_educacion_univ calculada (= 1 - ivh_con_educacion_univ)")
    elif "ivh_baja_educacion_univ" in gdf.columns:
        print("  ivh_baja_educacion_univ ya presente; no se recalcula.")
    elif "ivh_baja_educacion" in gdf.columns:
        # Fallback: GeoPackage generado con pipeline anterior (script 01 sin actualizar)
        gdf["ivh_baja_educacion_univ"] = gdf["ivh_baja_educacion"]
        print("  FALLBACK: usando ivh_baja_educacion como ivh_baja_educacion_univ")
        print("  (Regenerar el pipeline completo cuando script 01 este actualizado)")
    else:
        print("  ADVERTENCIA: no se encontro ninguna columna de educacion reconocida.")
    return gdf


def analizar_correlacion_nbi(gdf: gpd.GeoDataFrame) -> None:
    """
    Calcula y muestra la correlacion de Pearson entre ivh_nbi y las demas
    variables candidatas al IVH. Guarda un heatmap en 04_mapas/.
    """
    print("\n--- Correlacion de Pearson: ivh_nbi vs. resto de variables ---")

    vars_presentes = [v for v in VARS_CANDIDATAS if v in gdf.columns]
    if "ivh_nbi" not in vars_presentes:
        print("  ivh_nbi no encontrada en el GeoDataFrame; se omite analisis.")
        return

    corr_matrix = gdf[vars_presentes].corr(method="pearson")
    corr_nbi = corr_matrix["ivh_nbi"].drop("ivh_nbi").sort_values(ascending=False)

    print("  Correlaciones con ivh_nbi:")
    for var, r in corr_nbi.items():
        marca = "  *** r > 0.6 (multicolinealidad)" if abs(r) > 0.6 else ""
        print(f"    {var:30s}: r = {r:.4f}{marca}")

    # Heatmap completo de todas las variables candidatas
    MAPAS_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        center=0,
        vmin=-1,
        vmax=1,
        ax=ax,
        linewidths=0.5,
    )
    ax.set_title(
        "Correlacion de Pearson entre variables candidatas al IVH\n"
        "(ivh_nbi excluida del promedio por multicolinealidad)",
        fontsize=11,
    )
    plt.tight_layout()
    heatmap_path = MAPAS_DIR / "correlacion_variables_ivh.png"
    fig.savefig(heatmap_path, dpi=150)
    plt.close(fig)
    print(f"  Heatmap guardado en: {heatmap_path}")


def calcular_ivh(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Calcular IVH como promedio de igual peso de los 8 indicadores (sin NBI)."""
    vars_presentes = [v for v in VARS_IVH if v in gdf.columns]
    if len(vars_presentes) < len(VARS_IVH):
        faltantes = set(VARS_IVH) - set(vars_presentes)
        print(f"  ADVERTENCIA: faltan columnas: {faltantes}")
    if not vars_presentes:
        raise ValueError("No se encontro ninguna columna IVH en el GeoDataFrame.")

    # IVH en escala 0-1 (proporciones), promedio simple
    gdf["IVH"] = gdf[vars_presentes].mean(axis=1)
    return gdf


def calcular_quintiles_jenks(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Clasifica IVH en 5 clases usando Natural Breaks (Jenks).
    Labels: 1 = menor vulnerabilidad, 5 = mayor vulnerabilidad.
    Reemplaza el qcut anterior para obtener cortes mas significativos.
    """
    gdf_valid = gdf[gdf["IVH"].notna()].copy()
    if len(gdf_valid) < 5:
        print("  ADVERTENCIA: menos de 5 radios validos; no se calculan quintiles.")
        gdf["IVH_quintil"] = pd.NA
        return gdf

    nb = mapclassify.NaturalBreaks(y=gdf_valid["IVH"].values, k=5)

    # mapclassify asigna labels 0-4; sumamos 1 para obtener 1-5
    gdf["IVH_quintil"] = pd.NA
    gdf.loc[gdf_valid.index, "IVH_quintil"] = pd.array(nb.yb + 1, dtype="Int64")

    print(f"\n  Cortes Natural Breaks (Jenks) para IVH (k=5):")
    print(f"    bins: {[round(b, 4) for b in nb.bins]}")
    for i, (low, high) in enumerate(
        zip([gdf_valid['IVH'].min()] + list(nb.bins[:-1]), nb.bins), start=1
    ):
        print(f"    Clase {i}: [{low:.4f}, {high:.4f}]")

    return gdf


def main():
    print("=== FASE 3: Calculo de IVH ===")
    print(f"Leyendo: {INPUT_GPKG}")
    gdf = gpd.read_file(INPUT_GPKG)
    print(f"Radios cargados: {len(gdf)}")

    # Paso 0: derivar variable de educacion invertida
    gdf = preparar_variable_educacion(gdf)

    # Paso 0b: excluir radios casi sin viviendas (grandes superficies no residenciales)
    gdf = filtrar_radios_base_habitacional(gdf)

    # Paso 1: analisis de correlacion con NBI (antes del calculo del IVH)
    analizar_correlacion_nbi(gdf)

    # Paso 2: calcular IVH (promedio de 8 variables, sin NBI)
    gdf = calcular_ivh(gdf)

    # Paso 3: clasificar por Natural Breaks en lugar de qcut
    gdf = calcular_quintiles_jenks(gdf)

    print(f"\nIVH calculado. Rango: {gdf['IVH'].min():.4f} — {gdf['IVH'].max():.4f}")
    print(f"IVH promedio: {gdf['IVH'].mean():.4f}")
    print(f"Distribucion de clases (Natural Breaks):\n{gdf['IVH_quintil'].value_counts().sort_index()}")

    gdf.to_file(OUTPUT_GPKG, driver="GPKG")
    print(f"\nGuardado: {OUTPUT_GPKG}")
    print("Fase 3 completada.")


if __name__ == "__main__":
    main()
