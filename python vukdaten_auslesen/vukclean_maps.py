import pandas as pd
import requests
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font

# Excel einlesen
df = pd.read_excel("volksfeste_mit_details_clean.xlsx")

# Neue Spalte für echte Ziel-Links
df["Navigation_Echt"] = ""

for i, link in enumerate(df["Navigation_Link"].dropna()):
    try:
        r = requests.get(link, allow_redirects=True, timeout=10)
        df.loc[df["Navigation_Link"] == link, "Navigation_Echt"] = r.url
        print(f"[{i+1}] ✅ {link} → {r.url}")
    except Exception as e:
        print(f"[{i+1}] ⚠️ Fehler bei {link}: {e}")

# Export mit klickbaren Hyperlinks
wb = Workbook()
ws = wb.active
ws.title = "Veranstaltungen"

for r in dataframe_to_rows(df, index=False, header=True):
    ws.append(r)

# Hyperlinks in Navigation_Echt-Spalte aktivieren
nav_col = df.columns.get_loc("Navigation_Echt") + 1
for row in range(2, len(df) + 2):
    cell = ws.cell(row=row, column=nav_col)
    url = cell.value
    if isinstance(url, str) and url.startswith("http"):
        cell.hyperlink = url
        cell.font = Font(color="0000EE", underline="single")

wb.save("volksfeste_mit_details_mit_maps.xlsx")
print("✅ Datei gespeichert: volksfeste_mit_details_mit_maps.xlsx")
