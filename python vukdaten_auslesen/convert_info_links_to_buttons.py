import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font

# ========= Einstellungen =========
INPUT_FILE = "volksfeste_mit_details_mit_maps.xlsx"
OUTPUT_FILE = "volksfeste_mit_details_mit_websites.xlsx"
LINK_COLUMN = "Weitere_Info_Link"
BUTTON_TEXT = "🌐 Website"
# =================================


def main():
    print(f"📂 Lade Datei: {INPUT_FILE}")
    df = pd.read_excel(INPUT_FILE)

    if LINK_COLUMN not in df.columns:
        raise ValueError(f"Spalte '{LINK_COLUMN}' nicht gefunden!")

    wb = Workbook()
    ws = wb.active
    ws.title = "Veranstaltungen"

    # Schreibe DataFrame in Excel
    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)

    # Finde Spalte mit „Weitere_Info_Link“
    col_idx = df.columns.get_loc(LINK_COLUMN) + 1

    # Ersetze Links durch klickbare „🌐 Website“-Buttons
    for row in range(2, len(df) + 2):
        cell = ws.cell(row=row, column=col_idx)
        url = str(cell.value).strip() if cell.value else ""
        if url.startswith("http"):
            cell.value = BUTTON_TEXT
            cell.hyperlink = url
            cell.font = Font(color="0000EE", underline="single")

    wb.save(OUTPUT_FILE)
    print(f"✅ Fertig! Datei gespeichert unter: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
