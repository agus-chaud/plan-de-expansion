"""
01_descarga_y_limpieza.py
=========================
Fase 1: Cargar los 6 CSV de REDATAM exportados por RedatamX,
        mergearlos por radio censal (codigo) y calcular los
        indicadores del IVH (Indice de Vulnerabilidad Habitacional).

Salida:
  - 02_datos_procesados/datos_censo_CABA.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
CSV_DIR  = BASE_DIR / "01_datos_raw" / "censo_2022" / "redatam_exports" / "csv_output"
OUT_DIR  = BASE_DIR / "02_datos_procesados"
OUT_CSV  = OUT_DIR / "datos_censo_CABA.csv"

JOIN_KEY = "codigo"

# ---------------------------------------------------------------------------
# Archivos CSV a cargar
# ---------------------------------------------------------------------------
CSV_FILES = [
    "hacinamiento_materiales_CABA.csv",
    "nbi_por_radio_CABA.csv",
    "servicios_habitacionales_CABA.csv",
    "techo_CABA.csv",
    "educacion_por_radio_CABA.csv",
    "poblacion_por_radio_CABA.csv",
]


def safe_div(num: pd.Series, denom: pd.Series) -> pd.Series:
    """Division segura: retorna NaN cuando el denominador es 0."""
    num   = pd.to_numeric(num,   errors="coerce")
    denom = pd.to_numeric(denom, errors="coerce")
    return np.where(denom > 0, num / denom, np.nan)


def cargar_csv(nombre: str) -> pd.DataFrame:
    """Cargar un CSV con deteccion automatica de encoding."""
    ruta = CSV_DIR / nombre
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            df = pd.read_csv(ruta, encoding=enc, dtype=str)
            df[JOIN_KEY] = df[JOIN_KEY].str.zfill(9)
            df = df[df[JOIN_KEY].str.startswith("02")].reset_index(drop=True)
            # Convertir todas las columnas numericas (todo excepto JOIN_KEY)
            num_cols = [c for c in df.columns if c != JOIN_KEY]
            df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
            print(f"  [OK] {nombre:45s} -> {len(df):5d} radios  (enc: {enc})")
            return df
        except (UnicodeDecodeError, KeyError):
            continue
    raise ValueError(f"No se pudo leer {nombre} con ningun encoding conocido")


def main():
    print("=== FASE 1: Carga, merge y calculo de indicadores IVH ===\n")

    # 1. Crear directorio de salida si no existe
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Cargar todos los CSV
    print("Cargando archivos CSV:")
    dfs = [cargar_csv(f) for f in CSV_FILES]

    # 3. Merge secuencial sobre JOIN_KEY
    print(f"\nMergeando {len(dfs)} tablas sobre '{JOIN_KEY}'...")
    merged = dfs[0]
    for df in dfs[1:]:
        merged = merged.merge(df, on=JOIN_KEY, how="inner")
    print(f"Filas tras merge: {len(merged)}")
    print(f"Columnas antes de indicadores: {len(merged.columns)}")

    # 4. Calcular indicadores IVH
    # --- Piso de tierra ---
    merged["ivh_piso_tierra"] = safe_div(
        merged["h10_tierra"],
        merged["h10_total"]
    )

    # --- Techo precario ---
    techo_precario = (
        merged["h1112_chapa_carton"]
        + merged["h1112_cana_paja"]
        + merged["h1112_plastico"]
        + merged["h1112_tierra_barro"]
        + merged["h1112_piedra"]
    )
    merged["ivh_techo_precario"] = safe_div(techo_precario, merged["h1112_total"])

    # --- Sin agua de red (incluye todas las alternativas a red publica) ---
    # Columnas reales: h14_perforacion_motor, h14_perforacion_manual, h14_pozo, h14_otra
    # (no hay h14_camion / h14_rio en este dataset; se usan todas las no-red)
    sin_agua = (
        merged["h14_perforacion_motor"]
        + merged["h14_perforacion_manual"]
        + merged["h14_pozo"]
        + merged["h14_otra"]
    )
    merged["ivh_sin_agua_red"] = safe_div(sin_agua, merged["h14_total"])

    # --- Sin cloaca de red ---
    # Columnas reales: h18_camara_pozo, h18_solo_pozo, h18_hoyo
    sin_cloaca = (
        merged["h18_camara_pozo"]
        + merged["h18_solo_pozo"]
        + merged["h18_hoyo"]
    )
    merged["ivh_sin_cloaca"] = safe_div(sin_cloaca, merged["h18_total"])

    # --- Sin gas de red ---
    # h19_gas_red es la columna directa de hogares con gas de red.
    # ivh_sin_gas_red = 1 - proporcion_con_gas_red  (alto = mas vulnerable)
    merged["ivh_sin_gas_red"] = 1 - safe_div(merged["h19_gas_red"], merged["h19_total"])

    # --- Hacinamiento critico (>= 1.5 personas por cuarto) ---
    hacin_critico = (
        merged["hacina_150_199"]
        + merged["hacina_200_300"]
        + merged["hacina_mas300"]
    )
    merged["ivh_hacinamiento"] = safe_div(hacin_critico, merged["hacina_total"])

    # --- NBI ---
    merged["ivh_nbi"] = safe_div(merged["nbi_tot_si"], merged["nbi_tot_total"])

    # --- Desempleo ---
    pea = merged["condact_ocupado"] + merged["condact_desocupado"]
    merged["ivh_desempleo"] = safe_div(merged["condact_desocupado"], pea)

    # --- Educacion universitaria completa ---
    # Proporcion de poblacion con universitario completo (alto = mejor situacion educativa).
    # En el calculo del IVH (03_calculo_indicadores.py) se usa como 1 - ivh_con_educacion_univ.
    merged["ivh_con_educacion_univ"] = safe_div(
        merged["p08_universitario_comp"], merged["p08_total"]
    )

    # 5. Guardar
    merged.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\nGuardado: {OUT_CSV}")

    # 6. Resumen
    ivh_cols = [c for c in merged.columns if c.startswith("ivh_")]
    print(f"\n{'='*55}")
    print(f"RESUMEN FINAL")
    print(f"{'='*55}")
    print(f"Filas (radios censales): {len(merged)}")
    print(f"Columnas totales:        {len(merged.columns)}")
    print(f"\nMedia de indicadores IVH:")
    for col in ivh_cols:
        media = merged[col].mean()
        print(f"  {col:<25s}: {media:.4f}  ({media*100:.2f}%)")
    print(f"{'='*55}")
    print("\nFase 1 completada.")


if __name__ == "__main__":
    main()
