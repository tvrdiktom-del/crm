import streamlit as st
import pandas as pd
import urllib.parse

# Široké rozvržení, aby bylo vlevo a vpravo dost místa
st.set_page_config(page_title="Cloakroom CRM", page_icon="💼", layout="wide")
st.title("💼 Šatní CRM")

# Bezpečné načtení odkazu
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

# Definice potřebných sloupců
POTREBNE_SLOUPCE = [
    "Nazev", "Adresa", "Rating", "Obor", "Kapacita_Satny", 
    "Cena_Satny", "Kontaktni_Osoba", "Poznamka", "Stav", 
    "Telefon", "Posledni_Aktivita", "Aktivita_Popis", 
    "Datum_Aktivity", "Dalsi_Kontakt"
]

# Sjednocení a vyčištění sloupců
if not df.empty:
    df.columns = [str(c).strip() for c in df.columns]
    mapping = {}
    for col in df.columns:
        c_clean = col.lower()
        if "nazev" in c_clean or "název" in c_clean: mapping[col] = "Nazev"
        elif "adresa" in c_clean: mapping[col] = "Adresa"
        elif "rating" in c_clean: mapping[col] = "Rating"
        elif "obor" in c_clean: mapping[col] = "Obor"
        elif "kapacita" in c_clean: mapping[col] = "Kapacita_Satny"
        elif "cena" in c_clean: mapping[col] = "Cena_Satny"
        elif "kontakt" in c_clean and "osoba" in c_clean: mapping[col] = "Kontaktni_Osoba"
        elif "stav" in c_clean: mapping[col] = "Stav"
        elif "telefon" in c_clean or "tel" in c_clean: mapping[col] = "Telefon"
        elif "aktivita" in c_clean and "popis" in c_clean: mapping[col] = "Aktivita_Popis"
        elif "aktivita" in c_clean: mapping[col] = "Posledni_Aktivita"
        elif "datum" in c_clean: mapping[col] = "Datum_Aktivity"
        elif "termin" in c_clean or "příští" in c_clean: mapping[col] = "Dalsi_Kontakt"
    
    df = df.rename(columns=mapping)
    for col in POTREBNE_SLOUPCE:
        if col not in df.columns:
            df[col] = ""
    df = df.fillna("")
    for col in df.columns:
        df[col] = df[col].astype(str).apply(lambda x: x.replace("nan", "").strip())
else:
    df = pd.DataFrame(columns=POTREBNE_SLOUPCE)

# ROZDĚLENÍ OBRAZOVKY NA DVA SLOUPCE (Nalevo přehled, Napravo přidávání)
sloupec_levy, sloupec_pravy = st.columns([3, 2])

# --- LEVÁ STRANA: VYHLEDÁVÁNÍ A PŘEHLED ---
with sloupec_levy:
    st.subheader("📋 Seznam provozoven")
    
    if not df.empty and len(df) > 0:
        hledat = st.text_input("🔍 Hledat (Název, adresa, obor...)")
        
        # Detekce stavů
        mozne_stavy = sorted(list(df["Stav"].unique())) if "Stav" in df.columns else []
        mozne_stavy = [s for s in mozne_stavy if s and s != "nan" and s != ""]
        if not mozne_stavy:
            mozne_stavy = ["Nový", "Rozjednaný", "Aktivní", "Mrtvý"]
            
        filtr_stav = st.multiselect("Filtrovat podle stavu", mozne_stavy, default=mozne_stavy)

        df_filtered = df.copy()
        if "Stav" in df_filtered.columns and filtr_stav:
            df_filtered = df_filtered[df_filtered["Stav"].isin(filtr_stav)]
            
        if hledat:
            mask = df_filtered.astype(str).apply(lambda x: x.str.contains(hledat, case=False)).any(axis=1)
            df_filtered = df_filtered[mask]

        st.write(f"Nalezeno záznamů: {len(df_filtered)}")

        for idx, row in df_filtered.iterrows():
            nazev = row.get("Nazev", "").strip()
            if not nazev or nazev == "nan" or nazev == "": 
                continue
                
            stav_val = row.get("Stav", "")
            stav_badge = f" [{stav_val}]" if stav_val else ""
            rating_val = row.get("Rating", "")
            rating_badge = f" ({rating_val})" if rating_val else ""
            
            with st.expander(f"**{nazev}**{rating_badge}{stav_badge}"):
                # Raynet Aktivita
                p_akt = row.get("Posledni_Aktivita", "")
                p_popis = row.get("Aktivita_Popis", "")
                p_dat = row.get("Datum_Aktivity", "")
                if p_akt or p_popis:
                    st.info(f"**📝 Naposledy řešeno{f' ({p_dat})' if p_dat else ''}:**\n*{p_akt}* - {p_popis}")
                
                # Info o klientovi
                st.write(f"🎭 **Obor:** {row.get('Obor', '-')}")
                st.write(f"📍 **Adresa:** {row.get('Adresa', '-')}")
                st.write(f"👤 **Kontakt:** {row.get('Kontaktni_Osoba', '-')} (Tel: {row.get('Telefon', '-')})")
                st.write(f"🧥 **Šatna:** {row.get('Kapacita_Satny', '-')} ks | **Cena:** {row.get('Cena_Satny', '-')} Kč")
                if row.get("Poznamka"): st.write(f"ℹ️ **Poznámka:** {row.get('Poznamka')}")
                if row.get("Dalsi_Kontakt"): st.write(f"📅 **Příští kontakt:** {row.get('Dalsi_Kontakt')}")
                
                st.write("---")
                # Mobilní akce
                c1, c2, c3 = st.columns(3)
                if row.get("Telefon"): c1.markdown(f"[📞 Volat](tel:{row.get('Telefon')})", unsafe_allow_html=True)
                if row.get("Adresa"): c2.markdown(f"[📍 Navigovat](http://maps.google.com/?q={urllib.parse.quote(row.get('Adresa'))})", unsafe_allow_html=True)
                if row.get("Dalsi_Kontakt"):
                    g_cal = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={urllib.parse.quote('Kontakt: ' + nazev)}"
                    c3.markdown(f"[📅 Kalendář]({g_cal})", unsafe_allow_html=True)
                    
                st.write("---")
                st.markdown(f"[✏️ Upravit řádek přímo v tabulce]({url})", unsafe_allow_html=True)
    else:
        st.info("Žádná data k zobrazení.")

# --- PRAVÁ STRANA: FORMULÁŘ PRO PŘIDÁVÁNÍ ---
with sloupec_pravy:
    st.subheader("➕ Nový klient")
    with st.form(key="novy_klient_form", clear_on_submit=True):
        f_nazev = st.text_input("Název provozovny *")
        f_obor = st.text_input("Obor (např. klub, divadlo)")
        f_adresa = st.text_input("Adresa")
        f_stav = st.selectbox("Stav", ["Nový", "Rozjednaný", "Aktivní", "Mrtvý"])
        f_rating = st.selectbox("Rating", ["A", "B", "C"])
        f_kapacita = st.text_input("Kapacita šatny")
        f_cena = st.text_input("Cena šatny")
        f_kontakt = st.text_input("Kontaktní osoba")
        f_telefon = st.text_input("Telefon")
        f_poznamka = st.text_area("Poznámka")
        
        tlacitko = st.form_submit_button("🚀 Připravit k uložení")
        
        if tlacitko:
            if not f_nazev:
                st.error("Název provozovny je povinný!")
            else:
                st.success(f"Klient '{f_nazev}' je připraven!")
                # Vygenerujeme odkaz na přímé otevření tabulky pro rychlé zapsání
                st.markdown(f"### [➡️ KLIKNI ZDE PRO ZÁPIS DO TABULKY]({url})", unsafe_allow_html=True)
                st.info("Opravdu skvělá práce! Stačí kliknout na odkaz výše a zapsat údaje na nový řádek.")
