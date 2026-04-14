"""
Scraper de sucursales Disco en CABA.

Estrategia: API VTEX Master Data (REST).
Endpoint: /api/dataentities/NT/search con header REST-Range para paginación.
Las coordenadas vienen directas en el campo geocoordinates (lat,lon separados por coma).
Filtro: grouping == 'CABA'.
Sin Playwright, sin geocoding.
"""

import csv
import time
from pathlib import Path

import requests

OUTPUT_DIR = Path(__file__).parent.parent.parent / "02_datos_procesados" / "supermercados"
OUTPUT_FILE = OUTPUT_DIR / "disco.csv"

BASE_URL = "https://www.disco.com.ar/api/dataentities/NT/search"
FIELDS = "name,grouping,geocoordinates,state,city,street,number,neighborhood,address"
CABA_GROUPING = "CABA"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def parsear_geocoordinates(raw: str) -> tuple[float | None, float | None]:
    """
    Parsea el campo geocoordinates de VTEX: '-34.5868357000000,-58.4109053000000'.
    Retorna (lat, lon) como float o (None, None) si falla.
    """
    if not raw:
        return None, None
    try:
        parts = raw.split(",")
        if len(parts) >= 2:
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())
            return lat, lon
    except (ValueError, AttributeError):
        pass
    return None, None


def fetch_all_stores() -> list[dict]:
    """Descarga todos los stores de Disco usando paginación con REST-Range."""
    all_stores = []
    batch_size = 100
    start = 0

    while True:
        end = start + batch_size - 1
        headers = {
            **HEADERS,
            "REST-Range": f"resources={start}-{end}",
        }
        params = {
            "_fields": FIELDS,
            "_where": "isActive=true",
            "_sort": "name ASC",
        }

        print(f"  [INFO] Fetching resources {start}-{end}...")
        response = requests.get(BASE_URL, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        batch = response.json()
        if not batch:
            break

        all_stores.extend(batch)
        print(f"  [INFO] Batch: {len(batch)} stores (total: {len(all_stores)})")

        # REST-Content-Range indica el total disponible
        content_range = response.headers.get("REST-Content-Range", "")
        # Formato: "resources 0-71/71"
        if "/" in content_range:
            try:
                total = int(content_range.split("/")[1])
                if len(all_stores) >= total:
                    break
            except ValueError:
                pass

        if len(batch) < batch_size:
            break

        start = end + 1
        time.sleep(0.5)

    return all_stores


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Descargando stores Disco via API VTEX Master Data...")
    all_stores = fetch_all_stores()
    print(f"[INFO] Total stores Disco: {len(all_stores)}")

    sucursales = []
    descartados = 0

    for store in all_stores:
        grouping = store.get("grouping", "")

        # Filtrar solo CABA
        if grouping != CABA_GROUPING:
            descartados += 1
            continue

        nombre = store.get("name", "Disco")
        geocoords = store.get("geocoordinates", "")
        lat, lon = parsear_geocoordinates(geocoords)

        # Construir dirección desde campos disponibles
        street = store.get("street", "") or ""
        number = store.get("number", "") or ""
        address = store.get("address", "") or ""

        if street and number:
            direccion = f"{street} {number}".strip()
        elif address:
            direccion = address.strip()
        else:
            direccion = nombre

        sucursales.append({
            "marca": "Disco",
            "nombre": nombre,
            "direccion": direccion,
            "lat": lat,
            "lon": lon,
        })

    print(f"[INFO] Stores CABA (grouping='{CABA_GROUPING}'): {len(sucursales)}")
    print(f"[INFO] Stores fuera de CABA descartados: {descartados}")

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["marca", "nombre", "direccion", "lat", "lon"])
        writer.writeheader()
        writer.writerows(sucursales)

    print(f"[OK] Guardado en {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
