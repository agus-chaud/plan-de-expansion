"""
Scraper de sucursales Carrefour en CABA.

Estrategia: interceptar la llamada GraphQL VTEX getStoreLocations via Playwright.
La página carga automáticamente todos los stores (681 en Argentina) en una sola
respuesta GraphQL de ~1.9MB al navegar a /sucursales.

Cada store tiene campos: businessName, addressLineOne, administrativeArea,
locality, latitude, longitude.

Nota sobre latitude: VTEX devuelve el valor como entero sin punto decimal,
p. ej. '-346274214' que representa '-34.6274214'. Se normaliza dividiendo
hasta que el valor sea un float válido en el rango [-90, 90].

Filtro: administrativeArea == 'Ciudad Autónoma de Buenos Aires'.
Sin geocoding.
"""

import csv
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path(__file__).parent.parent.parent / "02_datos_procesados" / "supermercados"
OUTPUT_FILE = OUTPUT_DIR / "carrefour.csv"

CABA_MARKER = "ciudad autónoma de buenos aires"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def es_caba(text: str) -> bool:
    return CABA_MARKER in text.lower()


def normalizar_coordenada(raw) -> float | None:
    """
    Normaliza una coordenada del formato VTEX Carrefour.
    El valor puede ser:
    - Un float ya correcto: '-34.6274214' -> -34.6274214
    - Un entero sin decimal: '-346274214' -> -34.6274214

    La estrategia: si el valor está fuera del rango válido para lat/lon,
    dividir por 10 hasta que entre en [-90, 90] para lat o [-180, 180] para lon.
    """
    if raw is None:
        return None
    try:
        val = float(raw)
    except (ValueError, TypeError):
        return None

    # Si ya está en rango válido (-90 a 90 para lat, similar para lon)
    if -180 <= val <= 180:
        return val

    # Dividir por 10 hasta entrar en rango
    for _ in range(10):
        val /= 10.0
        if -180 <= val <= 180:
            return val

    return None


def procesar_doc(doc: dict) -> dict | None:
    """
    Procesa un documento de store de Carrefour.
    Retorna dict con campos estandarizados o None si no es CABA.
    """
    fields = {f["key"]: f["value"] for f in doc.get("fields", [])}

    area = fields.get("administrativeArea", "") or ""
    locality = fields.get("locality", "") or ""

    # Filtrar CABA
    texto_loc = f"{area} {locality}"
    if not es_caba(texto_loc):
        return None

    nombre = fields.get("businessName", "Carrefour")
    direccion = fields.get("addressLineOne", "") or ""

    lat_raw = fields.get("latitude")
    lon_raw = fields.get("longitude")

    lat = normalizar_coordenada(lat_raw)
    lon = normalizar_coordenada(lon_raw)

    return {
        "marca": "Carrefour",
        "nombre": nombre,
        "direccion": direccion,
        "lat": lat,
        "lon": lon,
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_docs = []

    def on_response(response):
        content_type = response.headers.get("content-type", "")
        if "json" not in content_type:
            return
        if "graphql" not in response.url:
            return
        if response.status != 200:
            return
        try:
            body = response.body()
            if len(body) < 100_000:
                return
            data = json.loads(body)
            if isinstance(data, dict) and "documents" in data.get("data", {}):
                docs = data["data"]["documents"]
                print(f"  [INFO] Capturados {len(docs)} stores en respuesta GraphQL")
                all_docs.extend(docs)
        except Exception as e:
            print(f"  [WARN] Error procesando respuesta: {e}")

    print(f"[INFO] Navegando a Carrefour/sucursales con Playwright...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=UA,
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()
        page.on("response", on_response)

        try:
            page.goto(
                "https://www.carrefour.com.ar/sucursales",
                wait_until="domcontentloaded",
                timeout=45000,
            )
        except Exception as e:
            print(f"  [WARN] goto: {e}")

        # Esperar a que cargue el componente de stores
        print("  [INFO] Esperando carga de stores (12s)...")
        page.wait_for_timeout(12000)

        browser.close()

    print(f"[INFO] Total documentos capturados: {len(all_docs)}")

    if not all_docs:
        print("[ERROR] No se capturaron stores. Verificar conectividad o selector GraphQL.")
        return

    sucursales = []
    descartados = 0

    for doc in all_docs:
        resultado = procesar_doc(doc)
        if resultado is None:
            descartados += 1
        else:
            sucursales.append(resultado)

    # Deduplicar por nombre+dirección
    vistos = set()
    dedup = []
    for s in sucursales:
        key = (s["nombre"], s["direccion"])
        if key not in vistos:
            vistos.add(key)
            dedup.append(s)

    print(f"[INFO] Sucursales CABA encontradas: {len(dedup)}")
    print(f"[INFO] Descartadas (fuera de CABA): {descartados}")

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["marca", "nombre", "direccion", "lat", "lon"])
        writer.writeheader()
        writer.writerows(dedup)

    print(f"[OK] Guardado en {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
