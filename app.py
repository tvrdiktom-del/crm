import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Nastavení mobilního vzhledu stránky
st.set_page_config(page_title="Cloakroom CRM", page_icon="💼", layout="centered")
st.title("💼 Šatní CRM")

# Propojení s Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Načtení dat (s cache na 5 minut kvůli úspoře dat a rychlosti načítání na mobilu)
try:
    df = conn.read(ttl="5m")
except Exception as e:
    st.error("Nepodařilo se načíst data z Google Tabulky.")
    df = pd.DataFrame()

# Záložky pro mobilní rozhraní
tab_prehled, tab_pridat = st.tabs(["📋 Přehled klientů", "➕ Nový klient"])

with tab_prehled:
    st.subheader("Seznam provozoven")
    if not df.empty and len(df) > 0:
        # Mobilní vyhledávání a filtry
        hledat = st.text_input("🔍 Hledat podle názvu nebo adresy")
        filtr_rating = st.multiselect("Filtr Ratingu", ["A", "B", "C"], default=["A", "B", "C"])
        
        # Filtrování
        df_filtered = df.copy()
        if hledat:
            df_filtered = df_filtered[df_filtered['Nazev'].str.contains(hledat, case=False, na=False) | 
                                      df_filtered['Adresa'].str.contains(hledat, case=False, na=False)]
        df_filtered = df_filtered[df_filtered['Rating'].isin(filtr_rating)]
        
        st.write(f"Nalezeno klientů: {len(df_filtered)}")
        
        # Zobrazení karet (Cards) místo široké tabulky – ideální na šířku mobilu
        for idx, row in df_filtered.iterrows():
            with st.expander(f"**{row['Nazev']}** ({row['Rating']})"):
                st.write(f"📍 **Adresa:** {row['Adresa']}")
                st.write(f"👤 **Kontakt:** {row['Kontaktni_Osoba']}")
                st.write(f"🧥 **Kapacita šatny:** {row['Kapacita_Satny']} ks")
                st.write(f"💰 **Cena šatny:** {row['Cena_Satny']} Kč")
                st.write(f"📝 **Poznámka:** {row['Poznamka']}")
    else:
        st.info("V databázi zatím nejsou žádná data.")

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
                aktualizovany_df = pd.concat([df, novy_radek], ignore_index=True)
                conn.update(data=aktualizovany_df)
                st.success(f"Klient '{nazev}' úspěšně uložen!")
                st.cache_data.clear()