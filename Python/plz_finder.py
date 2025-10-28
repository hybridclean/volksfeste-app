import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

# ------------------------------------------------------
# 1. Einstellungen
# ------------------------------------------------------

# Datei mit den Städten
# Passe den Pfad ggf. an:
eingabe_datei = r"C:\Users\micha\OneDrive\01-Micha\KI\Konzepte\Internetseiten\fehlende plz.csv"

# Ausgabedatei
ausgabe_datei = r"C:\Users\micha\OneDrive\01-Micha\KI\Konzepte\Internetseiten\PLZ_ergänzt.csv"

# Fallback-PLZ für Orte, die Nominatim nicht findet
fallback = {
    "Amberg": "92224",
    "Hannover": "30159",
    "München": "80331",
    "Leipzig": "04109",
    "Berlin": "10115"
}

# ------------------------------------------------------
# 2. Daten einlesen
# ------------------------------------------------------

if eingabe_datei.endswith(".xlsx"):
    df = pd.read_excel(eingabe_datei)
else:
    # wichtig: Encoding für deutsche Umlaute
    df = pd.read_csv(eingabe_datei, encoding="latin1")

# Prüfen, ob Spalte „Stadt“ existiert
if "Stadt" not in df.columns:
    raise ValueError("❌ Die Datei muss eine Spalte mit dem Namen 'Stadt' enthalten!")

# Falls keine PLZ-Spalte vorhanden, neu anlegen
if "PLZ" not in df.columns:
    df.insert(0, "PLZ", "")

# ------------------------------------------------------
# 3. Geocoder einrichten
# ------------------------------------------------------

geolocator = Nominatim(user_agent="plz_finder_script")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

# ------------------------------------------------------
# 4. PLZ ermitteln
# ------------------------------------------------------

for idx, row in df.iterrows():
    if pd.isna(row["PLZ"]) or str(row["PLZ"]).strip() == "":
        stadt = str(row["Stadt"]).strip()
        try:
            ort = geocode(f"{stadt}, Deutschland")

            if ort and "address" in ort.raw and "postcode" in ort.raw["address"]:
                plz = ort.raw["address"]["postcode"]
                df.at[idx, "PLZ"] = plz
                print(f"✅ {stadt} -> {plz}")

            else:
                print(f"⚠️  Keine PLZ von Nominatim für: {stadt}")
                if stadt in fallback:
                    df.at[idx, "PLZ"] = fallback[stadt]
                    print(f"   → Fallback verwendet: {fallback[stadt]}")
                else:
                    df.at[idx, "PLZ"] = ""

        except Exception as e:
            print(f"❌ Fehler bei {stadt}: {e}")
            if stadt in fallback:
                df.at[idx, "PLZ"] = fallback[stadt]
                print(f"   → Fallback verwendet: {fallback[stadt]}")

        time.sleep(1)  # um die Server nicht zu überlasten

# ------------------------------------------------------
# 5. Ergebnis speichern
# ------------------------------------------------------

df.to_csv(ausgabe_datei, index=False, encoding="utf-8-sig")
print(f"\n✅ Fertig! Datei gespeichert als: {ausgabe_datei}")
