🧾 1️⃣ README.md

Erstelle im gleichen Projektordner (volksfesteundkirmes Internetseite)
eine Datei mit dem Namen README.md
und kopiere folgenden Text hinein:

# 🎡 Volksfeste Deutschland – Interaktive Karte

Eine interaktive **Streamlit-Web-App**, die alle Volksfeste in Deutschland anzeigt –  
mit Filter nach **Bundesland, Monat und Datum**.  
Die Karte nutzt **Folium**, und die Daten stammen aus einer Excel-Tabelle mit Koordinaten.

---

## 🚀 Features

- 🗺️ Interaktive Deutschlandkarte mit Marker-Clustering  
- 📅 Filter nach Monat, Bundesland und Zeitraum  
- 🧾 Tabellenansicht mit Monats-Tabs  
- 📤 Exportfunktion für ausgewählte Einträge  
- 🎨 Farblich kodierte Monate für bessere Übersicht  

---

## ⚙️ Installation (lokal)

```bash
# Repository klonen
git clone https://github.com/hybridclean/volksfeste-app.git
cd volksfeste-app

# Abhängigkeiten installieren
pip install -r requirements.txt

# App starten
streamlit run volksfeste_app.py


Dann öffnet sich automatisch dein Browser unter:
👉 http://localhost:8501

☁️ Deployment

Diese App ist auch online auf Streamlit Cloud verfügbar:
🔗 (Link folgt, sobald du sie veröffentlicht hast)

📂 Datenquelle

Die Volksfestdaten stammen aus einer Excel-Datei mit folgenden Spalten:

Bundesland	Ort	Veranstaltung	Von	Bis	Monat	Jahr	Latitude	Longitude
🧰 Verwendete Technologien

Streamlit

Pandas

Folium

streamlit-folium

OpenPyXL

👨‍💻 Autor

Michael [Nachname optional]
Projekt Volksfeste & Kirmes Deutschland
📧 Kontakt: (optional)


---

## 🧹 2️⃣ `.gitignore`

Erstelle eine weitere Datei namens **`.gitignore`**  
(im selben Ordner wie `volksfeste_app.py`)  
mit folgendem Inhalt:

```text
# Python
__pycache__/
*.pyc
*.pyo
*.pyd

# VSCode
.vscode/

# Streamlit
.streamlit/

# Lokale Dateien
*.xlsx
*.csv
*.html
*.log

# Windows
Thumbs.db
desktop.ini

📤 Danach

1️⃣ Füge beide Dateien zu Git hinzu:

git add README.md .gitignore
git commit -m "Add README and gitignore"
git push


2️⃣ Schau dir dein GitHub-Projekt an —
es sieht jetzt sauber, professionell und vollständig aus 🌟
