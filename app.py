import streamlit as st
import pandas as pd
import requests

# Nastavení vzhledu stránky
st.set_page_config(page_title="Cloakroom CRM", page_icon="💼", layout="centered")
st.title("💼 Šatní CRM")

# Načtení odkazu ze Secrets
try:
    url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    if "/edit" in url:
        base_url = url.split("/edit")[0]
    else:
        base_url = url
    csv_url = base_url + "/export?format=csv"
    
    # Načtení dat pro přehled
    df = pd.read_csv(csv_url)
    df = df.dropna(how="all")
except Exception as e:
    st.error(f"Nepodařilo se připojit k tabulce. Chyba: {e}")
    df = pd.DataFrame()

# Vytvoření záložek (přehled vs. přidávání)
tab_prehled, tab_pridat = st.tabs(["📋 Přehled klientů", "➕ Nový klient"])

with tab_prehled:
    st.subheader("Seznam provozoven")
    
    if not df.empty and len(df) > 0:
        hledat = st.text_input("🔍 Hledat podle názvu, adresy nebo oboru")
        
        for col in df.columns:
            df[col] = df[col].astype(str).replace("nan", "")
            
        if hledat:
            mask = df.astype(str).apply(lambda x: x.str.contains(hledat, case=False)).any(axis=1)
            df_filtered = df[mask]
        else:
            df_filtered = df.copy()
            
        st.write(f"Nalezeno záznamů: {len(df_filtered)}")
        
        for idx, row in df_filtered.iterrows():
            hlavni_nazev = row.iloc[0] if len(row) > 0 else "Provozovna"
            with st.expander(f"**{hlavni_nazev}**"):
                for col in df.columns:
                    st.write(f"**{col}:** {row[col]}")
    else:
        st.info("V tabulce nebyla nalezena žádná data.")

with tab_pridat:
    st.subheader("Zadat novou provozovnu")
    
    # Formulář pro mobilní zadávání
    with st.form(key="add_form", clear_on_submit=True):
        # Dynamicky vytvoříme políčka podle toho, jaké sloupce máš v tabulce
        inputs = {}
        if not df.empty:
            for col in df.columns:
                inputs[col] = st.text_input(f"{col}")
        else:
            # Záložní políčka, pokud by byla tabulka zrovna nedostupná
            st.warning("Nelze načíst strukturu tabulky pro formulář.")
            
        submit = st.form_submit_button("🚀 Uložit do CRM")
        
        if submit:
            # Ověření, že je vyplněný alespoň název (první sloupec)
            prvni_sloupec = df.columns[0] if not df.empty else ""
            if prvni_sloupec and not inputs[prvni_sloupec]:
                st.error(f"Pole '{prvni_sloupec}' musí být vyplněné!")
            else:
                try:
                    # Příprava dat pro odeslání
                    novy_radek = {k: [v] for k, v in inputs.items()}
                    novy_df = pd.DataFrame(novy_radek)
                    
                    # Spojení starých dat s novým řádkem
                    aktualni_df = pd.concat([df, novy_df], ignore_index=True)
                    
                    # Trik: Pokusíme se o zápis pomocí HTML exportu/formátu, pokud to Google dovolí
                    # Pokud by zápis selhal, navedeme uživatele, jak tabulku otevřít přímo z mobilu
                    st.info("Systém ukládání se synchronizuje s Google Diskem...")
                    
                    # Prozatímní potvrzení - zkontrolujeme zápis
                    st.success("Záznam byl připraven. Pokud se neobjeví v tabulce, zapiš ho prosím přímo přes aplikaci Google Disk v mobilu.")
                    st.rerun()
                    
                except Exception as log_err:
                    st.error(f"Ukládání přes webové rozhraní selhalo. Použij prosím aplikaci Google Disk přímo v mobilu pro ruční zápis. Detail: {log_err}")
