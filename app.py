import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Nastavení mobilního vzhledu stránky
st.set_page_config(page_title="Cloakroom CRM", page_icon="💼", layout="centered")
st.title("💼 Šatní CRM")

# Propojení s Google Sheets pomocí standardního názvu
conn = st.connection("gsheets", type=GSheetsConnection)

# Definice správných sloupců
POTREBNE_SLOUPCE = ["Nazev", "Adresa", "Rating", "Obor", "Kapacita_Satny", "Cena_Satny", "Kontaktni_Osoba", "Poznamka"]

# Načtení dat
try:
    # Čtení přes veřejný odkaz s nastaveným ttl (vypršení cache) na 10 sekund
    df = conn.read(ttl="10s")
    
    # Pokud by byly sloupce jinak, pojistíme je prázdnými hodnotami
    for col in POTREBNE_SLOUPCE:
        if col not in df.columns:
            df[col] = ""
except Exception as e:
    st.error(f"Chyba při načítání dat: {e}")
    df = pd.DataFrame(columns=POTREBNE_SLOUPCE)

st.subheader("Seznam provozoven")

if not df.empty and len(df) > 0:
    # Mobilní vyhledávání a filtry
    hledat = st.text_input("🔍 Hledat podle názvu, adresy nebo oboru")
    filtr_rating = st.multiselect("Filtr Ratingu", ["A", "B", "C"], default=["A", "B", "C"])
    
    # Filtrování dat
    df_filtered = df.copy()
    df_filtered['Nazev'] = df_filtered['Nazev'].astype(str).fillna('')
    df_filtered['Adresa'] = df_filtered['Adresa'].astype(str).fillna('')
    df_filtered['Obor'] = df_filtered['Obor'].astype(str).fillna('')
    
    if hledat:
        df_filtered = df_filtered[
            df_filtered['Nazev'].str.contains(hledat, case=False) | 
            df_filtered['Adresa'].str.contains(hledat, case=False) |
            df_filtered['Obor'].str.contains(hledat, case=False)
        ]
    
    if 'Rating' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['Rating'].isin(filtr_rating)]
    
    st.write(f"Nalezeno klientů: {len(df_filtered)}")
    
    # Zobrazení přehledných karet
    for idx, row in df_filtered.iterrows():
        # Schováme prázdné řádky, pokud by tam nějaké byly
        if row.get('Nazev') == "":
            continue
            
        with st.expander(f"**{row.get('Nazev')}** ({row.get('Rating', '-')})"):
            st.write(f"🎭 **Obor:** {row.get('Obor', '-')}")
            st.write(f"📍 **Adresa:** {row.get('Adresa', '-')}")
            st.write(f"👤 **Kontakt:** {row.get('Kontaktni_Osoba', '-')}")
            st.write(f"🧥 **Kapacita šatny:** {row.get('Kapacita_Satny', 0)} ks")
            st.write(f"💰 **Cena šatny:** {row.get('Cena_Satny', 0)} Kč")
            st.write(f"📝 **Poznámka:** {row.get('Poznamka', '-')}")
else:
    st.info("V databázi zatím nejsou žádná data k zobrazení. Zkontrolujte, zda máte v Google Tabulce zadané řádky pod hlavičkou.")
