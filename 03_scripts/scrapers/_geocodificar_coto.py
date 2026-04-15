"""
Script auxiliar: geocodifica las sucursales Coto que quedaron sin coordenadas.

Lee coto.csv, identifica filas con lat/lon vacíos, las geocodifica
con Nominatim y sobreescribe el CSV con todas las coords disponibles.
"""

import csv
import time
from pathlib import Path

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

OUTPUT_DIR = Path(__file__).parent.parent.parent / "02_datos_procesados" / "supermercados"
COTO_CSV = OUTPUT_DIR / "coto.csv"


def geocodificar_con_reintentos(geolocator, direccion: str, max_intentos: int = 3) -> tuple:
    """
    Intenta geocodificar una dirección con reintentos.
    Aumenta el delay en cada intento fallido.
    """
    query = f"{direccion}, Buenos Aires, Argentina"
    for intento in range(max_intentos):
        try:
            time.sleep(1.2 + intento * 0.5)  # delay creciente entre reintentos
            result = geolocator.geocode(query, timeout=15)
            if result:
                return result.latitude, result.longitude
            return None, None
        except GeocoderTimedOut:
            print(f"    [TIMEOUT] intento {intento+1}/{max_intentos}: {direccion}")
            time.sleep(3 * (intento + 1))
        except GeocoderServiceError as e:
            print(f"    [ERROR] {e}")
            time.sleep(5)
        except Exception as e:
            print(f"    [ERROR] inesperado: {e}")
            break
    return None, None


def main():
    if not COTO_CSV.exists():
        print(f"[ERROR] No encontrado: {COTO_CSV}")
        return

    with open(COTO_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    sin_coords = [r for r in rows if not r.get("lat") or r["lat"].strip() in ("", "None")]
    con_coords_count = len(rows) - len(sin_coords)

    print(f"[INFO] Coto CSV: {len(rows)} sucursales")
    print(f"[INFO] Con coords: {con_coords_count}")
    print(f"[INFO] Sin coords (a geocodificar): {len(sin_coords)}")

    if not sin_coords:
        print("[OK] Todas las sucursales ya tienen coordenadas.")
        return

    geolocator = Nominatim(user_agent="ivh_caba_coto_v2", timeout=15)

    exitosas = 0
    fallidas = 0

    for i, row in enumerate(rows):
        if row.get("lat") and row["lat"].strip() not in ("", "None"):
            continue  # ya tiene coords

        direccion = row["direccion"]
        print(f"  [{i+1}/{len(rows)}] Geocodificando: {row['nombre']} — {direccion}")

        lat, lon = geocodificar_con_reintentos(geolocator, direccion)
        row["lat"] = lat
        row["lon"] = lon

        if lat:
            exitosas += 1
            print(f"    -> ({lat:.6f}, {lon:.6f})")
        else:
            fallidas += 1
            print(f"    -> SIN COORDS")

    # Sobreescribir CSV con coords actualizadas
    with open(COTO_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["marca", "nombre", "direccion", "lat", "lon"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n[OK] CSV actualizado: {exitosas} nuevas coords, {fallidas} fallidas")
    print(f"[OK] Guardado en {COTO_CSV}")


if __name__ == "__main__":
    main()
