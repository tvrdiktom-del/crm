import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Nastavení mobilního vzhledu stránky
st.set_page_config(page_title="Cloakroom CRM", page_icon="💼", layout="centered")
st.title("💼 Šatní CRM")

# Propojení s Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Definice správných sloupců
POTREBNE_SLOUPCE = ["Nazev", "Adresa", "Rating", "Kapacita_Satny", "Cena_Satny", "Kontaktni_Osoba", "Poznamka"]

# Načtení dat s pojistkou proti prázdné tabulce nebo chybějícím sloupcům
try:
    df = conn.read(ttl="10s")  # Zkráceno na 10s pro rychlé testování
    
    # Pojistka: Pokud je tabulka úplně prázdná nebo chybí sloupce, vytvoříme je v paměti aplikací
    if df.empty or not all(col in df.columns for col in POTREBNE_SLOUPCE):
        df = pd.DataFrame(columns=POTREBNE_SLOUPCE)
except Exception as e:
    df = pd.DataFrame(columns=POTREBNE_SLOUPCE)

# Záložky pro mobilní rozhraní
tab_prehled, tab_pridat = st.tabs(["📋 Přehled klientů", "➕ Nový klient"])

with tab_prehled:
    st.subheader("Seznam provozoven")
    
    if not df.empty and len(df) > 0:
        # Mobilní vyhledávání a filtry
        hledat = st.text_input("🔍 Hledat podle názvu nebo adresy")
        filtr_rating = st.multiselect("Filtr Ratingu", ["A", "B", "C"], default=["A", "B", "C"])
        
        # Filtrování dat
        df_filtered = df.copy()
        
        # Ošetření, aby vyhledávání nespadlo na prázdných hodnotách
        df_filtered['Nazev'] = df_filtered['Nazev'].astype(str).fillna('')
        df_filtered['Adresa'] = df_filtered['Adresa'].astype(str).fillna('')
        
        if hledat:
            df_filtered = df_filtered[df_filtered['Nazev'].str.contains(hledat, case=False) | 
                                      df_filtered['Adresa'].str.contains(hledat, case=False)]
        
        if 'Rating' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['Rating'].isin(filtr_rating)]
        
        st.write(f"Nalezeno klientů: {len(df_filtered)}")
        
        # Zobrazení karet (Cards) pod sebou – ideální na mobil
        for idx, row in df_filtered.iterrows():
            with st.expander(f"**{row.get('Nazev', 'Neznámý')}** ({row.get('Rating', '-')})"):
                st.write(f"📍 **Adresa:** {row.get('Adresa', '-')}")
                st.write(f"👤 **Kontakt:** {row.get('Kontaktni_Osoba', '-')}")
                st.write(f"🧥 **Kapacita šatny:** {row.get('Kapacita_Satny', 0)} ks")
                st.write(f"💰 **Cena šatny:** {row.get('Cena_Satny', 0)} Kč")
                st.write(f"📝 **Poznámka:** {row.get('Poznamka', '-')}")
    else:
        st.info("V databázi zatím nejsou žádná data. Přidej první provozovnu v záložce vedle!")

with tab_pridat:
    st.subheader("Zadat novou provozovnu")
    with st.form(key="mobilni_crm_form", clear_on_submit=True):
        nazev = st.text_input("Název provozovny *")
        adresa = st.text_input("Adresa provozovny")
        rating = st.selectbox("Rating", ["A", "B", "C"])
        kapacita = st.number_input("Kapacita šatny", min_value=0, step=1, value=0)
        cena = st.number_input("Cena šatny (Kč/ks)", min_value=0.0, step=1.0, value=0.0)
        kontakt = st.text_input("Kontaktní osoba")
        poznamka = st.text_area("Volný text / Popis")
        
        submit_button = st.form_submit_button(label="🚀 Uložit do CRM")
        
        if submit_button:
            if not nazev:
                st.error("Název provozovny je povinný!")
            else:
                novy_radek = pd.DataFrame([{
                    "Nazev": nazev, "Adresa": adresa, "Rating": rating,
                    "Kapacita_Satny": int(kapacita), "Cena_Satny": float(cena),
                    "Kontaktni_Osoba": kontakt, "Poznamka": poznamka
                }])
                
                # Propojení starých a nových dat
                if df.empty:
                    aktualizovany_df = novy_radek
                else:
                    aktualizovany_df = pd.concat([df, novy_radek], ignore_index=True)
                
                # Zápis zpět do Google Sheets
                conn.update(data=aktualizovany_df)
                st.success(f"Klient '{nazev}' byl úspěšně uložen!")
                st.cache_data.clear()
                st.rerun()
