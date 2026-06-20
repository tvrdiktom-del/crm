import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Nastavení mobilního vzhledu stránky
st.set_page_config(page_title="Cloakroom CRM", page_icon="💼", layout="centered")
st.title("💼 Šatní CRM")

# Propojení s Google Sheets
conn = st.connection("moje_crm", type=GSheetsConnection)

# Definice správných sloupců
POTREBNE_SLOUPCE = ["Nazev", "Adresa", "Rating", "Obor", "Kapacita_Satny", "Cena_Satny", "Kontaktni_Osoba", "Poznamka"]

# Načtení dat
try:
    # Čtení funguje přes odkaz bezproblémově
    df = conn.read(ttl="5s")
    if df.empty or not all(col in df.columns for col in POTREBNE_SLOUPCE):
        st.warning("Tabulka byla načtena, ale sloupce neodpovídají vzoru.")
except Exception as e:
    st.error(f"Chyba při komunikaci s Google: {e}")
    df = pd.DataFrame()

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
    
    # Zobrazení karet na mobilu
    for idx, row in df_filtered.iterrows():
        with st.expander(f"**{row.get('Nazev', 'Neznámý')}** ({row.get('Rating', '-')})"):
            st.write(f"🎭 **Obor:** {row.get('Obor', '-')}")
            st.write(f"📍 **Adresa:** {row.get('Adresa', '-')}")
            st.write(f"👤 **Kontakt:** {row.get('Kontaktni_Osoba', '-')}")
            st.write(f"🧥 **Kapacita šatny:** {row.get('Kapacita_Satny', 0)} ks")
            st.write(f"💰 **Cena šatny:** {row.get('Cena_Satny', 0)} Kč")
            st.write(f"📝 **Poznámka:** {row.get('Poznamka', '-')}")
else:
    st.info("V databázi zatím nejsou žádná data k zobrazení.")
