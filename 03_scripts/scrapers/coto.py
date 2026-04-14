"""
Scraper de sucursales Coto en CABA.

Estrategia: HTML server-side rendered con tabla estática.
No hay coordenadas — se geocodifica cada dirección con Nominatim.
"""

import csv
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

URL = "https://www.coto.com.ar/sucursales/"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "02_datos_procesados" / "supermercados"
OUTPUT_FILE = OUTPUT_DIR / "coto.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def geocodificar_direccion(geocode, direccion: str) -> tuple[float | None, float | None]:
    """Geocodifica una dirección en CABA. Retorna (lat, lon) o (None, None) si falla."""
    query = f"{direccion}, Buenos Aires, Argentina"
    try:
        location = geocode(query)
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print(f"  [WARN] Geocoding falló para '{direccion}': {e}")
    return None, None


def parsear_direccion(raw: str) -> str | None:
    """
    Extrae solo la parte de la calle del campo dirección.
    Formato de entrada: "Agüero 616 - CAPITAL FEDERAL"
    Retorna "Agüero 616" (sin la ciudad al final).
    """
    if " - CAPITAL FEDERAL" in raw.upper():
        return raw.split(" - ")[0].strip()
    return None  # No es CABA


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Descargando {URL}...")
    response = requests.get(URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")
    tabla = soup.find("table")
    if not tabla:
        print("[ERROR] No se encontró la tabla de sucursales en el HTML.")
        return

    filas = tabla.find_all("tr")
    print(f"[INFO] Filas encontradas en tabla: {len(filas)}")

    geolocator = Nominatim(user_agent="ivh_caba_supermercados")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.1)

    sucursales = []
    for fila in filas:
        celdas = fila.find_all("td")
        if len(celdas) < 3:
            continue  # Saltar encabezado o filas incompletas

        # Columnas: Suc | Sucursal | Direccion | Tipo | ...
        nombre = celdas[1].get_text(strip=True)
        raw_dir = celdas[2].get_text(strip=True)

        direccion = parsear_direccion(raw_dir)
        if direccion is None:
            continue  # No es CABA

        print(f"  Geocodificando: {nombre} — {direccion}")
        lat, lon = geocodificar_direccion(geocode, direccion)

        sucursales.append({
            "marca": "Coto",
            "nombre": nombre,
            "direccion": direccion,
            "lat": lat,
            "lon": lon,
        })

    print(f"[INFO] Sucursales CABA encontradas: {len(sucursales)}")

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["marca", "nombre", "direccion", "lat", "lon"])
        writer.writeheader()
        writer.writerows(sucursales)

    print(f"[OK] Guardado en {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
