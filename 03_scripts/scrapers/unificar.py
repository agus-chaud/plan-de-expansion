"""
Unificador de CSVs de supermercados.

Lee los 4 CSVs individuales (coto.csv, disco.csv, jumbo.csv, carrefour.csv)
desde 02_datos_procesados/supermercados/ y los combina en supermercados_CABA.csv.

Valida que cada archivo exista y tiene el formato correcto antes de combinar.
El CSV final mantiene el orden: coto → disco → jumbo → carrefour.
"""

import csv
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
OUTPUT_DIR = BASE_DIR / "02_datos_procesados" / "supermercados"
OUTPUT_FILE = OUTPUT_DIR / "supermercados_CABA.csv"

ARCHIVOS = [
    ("Coto", OUTPUT_DIR / "coto.csv"),
    ("Disco", OUTPUT_DIR / "disco.csv"),
    ("Jumbo", OUTPUT_DIR / "jumbo.csv"),
    ("Carrefour", OUTPUT_DIR / "carrefour.csv"),
]

COLUMNAS = ["marca", "nombre", "direccion", "lat", "lon"]


def leer_csv(path: Path, marca_esperada: str) -> list[dict]:
    """Lee un CSV de sucursales y valida su estructura."""
    if not path.exists():
        print(f"  [WARN] Archivo no encontrado: {path}")
        return []

    filas = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Validar columnas
        columnas_faltantes = set(COLUMNAS) - set(reader.fieldnames or [])
        if columnas_faltantes:
            print(f"  [WARN] {path.name} le faltan columnas: {columnas_faltantes}")

        for fila in reader:
            # Asegurar que la columna marca tenga el valor correcto
            if not fila.get("marca"):
                fila["marca"] = marca_esperada
            filas.append({col: fila.get(col, "") for col in COLUMNAS})

    return filas


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    todas = []
    resumen = {}

    for marca, path in ARCHIVOS:
        filas = leer_csv(path, marca)
        resumen[marca] = len(filas)
        todas.extend(filas)
        print(f"  [{marca}] {len(filas)} sucursales")

    if not todas:
        print("[ERROR] No se encontró ningún archivo de sucursales. Ejecutá primero los scrapers individuales.")
        sys.exit(1)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNAS)
        writer.writeheader()
        writer.writerows(todas)

    total = len(todas)
    print(f"\n[OK] {OUTPUT_FILE}")
    print(f"     Total: {total} sucursales CABA")
    for marca, n in resumen.items():
        pct = (n / total * 100) if total else 0
        print(f"     - {marca}: {n} ({pct:.1f}%)")


if __name__ == "__main__":
    main()
