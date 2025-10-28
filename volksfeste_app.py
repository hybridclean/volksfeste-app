# =========================================================
# 🎡 VOLKSFESTE DEUTSCHLAND – STABILE VERSION (OKT 2025)
# =========================================================

import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from io import BytesIO

# ---------------------------------------------------------
# 📥 Daten laden
# ---------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("volksfeste_mit_koordinaten.xlsx")
    df = df.dropna(subset=["Latitude", "Longitude"])
    for col in ["Von", "Bis"]:
        if col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = pd.to_datetime("1899-12-30") + pd.to_timedelta(df[col], "D")
            else:
                df[col] = pd.to_datetime(df[col], errors="coerce", format="%d.%m.%Y")
            df[col] = df[col].dt.date
    return df


# ---------------------------------------------------------
# ⚙️ Seite einrichten
# ---------------------------------------------------------
st.set_page_config(page_title="Volksfeste Deutschland", layout="wide")
df = load_data()

month_colors = {
    "Januar": "blue", "Februar": "cadetblue", "März": "darkgreen",
    "April": "green", "Mai": "lightgreen", "Juni": "orange",
    "Juli": "red", "August": "darkred", "September": "purple",
    "Oktober": "darkpurple", "November": "gray", "Dezember": "black",
}
monate = list(month_colors.keys())

# ---------------------------------------------------------
# 🧭 Session-State initialisieren (verbesserte Startlogik)
# ---------------------------------------------------------
defaults = {
    "month_select": "Alle",
    "active_month": "Alle",
    "search": "",
    "pending_month": None,  # 👈 Hilfspuffer für Tabs
    "initialized": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Erster Start → sauberer Initialzustand "Alle"
if not st.session_state.initialized:
    st.session_state.month_select = "Alle"
    st.session_state.active_month = "Alle"
    st.session_state.pending_month = None
    st.session_state.initialized = True

# Falls später ein Monat vorgemerkt wurde (Tab-Klick) → übernehmen
elif st.session_state.pending_month and st.session_state.pending_month != "Alle":
    st.session_state.month_select = st.session_state.pending_month
    st.session_state.active_month = st.session_state.pending_month
    st.session_state.pending_month = None


# =========================================================
# 🔍 FILTER (linke Spalte)
# =========================================================
col1, col2 = st.columns([1, 3])

with col1:
    st.title("🎡 Volksfeste Deutschland")
    st.subheader("🔍 Filter")

    bundeslaender = sorted(df["Bundesland"].dropna().unique())
    selected_state = st.selectbox("Bundesland auswählen", ["Alle"] + bundeslaender)

    opts = ["Alle"] + monate
    if st.session_state.month_select not in opts:
        st.session_state.month_select = "Alle"

    selected_month = st.selectbox(
        "Monat auswählen",
        opts,
        index=opts.index(st.session_state.month_select),
        key="month_select",
    )

    if st.session_state.active_month != selected_month:
        st.session_state.active_month = selected_month

    min_date, max_date = df["Von"].min(), df["Bis"].max()
    selected_date = st.slider(
        "Datum auswählen", min_value=min_date, max_value=max_date, value=min_date, format="DD.MM.YYYY"
    )

    # 🔁 Zurücksetzen-Button
    if st.button("🔄 Filter zurücksetzen"):
        st.session_state.month_select = "Alle"
        st.session_state.active_month = "Alle"
        st.session_state.search = ""
        selected_state = "Alle"
        selected_date = min_date
        st.rerun()

    st.caption("Die Karte zeigt alle Feste, die **ab dem gewählten Datum** beginnen.")

    st.markdown("#### 🗓️ Farblegende")
    legend = "<div style='font-size:14px; line-height:1.6;'>"
    for m, c in month_colors.items():
        legend += f"<span style='color:{c};'>●</span> {m}<br>"
    legend += "</div>"
    st.markdown(legend, unsafe_allow_html=True)


# =========================================================
# 🗺️ KARTEN- UND TABELLENBEREICH (rechte Spalte)
# =========================================================
with col2:
    # ------------------------------
    # 🔎 Filter anwenden
    # ------------------------------
    filtered = df.copy()
    if selected_state != "Alle":
        filtered = filtered[filtered["Bundesland"] == selected_state]
    if st.session_state.active_month != "Alle":
        filtered = filtered[filtered["Monat"] == st.session_state.active_month]
    filtered = filtered[filtered["Von"] >= selected_date]

    st.markdown(f"**{len(filtered)} Veranstaltungen ab dem {selected_date.strftime('%d.%m.%Y')}**")

    # ------------------------------
    # 🗺️ Karte
    # ------------------------------
    m = folium.Map(location=[51.1657, 10.4515], zoom_start=6, tiles="CartoDB positron")
    marker_cluster = MarkerCluster().add_to(m)

    for _, r in filtered.iterrows():
        color = month_colors.get(str(r["Monat"]).capitalize(), "blue")
        popup = f"""
        <b>{r['Veranstaltung']}</b><br>
        {r['Ort']} ({r['Bundesland']})<br>
        📅 {r['Von'].strftime('%d.%m.%Y')} – {r['Bis'].strftime('%d.%m.%Y')}
        """
        folium.CircleMarker(
            location=[r["Latitude"], r["Longitude"]],
            radius=6, color=color, fill=True, fill_opacity=0.85, popup=popup
        ).add_to(marker_cluster)

    if not filtered.empty:
        m.fit_bounds([
            [filtered["Latitude"].min(), filtered["Longitude"].min()],
            [filtered["Latitude"].max(), filtered["Longitude"].max()],
        ])

    st_folium(m, width=950, height=650)

    # ------------------------------
    # 🔍 Suchfeld
    # ------------------------------
    st.session_state.search = st.text_input(
        "🔎 Veranstaltung oder Ort suchen", value=st.session_state.search
    )
    visible = filtered.copy()
    if st.session_state.search.strip():
        q = st.session_state.search.lower()
        visible = visible[
            visible["Veranstaltung"].str.lower().str.contains(q, na=False)
            | visible["Ort"].str.lower().str.contains(q, na=False)
        ]

    export_on = st.checkbox("💾 Aktuelle Ansicht exportieren")

    # =====================================================
    # 📋 Tabellenanzeige
    # =====================================================
    st.subheader("📋 Veranstaltungen")

    if visible.empty:
        st.info("Keine Veranstaltungen gefunden.")
    else:
        if st.session_state.active_month == "Alle":
            months_present = [m for m in monate if m in visible["Monat"].unique()]
            tabs = st.tabs([f"{m} ({len(visible[visible['Monat'] == m])})" for m in months_present])

            for i, mname in enumerate(months_present):
                with tabs[i]:
                    # 🔁 Synchronisation Tab → Dropdown (sanft, aber nicht aus "Alle")
                    if (
                        st.session_state.month_select != mname
                        and st.session_state.month_select != "Alle"
                    ):
                        st.session_state.pending_month = mname
                        st.stop()  # beendet Rendering, beim nächsten Lauf wird pending_month gesetzt

                    df_m = visible[visible["Monat"] == mname].copy()
                    df_m["Von"] = df_m["Von"].apply(lambda d: d.strftime("%d.%m.%Y") if pd.notna(d) else "")
                    df_m["Bis"] = df_m["Bis"].apply(lambda d: d.strftime("%d.%m.%Y") if pd.notna(d) else "")
                    st.markdown(f"**{len(df_m)} Veranstaltungen im {mname}**")

                    df_m = df_m[["Veranstaltung", "Ort", "Von", "Bis"]].sort_values("Von")
                    df_m.insert(0, "Export", False)

                    edited = st.data_editor(
                        df_m,
                        width="stretch",
                        num_rows="fixed",
                        column_config={
                            "Export": st.column_config.CheckboxColumn("Export", help="Für Export markieren"),
                        },
                    )

                    sel = edited[edited["Export"]]
                    if export_on and not sel.empty:
                        csv = sel.to_csv(index=False).encode("utf-8")
                        xlsx = BytesIO()
                        sel.to_excel(xlsx, index=False)
                        st.download_button("⬇️ CSV exportieren", csv, f"Volksfeste_{mname}.csv", "text/csv")
                        st.download_button("⬇️ Excel exportieren", xlsx.getvalue(), f"Volksfeste_{mname}.xlsx")

        else:
            mname = st.session_state.active_month
            df_m = visible.copy()
            df_m["Von"] = df_m["Von"].apply(lambda d: d.strftime("%d.%m.%Y") if pd.notna(d) else "")
            df_m["Bis"] = df_m["Bis"].apply(lambda d: d.strftime("%d.%m.%Y") if pd.notna(d) else "")
            st.markdown(f"**{len(df_m)} Veranstaltungen im {mname}**")

            df_m = df_m[["Veranstaltung", "Ort", "Von", "Bis"]].sort_values("Von")
            df_m.insert(0, "Export", False)

            edited = st.data_editor(
                df_m,
                width="stretch",
                num_rows="fixed",
                column_config={
                    "Export": st.column_config.CheckboxColumn("Export", help="Für Export markieren"),
                },
            )

            sel = edited[edited["Export"]]
            if export_on and not sel.empty:
                csv = sel.to_csv(index=False).encode("utf-8")
                xlsx = BytesIO()
                sel.to_excel(xlsx, index=False)
                st.download_button("⬇️ CSV exportieren", csv, f"Volksfeste_{mname}.csv", "text/csv")
                st.download_button("⬇️ Excel exportieren", xlsx.getvalue(), f"Volksfeste_{mname}.xlsx")
