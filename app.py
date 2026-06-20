import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(page_title="Cloakroom CRM", page_icon="💼", layout="centered")
st.title("💼 Šatní CRM")

try:
    url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    if "/edit" in url:
        base_url = url.split("/edit")[0]
    else:
        base_url = url
    csv_url = base_url + "/export?format=csv"
    
    df = pd.read_csv(csv_url)
    df = df.dropna(how="all")
except Exception as e:
    st.error(f"Nepodařilo se připojit k tabulce. Chyba: {e}")
    df = pd.DataFrame()

st.subheader("Seznam provozoven")

if not df.empty and len(df) > 0:
    # Vyčištění dat
    for col in df.columns:
        df[col] = df[col].astype(str).replace("nan", "").str.strip()

    # Filtry nahoře (Stav a Hledání)
    mozne_stavy = list(df["Stav"].unique()) if "Stav" in df.columns else []
    mozne_stavy = [s for s in mozne_stavy if s]
    
    col1, col2 = st.columns([2, 1])
    with col1:
        hledat = st.text_input("🔍 Hledat (Název, adresa, obor...)")
    with col2:
        filtr_stav = st.multiselect("Stav", mozne_stavy, default=mozne_stavy)

    # Filtrování
    df_filtered = df.copy()
    if filtr_stav and "Stav" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["Stav"].isin(filtr_stav)]
        
    if hledat:
        mask = df_filtered.astype(str).apply(lambda x: x.str.contains(hledat, case=False)).any(axis=1)
        df_filtered = df_filtered[mask]
        
    st.write(f"Nalezeno záznamů: {len(df_filtered)}")
    
    # Výpis klientů
    for idx, row in df_filtered.iterrows():
        nazev = row.get("Nazev", "Neznámý")
        stav = f" [{row.get('Stav')}]" if row.get("Stav") else ""
        rating = f" ({row.get('Rating')})" if row.get('Rating') else ""
        
        with st.expander(f"**{nazev}**{rating}{stav}"):
            # PŘEHLED POSLEDNÍ AKTIVITY (Raynet styl)
            if row.get("Posledni_Aktivita") or row.get("Aktivita_Popis"):
                st.info(f"**📝 Naposledy řešeno ({row.get('Datum_Aktivity', '-')}) :**\n"
                        f"*{row.get('Posledni_Aktivita', 'Aktivita')}* - {row.get('Aktivita_Popis', '-')}")
            
            # ZÁKLADNÍ INFO
            st.write(f"🎭 **Obor:** {row.get('Obor', '-')}")
            st.write(f"📍 **Adresa:** {row.get('Adresa', '-')}")
            st.write(f"👤 **Kontakt:** {row.get('Kontaktni_Osoba', '-')} (Tel: {row.get('Telefon', '-')})")
            st.write(f"🧥 **Šatna:** {row.get('Kapacita_Satny', '-')} ks | **Cena:** {row.get('Cena_Satny', '-')} Kč")
            if row.get("Poznamka"):
                st.write(f"ℹ️ **Poznámka:** {row.get('Poznamka')}")
                
            st.write("---")
            
            # AKČNÍ TLAČÍTKA PRO MOBIL
            c1, c2, c3 = st.columns(3)
            
            # 1. Rychlé volání
            if row.get("Telefon"):
                c1.markdown(f"[📞 Volat](tel:{row.get('Telefon')})", unsafe_allow_html=True)
            
            # 2. Rychlá navigace
            if row.get("Adresa"):
                adr_encoded = urllib.parse.quote(row.get("Adresa"))
                c2.markdown(f"[📍 Navigovat](https://www.google.com/maps/search/?api=1&query={adr_encoded})", unsafe_allow_html=True)
                
            # 3. Kalendář (Plánování dalšího kontaktu)
            if row.get("Dalsi_Kontakt"):
                text_kalendar = f"Schůzka/Kontakt: {nazev}"
                text_encoded = urllib.parse.quote(text_kalendar)
                # Odkaz na Google kalendář s předvyplněným názvem a místem
                g_cal_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={text_encoded}&location={adr_encoded}"
                c3.markdown(f"[📅 Do kalendáře]({g_cal_url})", unsafe_allow_html=True)
else:
    st.info("V tabulce nebyla nalezena žádná data.")
