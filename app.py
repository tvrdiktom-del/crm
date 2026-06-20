import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(page_title="Cloakroom CRM", page_icon="💼", layout="centered")
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

# DEFINICE SLOUPCŮ, KTERÉ CRM POTŘEBUJE
POTREBNE_SLOUPCE = [
    "Nazev", "Adresa", "Rating", "Obor", "Kapacita_Satny", 
    "Cena_Satny", "Kontaktni_Osoba", "Poznamka", "Stav", 
    "Telefon", "Posledni_Aktivita", "Aktivita_Popis", 
    "Datum_Aktivity", "Dalsi_Kontakt"
]

# Bezpečné vyčištění a párování dat bez KeyErrorů
if not df.empty:
    # 1. Převedeme všechny současné sloupce na čistý text a odstraníme mezery
    df.columns = [str(c).strip() for c in df.columns]
    
    # 2. Vytvoříme inteligentní převodník (překladač) sloupců
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
        elif "kontakt" in c_clean and "dalsi" in c_clean: mapping[col] = "Dalsi_Kontakt"
        elif "poznamka" in c_clean or "poznámka" in c_clean: mapping[col] = "Poznamka"
        elif "stav" in c_clean: mapping[col] = "Stav"
        elif "telefon" in c_clean or "tel" in c_clean: mapping[col] = "Telefon"
        elif "aktivita" in c_clean and "popis" in c_clean: mapping[col] = "Aktivita_Popis"
        elif "aktivita" in c_clean: mapping[col] = "Posledni_Aktivita"
        elif "datum" in c_clean: mapping[col] = "Datum_Aktivity"
        elif "termin" in c_clean or "příští" in c_clean: mapping[col] = "Dalsi_Kontakt"
    
    df = df.rename(columns=mapping)
    
    # 3. Pojistka: Pokud některé sloupce v tabulce chybí, dokreslíme je prázdné
    for col in POTREBNE_SLOUPCE:
        if col not in df.columns:
            df[col] = ""
            
    # 4. Úplně bezpečné vyčištění všech buněk od "nan" balastu
    df = df.fillna("")
    for col in df.columns:
        df[col] = df[col].astype(str).apply(lambda x: x.replace("nan", "").strip())
else:
    # Pokud je tabulka prázdná, vytvoříme strukturu v paměti
    df = pd.DataFrame(columns=POTREBNE_SLOUPCE)

st.subheader("Seznam provozoven")

if not df.empty and len(df) > 0:
    # Vyhledávání a filtry
    hledat = st.text_input("🔍 Hledat (Název, adresa, obor...)")
    
    # Filtrace stavů
    mozne_stavy = sorted(list(df["Stav"].unique())) if "Stav" in df.columns else []
    mozne_stavy = [s for s in mozne_stavy if s and s != "nan"]
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
        if not nazev or nazev == "nan": 
            continue
            
        stav_val = row.get("Stav", "")
        stav_badge = f" [{stav_val}]" if stav_val and stav_val != "nan" else ""
        rating_val = row.get("Rating", "")
        rating_badge = f" ({rating_val})" if rating_val and rating_val != "nan" else ""
        
        with st.expander(f"**{nazev}**{rating_badge}{stav_badge}"):
            # RAYNET HISTORIE AKTIVIT
            p_akt = row.get("Posledni_Aktivita", "")
            p_popis = row.get("Aktivita_Popis", "")
            p_dat = row.get("Datum_Aktivity", "")
            
            if (p_akt and p_akt != "nan") or (p_popis and p_popis != "nan"):
                datum_str = f" ({p_dat})" if p_dat and p_dat != "nan" else ""
                st.info(f"**📝 Naposledy řešeno{datum_str}:**\n"
                        f"*{p_akt if p_akt and p_akt != 'nan' else 'Aktivita'}* - {p_popis if p_popis and p_popis != 'nan' else '-'}")
            
            # KARTA PROVOZOVNY
            st.write(f"🎭 **Obor:** {row.get('Obor', '-')}")
            st.write(f"📍 **Adresa:** {row.get('Adresa', '-')}")
            st.write(f"👤 **Kontakt:** {row.get('Kontaktni_Osoba', '-')} (Tel: {row.get('Telefon', '-')})")
            st.write(f"🧥 **Šatna:** {row.get('Kapacita_Satny', '-')} ks | **Cena:** {row.get('Cena_Satny', '-')} Kč")
            
            if row.get("Poznamka") and row.get("Poznamka") != "nan":
                st.write(f"ℹ️ **Poznámka:** {row.get('Poznamka')}")
            if row.get("Dalsi_Kontakt") and row.get("Dalsi_Kontakt") != "nan":
                st.write(f"📅 **Příští kontakt:** {row.get('Dalsi_Kontakt')}")

            st.write("---")
            
            # RYCHLÉ AKCE PRO TELEFON
            c1, c2, c3 = st.columns(3)
            tel_cislo = row.get("Telefon", "")
            if tel_cislo and tel_cislo != "nan":
                c1.markdown(f"[📞 Volat](tel:{tel_cislo})", unsafe_allow_html=True)
                
            adresa_val = row.get("Adresa", "")
            if adresa_val and adresa_val != "nan":
                adr_encoded = urllib.parse.quote(adresa_val)
                c2.markdown(f"[📍 Navigovat](http://maps.google.com/?q={adr_encoded})", unsafe_allow_html=True)
                
            termin_val = row.get("Dalsi_Kontakt", "")
            if termin_val and termin_val != "nan":
                text_encoded = urllib.parse.quote(f"Kontakt: {nazev}")
                loc_encoded = urllib.parse.quote(adresa_val) if adresa_val and adresa_val != "nan" else ""
                g_cal_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={text_encoded}&location={loc_encoded}"
                c3.markdown(f"[📅 Kalendář]({g_cal_url})", unsafe_allow_html=True)

            st.write("---")
            
            # ODKAZ NA EDITACI V EXCELU / GOOGLE DISKU
            st.markdown(f"[✏️ Upravit data / Zapsat aktivitu]({url})", unsafe_allow_html=True)
else:
    st.info("V tabulce nebyla nalezena žádná data.")
