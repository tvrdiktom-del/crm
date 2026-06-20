import streamlit as st
import pandas as pd

# Nastavení vzhledu stránky
st.set_page_config(page_title="Cloakroom CRM", page_icon="💼", layout="centered")
st.title("💼 Šatní CRM")

# Přímé načtení veřejného odkazu z tvých Secrets
try:
    # Získání čisté adresy ze Streamlit Secrets
    url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    
    # Úprava odkazu, aby z něj Pandas mohl přímo stáhnout data (funguje pro jakýkoli typ tabulky na Disku)
    if "/edit" in url:
        csv_url = url.split("/edit")[0] + "/export?format=csv"
    else:
        csv_url = url
        
    # Načtení dat jako CSV
    df = pd.read_csv(csv_url)
    
    # Odstranění prázdných řádků a sloupců pro čisté zobrazení
    df = df.dropna(how="all")
    
except Exception as e:
    st.error(f"Nepodařilo se připojit k tabulce. Zkontroluj odkaz v Secrets. Chyba: {e}")
    df = pd.DataFrame()

st.subheader("Seznam provozoven")

if not df.empty and len(df) > 0:
    # Vyhledávání na mobilu
    hledat = st.text_input("🔍 Hledat podle názvu, adresy nebo oboru")
    
    # Převedení sloupců na text, aby vyhledávání nespadlo
    for col in df.columns:
        df[col] = df[col].astype(str).replace("nan", "")
        
    # Filtrování podle hledaného výrazu
    if hledat:
        mask = df.astype(str).apply(lambda x: x.str.contains(hledat, case=False)).any(axis=1)
        df_filtered = df[mask]
    else:
        df_filtered = df.copy()
        
    st.write(f"Nalezeno záznamů: {len(df_filtered)}")
    
    # Dynamické zobrazení všech sloupců, které v tabulce reálně máš
    for idx, row in df_filtered.iterrows():
        # Použijeme první sloupec jako hlavní název karty
        hlavni_nazev = row.iloc[0] if len(row) > 0 else "Provozovna"
        
        with st.expander(f"**{hlavni_nazev}**"):
            for col in df.columns:
                # Vypíšeme všechny detaily pod sebe
                st.write(f"**{col}:** {row[col]}")
else:
    st.info("V tabulce nebyla nalezena žádná data. Zkontroluj, zda v ní máš zadané řádky.")
