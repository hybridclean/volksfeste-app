import pandas as pd
import requests
import time
from tqdm import tqdm

# === 👉 Deinen Google-API-Key hier eintragen ======================
API_KEY = "AIzaSyAGddvZOD738At9ycBeFrupNNXxKbZqjGE"
# ================================================================

input_file = "volksfeste_mit_details_mit_maps.xlsx"
output_file = "volksfeste_mit_koordinaten.xlsx"

df = pd.read_excel(input_file)

# Fehlende Spalten anlegen
for col in ["Latitude", "Longitude"]:
    if col not in df.columns:
        df[col] = None

try:
    for i, row in tqdm(df.iterrows(), total=len(df), desc="Geocoding läuft..."):
        # Überspringe vorhandene Werte
        if pd.notna(row["Latitude"]) and pd.notna(row["Longitude"]):
            continue

        ort = str(row.get("Ort", "")).strip()
        plz = str(row.get("PLZ", "")).strip()

        if not ort or not plz:
            print(f"⚠️  Zeile {i}: kein Ort oder PLZ – übersprungen")
            continue

        address = f"{plz} {ort}, Deutschland"
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={API_KEY}"

        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            status = data.get("status")

            # --- Debug-Ausgabe ---
            print(f"\n🔍 [{i}] Anfrage: {address}")
            print(f"   ➜ Status: {status}")

            if status == "OK":
                loc = data["results"][0]["geometry"]["location"]
                lat, lng = loc["lat"], loc["lng"]
                df.at[i, "Latitude"] = lat
                df.at[i, "Longitude"] = lng
                print(f"   ✅ Gefunden: {lat:.5f}, {lng:.5f}")
            else:
                print(f"   ❌ Keine Koordinaten gefunden – Status: {status}")
                df.at[i, "Latitude"] = None
                df.at[i, "Longitude"] = None

        except Exception as e:
            print(f"⚠️  Fehler bei {address}: {e}")
            time.sleep(1)

        # Zwischenspeichern alle 25 Zeilen
        if i % 25 == 0 and i > 0:
            df.to_excel(output_file, index=False)
            print(f"💾 Zwischenspeicherung nach {i} Zeilen...")

        time.sleep(0.2)

except KeyboardInterrupt:
    print("\n🛑 Abbruch durch Benutzer – Zwischenergebnisse werden gespeichert...")
finally:
    df.to_excel(output_file, index=False)
    print("\n💾 Datei gespeichert:", output_file)
    print("✅ Geocoding abgeschlossen.")
