"""
REDATAM query scraper - queries INDEC REDATAM web portal via Python requests.

Key discoveries:
- Must use X-Requested-With: XMLHttpRequest (server returns async iframe URL, not blocking HTML)
- Must use SELECTION PROV 02 to restrict to CABA (~3820 radios) — without it, 52K Argentine
  radios are returned and the output HTML exceeds the server's file size limit (Error 301)
- Server returns wrapper HTML with <iframe src="/redarg//tempo/SESSION/~tmp_XXXXX.htm">
  pointing to the actual result table
"""
import requests
import re
import time
import csv
import os
from html.parser import HTMLParser

BASE_URL = "https://redatam.indec.gob.ar"
PORTAL_URL = f"{BASE_URL}/binarg/RpWebEngine.exe/Portal?BASE=CPV2022&lang=ESP"
FORM_URL = f"{BASE_URL}/binarg/RpWebStats.exe/CmdSet?BASE=CPV2022&ITEM=PROGVIVPART&lang=ESP"
POST_URL = f"{BASE_URL}/binarg/RpWebStats.exe/CmdSet?"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__)) + "/csv_output"

# SELECTION header used in all programs to restrict to CABA province
SELECTION_CABA = "RUNDEF Job\n    SELECTION INLINE,\n     PROV 02\n\n"

QUERIES = [
    # ── Hacinamiento + materiales del piso ──────────────────────────────────
    {
        "name": "hacinamiento_materiales",
        "filename": "hacinamiento_materiales_CABA.csv",
        "program": (
            SELECTION_CABA +
            "TABLE t01\n"
            '    TITLE "Hacinamiento y materiales del piso - CABA"\n'
            "    AS AREALIST\n"
            "    OF RADIO, HOGAR.H10, HOGAR.H20_HACINA"
        ),
        "headers": [
            "codigo",
            "h10_ceramica","h10_carpeta","h10_tierra","h10_otro","h10_total",
            "hacina_0_50","hacina_51_99","hacina_100_149","hacina_150_199",
            "hacina_200_300","hacina_mas300","hacina_total",
        ],
    },
    # ── NBI ─────────────────────────────────────────────────────────────────
    {
        "name": "nbi",
        "filename": "nbi_por_radio_CABA.csv",
        "program": (
            SELECTION_CABA +
            "TABLE t02\n"
            '    TITLE "NBI por radio censal - CABA"\n'
            "    AS AREALIST\n"
            "    OF RADIO, HOGAR.NBI_TOT, HOGAR.NBI_HAC, HOGAR.NBI_VIV,"
            " HOGAR.NBI_SAN, HOGAR.NBI_ESC, HOGAR.NBI_SUB"
        ),
        "headers": [
            "codigo",
            "nbi_tot_si","nbi_tot_no","nbi_tot_total",
            "nbi_hac_si","nbi_hac_no","nbi_hac_total",
            "nbi_viv_si","nbi_viv_no","nbi_viv_total",
            "nbi_san_si","nbi_san_no","nbi_san_total",
            "nbi_esc_si","nbi_esc_no","nbi_esc_total",
            "nbi_sub_si","nbi_sub_no","nbi_sub_total",
        ],
    },
    # ── Servicios habitacionales: agua, cloaca, gas ─────────────────────────
    {
        "name": "servicios_habitacionales",
        "filename": "servicios_habitacionales_CABA.csv",
        "program": (
            SELECTION_CABA +
            "TABLE t03\n"
            '    TITLE "Servicios habitacionales - CABA"\n'
            "    AS AREALIST\n"
            "    OF RADIO, HOGAR.H14, HOGAR.H18, HOGAR.H19"
        ),
        "headers": None,  # auto-detect
    },
    # ── Techo ────────────────────────────────────────────────────────────────
    {
        "name": "techo",
        "filename": "techo_CABA.csv",
        "program": (
            SELECTION_CABA +
            "TABLE t04\n"
            '    TITLE "Materiales del techo - CABA"\n'
            "    AS AREALIST\n"
            "    OF RADIO, HOGAR.H11_H12"
        ),
        "headers": None,
    },
    # ── Educación ────────────────────────────────────────────────────────────
    # NIVEL_ED does not exist in CPV2022; correct vars are P08 (nivel educativo)
    # and CONDACT (condición de actividad — processed categorical)
    {
        "name": "educacion",
        "filename": "educacion_por_radio_CABA.csv",
        "program": (
            SELECTION_CABA +
            "TABLE t05\n"
            '    TITLE "Educacion y actividad - CABA"\n'
            "    AS AREALIST\n"
            "    OF RADIO, PERSONA.P08, PERSONA.CONDACT"
        ),
        "headers": None,
    },
    # ── Población básica ─────────────────────────────────────────────────────
    {
        "name": "poblacion",
        "filename": "poblacion_por_radio_CABA.csv",
        "program": (
            SELECTION_CABA +
            "TABLE t06\n"
            '    TITLE "Poblacion basica por radio - CABA"\n'
            "    AS AREALIST\n"
            "    OF RADIO, PERSONA.P02, PERSONA.EDADGRU"
        ),
        # P02 (sexo): varon, mujer, total
        # EDADGRU (CPV2022): 0-14, 15-64, 65+, total
        "headers": [
            "codigo",
            "p02_varon", "p02_mujer", "p02_total",
            "edadgru_0_14", "edadgru_15_64", "edadgru_65_mas", "edadgru_total",
        ],
    },
]

RADIO_RE = re.compile(r"^02\d{7}$")


class RowExtractor(HTMLParser):
    """Streaming HTML parser — only stores CABA radio rows."""

    def __init__(self):
        super().__init__()
        self.rows = []
        self._row = []
        self._cell = None
        self._in_table = False

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._in_table = True
        elif tag == "tr" and self._in_table:
            self._row = []
        elif tag in ("td", "th") and self._in_table:
            self._cell = ""

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            self._row.append(self._cell.strip())
            self._cell = None
        elif tag == "tr":
            if self._row:
                # Keep row if second cell is a 9-digit CABA code
                code = self._row[1] if len(self._row) > 1 else ""
                if RADIO_RE.match(code):
                    self.rows.append(self._row[:])
            self._row = []
        elif tag == "table":
            self._in_table = False

    def handle_data(self, data):
        if self._cell is not None:
            self._cell += data


def make_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "text/html, */*; q=0.01",
        "Referer": FORM_URL,
    })
    s.get(PORTAL_URL, timeout=30)
    s.get(FORM_URL, timeout=30)
    return s


def run_query(session, program, name):
    post_data = {
        "MAIN": "WebServerMain.inl",
        "BASE": "CPV2022",
        "LANG": "ESP",
        "CODIGO": "XXUSUARIOXX",
        "ITEM": "PROGVIVPART",
        "MODE": "RUN",
        "CMDSET": program,
    }
    print(f"  Submitting '{name}'...")
    t0 = time.time()
    resp = session.post(POST_URL, data=post_data, timeout=600)
    resp.raise_for_status()
    elapsed = time.time() - t0
    print(f"  Response in {elapsed:.0f}s")

    iframe_m = re.search(r'<iframe[^>]+src="(/redarg/+tempo/[^"]+\.htm)"', resp.text)
    if not iframe_m:
        raise RuntimeError(f"No iframe in response:\n{resp.text[:500]}")

    result_url = BASE_URL + iframe_m.group(1)
    print(f"  Fetching: {result_url}")
    r2 = session.get(result_url, timeout=120)
    r2.raise_for_status()
    print(f"  Result: {len(r2.content):,} bytes")
    return r2.text


def extract_and_save(html, filename, headers):
    parser = RowExtractor()
    parser.feed(html)
    rows = parser.rows
    print(f"  CABA rows: {len(rows)}")

    if not rows:
        raise RuntimeError("No CABA rows found")

    n_cols = len(rows[0])
    if headers and len(headers) == n_cols:
        final_headers = headers
    else:
        final_headers = ["codigo"] + [f"col_{i}" for i in range(1, n_cols)]
        print(f"  Auto-headers: {final_headers[:8]}...")

    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(final_headers)
        for row in rows:
            w.writerow(row[:len(final_headers)])

    print(f"  Saved: {filename}")
    return len(rows)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("=== REDATAM Python Scraper ===")
    print(f"Output: {OUTPUT_DIR}\n")

    session = make_session()

    for i, q in enumerate(QUERIES):
        outpath = os.path.join(OUTPUT_DIR, q["filename"])
        if os.path.exists(outpath):
            print(f"[{i+1}/{len(QUERIES)}] SKIP: {q['filename']}")
            continue

        print(f"[{i+1}/{len(QUERIES)}] {q['name']}")
        try:
            html = run_query(session, q["program"], q["name"])
            count = extract_and_save(html, q["filename"], q["headers"])
            print(f"  OK — {count} rows\n")
        except Exception as e:
            print(f"  ERROR: {e}\n")
            debug = os.path.join(OUTPUT_DIR, f"debug_{q['name']}.html")
            try:
                with open(debug, "w", encoding="utf-8", errors="replace") as f:
                    f.write(str(e))
            except Exception:
                pass

        if i < len(QUERIES) - 1:
            time.sleep(3)

    print("=== Done ===")


if __name__ == "__main__":
    main()
