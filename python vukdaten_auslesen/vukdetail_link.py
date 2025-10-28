import os
import sys
import time
import hashlib
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ============ Einstellungen ============
INPUT_XLSX = "volksfeste.xlsx"                # vorhandene Excel mit Links
OUTPUT_XLSX = "volksfeste_mit_details.xlsx"   # Ausgabe-Datei
CACHE_DIR = "cache"                           # Cache-Verzeichnis für HTML
SLEEP_SEC = 1.5                               # Pause zwischen Requests (zur Serverentlastung)
BASE_URL = "http://www.volksfestundkirmes.de/"
# =======================================


# ------------------- HTML Abruf -------------------

def ensure_cache():
    os.makedirs(CACHE_DIR, exist_ok=True)

def cache_filename(url):
    """Erzeugt kurzen, sicheren Cache-Dateinamen"""
    h = hashlib.md5(url.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{h}.html")

def fetch_html(url, session):
    """Lädt HTML aus Cache oder vom Web"""
    ensure_cache()
    fn = cache_filename(url)
    if os.path.exists(fn):
        with open(fn, "r", encoding="utf-8") as f:
            return f.read()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Referer": "http://www.volksfestundkirmes.de/terminkalender.php",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8"
    }

    print(f"  ↳ Lade Seite: {url}")
    r = session.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    html = r.text

    if len(html.strip()) > 500:
        with open(fn, "w", encoding="utf-8") as f:
            f.write(html)

    time.sleep(SLEEP_SEC)
    return html


# ------------------- HTML Parser -------------------

def parse_detail_page(html: str) -> dict:
    """Liest alle Felder aus einer Detailseite (unterstützt <div class='tr'> Struktur)"""
    soup = BeautifulSoup(html, "html.parser")
    details = {}

    rows = soup.select("div.tr")

    for r in rows:
        cols = r.select("div.td")
        if len(cols) != 2:
            continue

        label = cols[0].get_text(" ", strip=True)
        val_block = cols[1]
        value = val_block.get_text(" ", strip=True)
        link_tag = val_block.find("a", href=True)
        href = urljoin(BASE_URL, link_tag["href"]) if link_tag else None

        if "Bundesland" in label:
            details["Bundesland"] = value
        elif "Anschrift/Ziel" in label:
            details["Anschrift"] = value
            details["Navigation_Link"] = href
        elif "Parkmöglichkeiten" in label:
            details["Parkmöglichkeiten"] = value
        elif "Nachricht" in label or "Bericht" in label:
            details["Nachricht/Bericht"] = value
        elif "Weiteres Bildmaterial" in label or "Bildmaterial" in label:
            details["Bildmaterial"] = value
        elif "Erwartete Besucher" in label:
            details["Besucher"] = value
        elif "Erwartete Geschäfte" in label:
            details["Geschäfte"] = value
        elif "Link(s) zu weiteren Informationen" in label or "Weitere Informationen" in label:
            details["Weitere_Info_Link"] = href

    return details


# ------------------- Hauptfunktion -------------------

def enrich_from_excel(input_xlsx, output_xlsx, limit=None):
    """Liest Excel mit Detail-Links und ergänzt Daten aus den Detailseiten"""
    df = pd.read_excel(input_xlsx)
    link_col = None
    for c in ["Detail_Link", "Link"]:
        if c in df.columns:
            link_col = c
            break
    if not link_col:
        raise ValueError("Keine Spalte 'Detail_Link' oder 'Link' gefunden!")

    detail_fields = [
        "Bundesland", "Anschrift", "Navigation_Link", "Parkmöglichkeiten",
        "Nachricht/Bericht", "Bildmaterial", "Besucher", "Geschäfte", "Weitere_Info_Link"
    ]
    for c in detail_fields:
        if c not in df.columns:
            df[c] = ""

    def build_session():
        """Neue Session mit gültigem Cookie aufbauen"""
        s = requests.Session()
        start_url = BASE_URL + "terminkalender.php?userid=&sessionid=&anbieterart="
        s.get(start_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": BASE_URL,
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8"
        })
        return s

    # Erste Session aufbauen
    print("🌐 Baue erste Session auf …")
    s = build_session()

    total = len(df)
    if limit:
        print(f"⚙️ Testlauf: Es werden nur die ersten {limit} Links verarbeitet.\n")
    else:
        print(f"⚙️ Verarbeite alle {total} Links.\n")

    count = 0
    for i, row in df.iterrows():
        url = str(row[link_col]).strip()
        if not url.startswith("http"):
            continue

        # Anbieterart=1 einsetzen, falls leer
        if "anbieterart=" in url and "anbieterart=&" in url:
            url = url.replace("anbieterart=&", "anbieterart=1&")

        count += 1
        if limit and count > limit:
            break

        print(f"[{i+1}/{total}] {row.get('Veranstaltung', '')} – {row.get('Ort', '')}")

        try:
            html = fetch_html(url, s)
            details = parse_detail_page(html)

            # Wenn leer -> neue Session aufbauen und nochmal versuchen
            if not details or len(details) == 0:
                print("   ⚠️ Keine Details – baue neue Session auf und wiederhole ...")
                s = build_session()
                time.sleep(2)
                html = fetch_html(url, s)
                details = parse_detail_page(html)

            if not details:
                print("   ❌ Keine Details nach Wiederholung.")
            else:
                print(f"   ✅ {len(details)} Felder.")
                for k, v in details.items():
                    df.at[i, k] = v

            # Alle 50 Abrufe neue Session (präventiv)
            if i % 50 == 0 and i > 0:
                print("   🔄 Erneuere Session (Routine).")
                s = build_session()

        except Exception as e:
            print(f"   ❌ Fehler bei {url}: {e}")
            s = build_session()  # neue Session bei Fehler

    df.to_excel(output_xlsx, index=False)
    print(f"\n🎉 Fertig! Datei gespeichert: {output_xlsx}")


# ------------------- Testfunktion -------------------

def test_local_detail(file_path="detail.html"):
    """Testet den Parser lokal mit einer gespeicherten HTML-Datei"""
    with open(file_path, encoding="utf-8") as f:
        html = f.read()
    details = parse_detail_page(html)
    print("\n🔍 Test-Ergebnis aus lokaler Datei:")
    if not details:
        print("⚠️ Keine Felder gefunden – ist es die echte Detailseite?")
    else:
        for k, v in details.items():
            print(f"{k:25}: {v}")
    return details


# ------------------- Einstiegspunkt -------------------

if __name__ == "__main__":
    mode = None

    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["test", "t"]:
            mode = "test"
        elif arg in ["live", "l"]:
            mode = "live"
        elif arg in ["livetest", "lt"]:
            mode = "livetest"

    if mode is None:
        print("Was möchtest du tun?")
        print("  [1] Test mit lokaler Datei detail.html")
        print("  [2] Live: Alle Detailseiten abrufen")
        print("  [3] Live-Test: Nur die ersten 3 Detailseiten abrufen")
        choice = input("Bitte Auswahl eingeben (1, 2 oder 3): ").strip()
        mode = "test" if choice == "1" else "live" if choice == "2" else "livetest"

    if mode == "test":
        file_to_test = sys.argv[2] if len(sys.argv) > 2 else "detail.html"
        print(f"\n🧪 Starte Testmodus mit Datei: {file_to_test}")
        test_local_detail(file_to_test)
    elif mode == "live":
        print("\n🌐 Starte Live-Abruf aller Detailseiten...")
        enrich_from_excel(INPUT_XLSX, OUTPUT_XLSX)
    elif mode == "livetest":
        print("\n🧩 Starte Live-Test mit den ersten 3 Detailseiten...")
        enrich_from_excel(INPUT_XLSX, OUTPUT_XLSX, limit=3)
    else:
        print("❌ Ungültige Auswahl. Bitte 'test', 'live' oder 'livetest' angeben.")
