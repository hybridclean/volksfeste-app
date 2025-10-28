import pandas as pd
import requests
import time
import json
import os
from tqdm import tqdm
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font

# ========= Einstellungen =========
INPUT_FILE = "volksfeste_mit_details_clean.xlsx"
OUTPUT_FILE = "volksfeste_mit_details_mit_maps.xlsx"
PROGRESS_FILE = "progress.json"
SLEEP_SEC = 2.0           # Pause zwischen Requests (Sekunden)
SAVE_EVERY = 20           # Nach wie vielen Requests Zwischenspeichern
TIMEOUT = 10              # Timeout für HTTP-Requests
MAX_RETRIES = 3           # Wiederholungsversuche bei Fehlern
# =================================


def load_progress(total_rows):
    """Lädt gespeicherten Fortschritt oder startet bei 0."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            last_index = data.get("last_index", 0)

            print(f"📄 Fortschritt gefunden: {last_index}/{total_rows} verarbeitet.")
            choice = input("🔁 Fortsetzen [F] oder Neu starten [N]? ").strip().lower()

            if choice == "f":
                print(f"➡️ Fortsetzen ab Zeile {last_index}")
                return last_index
            else:
                print("♻️ Neu gestartet (Fortschritt wird überschrieben).")
                return 0
    return 0


def save_progress(index):
    """Speichert aktuellen Fortschritt."""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_index": index}, f)


def resolve_redirect(url):
    """Löst Redirect auf und gibt Ziel-URL zurück."""
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, allow_redirects=True, timeout=TIMEOUT)
            if r.status_code == 200:
                return r.url
        except Exception as e:
            print(f"⚠️ Versuch {attempt+1}/{MAX_RETRIES} fehlgeschlagen: {e}")
            time.sleep(1)
    return None


def save_to_excel(df):
    """Speichert DataFrame mit klickbarem 'Maps'-Button."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Veranstaltungen"

    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)

    # Hyperlinks als "Maps"-Button
    if "Navigation_Echt" in df.columns:
        col_idx = df.columns.get_loc("Navigation_Echt") + 1
        for row in range(2, len(df) + 2):
            cell = ws.cell(row=row, column=col_idx)
            url = cell.value
            if isinstance(url, str) and url.startswith("http"):
                cell.value = "🗺️ Maps"
                cell.hyperlink = url
                cell.font = Font(color="0000EE", underline="single")

    wb.save(OUTPUT_FILE)


def main():
    print(f"📂 Lade Datei: {INPUT_FILE}")
    df = pd.read_excel(INPUT_FILE)

    if "Navigation_Link" not in df.columns:
        raise ValueError("Spalte 'Navigation_Link' nicht gefunden!")

    if "Navigation_Echt" not in df.columns:
        df["Navigation_Echt"] = ""

    total = len(df)
    start_index = load_progress(total)
    print(f"🔗 {total} Links gefunden. Starte bei Index {start_index}.\n")

    for i in tqdm(range(start_index, total), desc="Löse Weiterleitungen auf", unit="Link"):
        link = str(df.at[i, "Navigation_Link"]).strip()

        if not link.startswith("http"):
            continue
        if isinstance(df.at[i, "Navigation_Echt"], str) and df.at[i, "Navigation_Echt"].startswith("http"):
            continue

        resolved = resolve_redirect(link)
        if resolved:
            df.at[i, "Navigation_Echt"] = resolved

        # Zwischenspeicherung
        if i % SAVE_EVERY == 0 and i > 0:
            save_to_excel(df)
            save_progress(i)
            print(f"💾 Zwischengespeichert nach {i} Einträgen…")

        time.sleep(SLEEP_SEC)

    # Final speichern
    save_to_excel(df)
    save_progress(total)
    print(f"\n🎉 Fertig! Datei gespeichert unter: {OUTPUT_FILE}")
    print("✅ Fortschritt gesichert in progress.json")


if __name__ == "__main__":
    main()
