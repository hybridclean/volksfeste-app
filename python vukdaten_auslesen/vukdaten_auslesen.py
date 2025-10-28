import os
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from urllib.parse import urljoin

BASE_URL = "http://www.volksfestundkirmes.de/"
START_URL = BASE_URL + "terminkalender.php?userid=&sessionid=&anbieterart="
CACHE_DIR = "cache"


import hashlib
import os
import re
import time
import requests

CACHE_DIR = "cache"

def get_cached(url):
    """Lädt HTML aus Cache oder vom Web (mit Hash-basiertem Dateinamen)"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    # Kurzer eindeutiger Name über Hash
    hash_name = hashlib.md5(url.encode("utf-8")).hexdigest()
    filename = os.path.join(CACHE_DIR, f"{hash_name}.html")

    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()

    print(f"  ↳ Lade Seite: {url}")
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    html = r.text

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    time.sleep(1)  # kleine Pause zur Serverentlastung
    return html


def extract_main_page():
    """Liest Veranstaltungen von der Hauptseite"""
    html = get_cached(START_URL)
    soup = BeautifulSoup(html, "html.parser")

    events = []
    for a in soup.select("a[href*='veranstaltungdetails.php']"):
        href = urljoin(BASE_URL, a["href"])
        text = a.get_text(" ", strip=True)

        # Datum extrahieren
        dates = re.findall(r"(\d{2}\.\d{2}\.\d{4})", text)
        von, bis = (dates[0], dates[1]) if len(dates) >= 2 else ("", "")

        # Veranstaltungstitel
        b = a.find("b")
        veranstaltung = b.get_text(strip=True) if b else ""

        # PLZ und Ort
        after_b = b.find_next_sibling(text=True) if b else ""
        plz, ort = "", ""
        match = re.search(r"(\d{4,5})\s*([A-Za-zÄÖÜäöüß\-\s]+)", after_b)
        if match:
            plz, ort = match.groups()

        events.append({
            "PLZ": plz.strip(),
            "Ort": ort.strip(),
            "Veranstaltung": veranstaltung,
            "Von": von,
            "Bis": bis,
            "Detail_Link": href
        })
    return events


def extract_detail_page(url):
    """Liest Detailinformationen und prüft Erfolg"""
    details = {}
    html = get_cached(url)
    soup = BeautifulSoup(html, "html.parser")

    rows = soup.find_all("tr")
    if not rows:
        print("    ⚠️ Keine Tabellenzeilen gefunden.")
        return details

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        label = cells[0].get_text(" ", strip=True)
        content = cells[1].get_text(" ", strip=True)
        link_tag = cells[1].find("a", href=True)

        if "Bundesland" in label:
            details["Bundesland"] = content
        elif "Anschrift/Ziel" in label:
            details["Anschrift"] = content
            if link_tag:
                details["Navigation_Link"] = urljoin(BASE_URL, link_tag["href"])
        elif "Parkmöglichkeiten" in label:
            details["Parkmöglichkeiten"] = content
        elif "Nachricht" in label:
            details["Nachricht/Bericht"] = content
        elif "Bildmaterial" in label:
            details["Bildmaterial"] = content
        elif "Erwartete Besucher" in label:
            details["Besucher"] = content
        elif "Erwartete Geschäfte" in label:
            details["Geschäfte"] = content
        elif "Weitere Informationen" in label:
            if link_tag:
                details["Weitere_Info_Link"] = urljoin(BASE_URL, link_tag["href"])

    if details:
        print(f"    ✅ {len(details)} Detailfelder gefunden.")
    else:
        print("    ⚠️ Keine Details erkannt.")
    return details


def main():
    print("🔍 Lese Hauptseite …")
    events = extract_main_page()
    print(f"✅ {len(events)} Veranstaltungen erkannt.\n")

    enriched = []
    for i, event in enumerate(events, 1):
        print(f"[{i}/{len(events)}] {event['Veranstaltung']} – {event['Ort']}")
        details = extract_detail_page(event["Detail_Link"])
        event.update(details)
        enriched.append(event)

    df = pd.DataFrame(enriched)
    df.to_excel("volksfeste_mit_details.xlsx", index=False)
    print("\n🎉 Fertig! Datei gespeichert: volksfeste_mit_details.xlsx")


if __name__ == "__main__":
    main()
