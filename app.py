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

# Bezpečné vyčištění a párování sloupců
if not df.empty:
    mapping = {}
    for col in df.columns:
        c_clean = str(col).strip().lower()
        if "nazev" in c_clean or "název" in c_clean: mapping[col] = "Nazev"
        elif "adresa" in c_clean: mapping[col] = "Adresa"
        elif "rating" in c_clean: mapping[col] = "Rating"
        elif "obor" in c_clean: mapping[col] = "Obor"
        elif "kapacita" in c_clean: mapping[col] = "Kapacita_Satny"
        elif "cena" in c_clean: mapping[col] = "Cena_Satny"
        elif "kontakt" in c_clean: mapping[col] = "Kontaktni_Osoba"
        elif "poznamka" in c_clean or "poznámka" in c_clean: mapping[col] = "Poznamka"
        elif "stav" in c_clean: mapping[col] = "Stav"
        elif "telefon" in c_clean or "tel" in c_clean: mapping[col] = "Telefon"
        elif "aktivita" in c_clean and "popis" in c_clean: mapping[col] = "Aktivita_Popis"
        elif "aktivita" in c_clean: mapping[col] = "Posledni_Aktivita"
        elif "datum" in c_clean: mapping[col] = "Datum_Aktivity"
        elif "termin" in c_clean or "příští" in c_clean: mapping[col] = "Dalsi_Kontakt"
    
    df = df.rename(columns=mapping)
    
    # Bezpečné odsazení - vyčištění prvek po prvku bez .str chyb
    for col in df.columns:
        df[col] = df[col].fillna("").apply(lambda x: str(x).strip())

st.subheader("Seznam provozoven")

if not df.empty and len(df) > 0:
    # Vyhledávání a filtry
    hledat = st.text_input("🔍 Hledat (Název, adresa, obor...)")
    
    # Detekce stavů pro filtr
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
        nazev = row.get("Nazev", "Neznámý")
        if not nazev or nazev == "nan" or nazev == "": 
            continue
            
        stav_val = row.get("Stav", "")
        stav_badge = f" [{stav_val}]" if stav_val and stav_val != "nan" else ""
        rating_val = row.get("Rating", "")
        rating_badge = f" ({rating_val})" if rating_val and rating_val != "nan" else ""
        
        with st.expander(f"**{nazev}**{rating_badge}{stav_badge}"):
            # RAYNET AKTIVITA
            p_akt = row.get("Posledni_Aktivita", "")
            p_popis = row.get("Aktivita_Popis", "")
            p_dat = row.get("Datum_Aktivity", "")
            
            if (p_akt and p_akt != "nan" and p_akt != "") or (p_popis and p_popis != "nan" and p_popis != ""):
                datum_str = f" ({p_dat})" if p_dat and p_dat != "nan" else ""
                st.info(f"**📝 Naposledy řešeno{datum_str}:**\n"
                        f"*{p_akt if p_akt and p_akt != 'nan' else 'Aktivita'}* - {p_popis if p_popis and p_popis != 'nan' else '-'}")
            
            # KARTA KLIENTA
            st.write(f"🎭 **Obor:** {row.get('Obor', '-')}")
            st.write(f"📍 **Adresa:** {row.get('Adresa', '-')}")
            st.write(f"👤 **Kontakt:** {row.get('Kontaktni_Osoba', '-')} (Tel: {row.get('Telefon', '-')})")
            st.write(f"🧥 **Šatna:** {row.get('Kapacita_Satny', '-')} ks | **Cena:** {row.get('Cena_Satny', '-')} Kč")
            
            if row.get("Poznamka") and row.get("Poznamka") != "nan" and row.get("Poznamka") != "":
                st.write(f"ℹ️ **Poznámka:** {row.get('Poznamka')}")
            if row.get("Dalsi_Kontakt") and row.get("Dalsi_Kontakt") != "nan" and row.get("Dalsi_Kontakt") != "":
                st.write(f"📅 **Příští kontakt:** {row.get('Dalsi_Kontakt')}")

            st.write("---")
            
            # MOBILNÍ AKCE
            c1, c2, c3 = st.columns(3)
            tel_cislo = row.get("Telefon", "")
            if tel_cislo and tel_cislo != "nan" and tel_cislo != "":
                c1.markdown(f"[📞 Volat](tel:{tel_cislo})", unsafe_allow_html=True)
                
            adresa_val = row.get("Adresa", "")
            if adresa_val and adresa_val != "nan" and adresa_val != "":
                adr_encoded = urllib.parse.quote(adresa_val)
                c2.markdown(f"[📍 Navigovat](http://maps.google.com/?q={adr_encoded})", unsafe_allow_html=True)
                
            termin_val = row.get("Dalsi_Kontakt", "")
            if termin_val and termin_val != "nan" and termin_val != "":
                text_encoded = urllib.parse.quote(f"Kontaktovat: {nazev}")
                loc_encoded = urllib.parse.quote(adresa_val) if adresa_val and adresa_val != "nan" else ""
                g_cal_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={text_encoded}&location={loc_encoded}"
                c3.markdown(f"[📅 Kalendář]({g_cal_url})", unsafe_allow_html=True)

            st.write("---")
            
            # ODKAZ NA EDITACI V MOBILU
            st.markdown(f"[✏️ Upravit data / Zapsat aktivitu]({url})", unsafe_allow_html=True)
else:
    st.info("V tabulce nebyla nalezena žádná data.")
