"""
Script de diagnóstico: intercepta requests de red para descubrir
la API que usan Jumbo, Disco y Carrefour para cargar sus stores.
"""
import json
from playwright.sync_api import sync_playwright

SITIOS = [
    ("jumbo", "https://www.jumbo.com.ar/sucursales"),
    ("disco", "https://www.disco.com.ar/sucursales"),
    ("carrefour", "https://www.carrefour.com.ar/sucursales"),
]

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def investigar(nombre, url):
    print(f"\n{'='*60}")
    print(f"INVESTIGANDO: {nombre} -> {url}")
    print('='*60)

    responses_capturadas = []

    def on_response(response):
        url_r = response.url
        content_type = response.headers.get("content-type", "")
        # Solo JSON y URLs que puedan contener stores
        if "json" in content_type and any(k in url_r.lower() for k in [
            "store", "sucursal", "branch", "location", "search", "pickup", "loja"
        ]):
            try:
                body = response.body()
                data = json.loads(body)
                responses_capturadas.append({
                    "url": url_r,
                    "status": response.status,
                    "size": len(body),
                    "data_preview": str(data)[:300],
                })
                print(f"  [CAPTURADO] {response.status} {url_r[:100]}")
                print(f"    Content-Type: {content_type}")
                print(f"    Size: {len(body)} bytes")
                print(f"    Preview: {str(data)[:200]}")
            except Exception as e:
                pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=UA,
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()
        page.on("response", on_response)

        print(f"  Navegando (domcontentloaded)...")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"  [WARN] goto error: {e}")

        print(f"  Esperando 8s para que React cargue los stores...")
        page.wait_for_timeout(8000)

        # Si es Jumbo/Disco, intentar seleccionar Capital Federal
        try:
            select_opts = page.query_selector_all("select option")
            for opt in select_opts:
                txt = opt.inner_text().strip()
                if "capital" in txt.lower():
                    page.select_option("select", label=txt)
                    print(f"  [SELECT] Seleccionado: {txt}")
                    page.wait_for_timeout(5000)
                    break
        except Exception:
            pass

        print(f"\n  Total requests JSON de stores capturadas: {len(responses_capturadas)}")

        # También mostrar TODAS las requests JSON aunque no sean de stores
        print("\n  Todas las requests JSON (para referencia):")
        all_json = []

        def on_response2(response):
            if "json" in response.headers.get("content-type", ""):
                all_json.append(response.url)

        # Ya no podemos agregar otro listener, mostrar lo que tenemos
        browser.close()

    return responses_capturadas


for nombre, url in SITIOS:
    resultado = investigar(nombre, url)
    if resultado:
        print(f"\n[RESULTADO {nombre.upper()}]")
        for r in resultado:
            print(f"  URL: {r['url']}")
            print(f"  Preview: {r['data_preview'][:200]}")
