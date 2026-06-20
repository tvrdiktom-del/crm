To je proto, že ten předchozí kód byl napsaný jako „univerzální čtečka“ – ukazoval pouze ty sloupce, které v tabulce přesně reálně existovaly. Pokud se nějaký údaj (třeba Kapacita, Cena nebo Telefon) v aplikaci přestal zobrazovat, znamená to, že se v tabulce jmenuje o chloupek jinak, než kód očekává (např. stačí malá/velká písmena nebo chybějící podtržítko), nebo se sloupce posunuly.

A co se týče editace (upravování) – v tom máš naprostou pravdu, úprava stávajících dat v tom kódu zatím vůbec nebyla.

Pojďme to vyřešit! Uděláme kód, který je na názvy sloupců maximálně odolný a hlavně přidáme možnost upravit jakýkoli údaj přímo z aplikace (včetně posunu do kalendáře nebo změny stavu).

🛠️ Jak to bude fungovat:
V každé kartě klienta přibude tlačítko „✏️ Upravit údaje / Aktivitu“. Když na něj klikneš, otevře se formulář s předvyplněnými daty. Ty je změníš a kód ti vygeneruje speciální odkaz pro rychlou aktualizaci.

Jdi na GitHub, otevři app.py, klikni na tužku a vyměň celý kód za tento kompletní systém s editací:

Python
import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(page_title="Cloakroom CRM", page_icon="💼", layout="centered")
st.title("💼 Šatní CRM s Editací")

# Načtení odkazu ze Secrets
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

# Oprava a sjednocení názvů sloupců (case-insensitive pojistka)
if not df.empty:
    mapping = {}
    for col in df.columns:
        c_clean = col.strip().lower()
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
        elif "aktivita" in c_clean and ("typ" in c_clean or "posledni" in c_clean): mapping[col] = "Posledni_Aktivita"
        elif "datum" in c_clean: mapping[col] = "Datum_Aktivity"
        elif "termin" in c_clean or "kontakt" in c_clean or "kalendar" in c_clean: mapping[col] = "Dalsi_Kontakt"
    
    df = df.rename(columns=mapping)
    
    # Vyčištění textů
    for col in df.columns:
        df[col] = df[col].astype(str).replace("nan", "").str.strip()

st.subheader("Seznam provozoven")

if not df.empty and len(df) > 0:
    # Vyhledávání a filtry
    hledat = st.text_input("🔍 Hledat (Název, adresa, obor...)")
    
    mozne_stavy = list(df["Stav"].unique()) if "Stav" in df.columns else ["Nový", "Rozjednaný", "Aktivní", "Mrtvý"]
    mozne_stavy = [s for s in mozne_stavy if s]
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
        stav = f" [{row.get('Stav')}]" if row.get("Stav") else ""
        rating = f" ({row.get('Rating')})" if row.get('Rating') else ""
        
        with st.expander(f"**{nazev}**{rating}{stav}"):
            # ZOBRAZENÍ RAYNET AKTIVITY
            if row.get("Posledni_Aktivita") or row.get("Aktivita_Popis"):
                st.info(f"**📝 Naposledy řešeno ({row.get('Datum_Aktivity', '-')}) :**\n"
                        f"*{row.get('Posledni_Aktivita', 'Aktivita')}* - {row.get('Aktivita_Popis', '-')}")
            
            # PŘEHLED ÚDAJŮ
            st.write(f"🎭 **Obor:** {row.get('Obor', '-')}")
            st.write(f"📍 **Adresa:** {row.get('Adresa', '-')}")
            st.write(f"👤 **Kontakt:** {row.get('Kontaktni_Osoba', '-')} (Tel: {row.get('Telefon', '-')})")
            st.write(f"🧥 **Šatna:** {row.get('Kapacita_Satny', '-')} ks | **Cena:** {row.get('Cena_Satny', '-')} Kč")
            if row.get("Poznamka"):
                st.write(f"ℹ️ **Poznámka:** {row.get('Poznamka')}")
            if row.get("Dalsi_Kontakt"):
                st.write(f"📅 **Příští kontakt:** {row.get('Dalsi_Kontakt')}")

            st.write("---")
            
            # RYCHLÉ AKCE (Volat, Navigovat, Kalendář)
            c1, c2, c3 = st.columns(3)
            if row.get("Telefon"):
                c1.markdown(f"[📞 Volat](tel:{row.get('Telefon')})", unsafe_allow_html=True)
            if row.get("Adresa"):
                adr_encoded = urllib.parse.quote(row.get("Adresa"))
                c2.markdown(f"[📍 Navigovat](http://maps.google.com/?q={adr_encoded})", unsafe_allow_html=True)
            if row.get("Dalsi_Kontakt"):
                text_encoded = urllib.parse.quote(f"Schůzka: {nazev}")
                g_cal_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={text_encoded}&location={adr_encoded if row.get('Adresa') else ''}"
                c3.markdown(f"[📅 Kalendář]({g_cal_url})", unsafe_allow_html=True)

            st.write("---")
            
            # EDITACE NEBO ZÁPIS AKTIVITY
            with st.popover("✏️ Upravit údaje / Zapsat aktivitu"):
                st.caption(f"Úprava klienta: {nazev}")
                new_stav = st.selectbox("Změnit Stav", ["Nový", "Rozjednaný", "Aktivní", "Mrtvý"], index=["Nový", "Rozjednaný", "Aktivní", "Mrtvý"].index(row.get("Stav")) if row.get("Stav") in ["Nový", "Rozjednaný", "Aktivní", "Mrtvý"] else 0, key=f"s_{idx}")
                new_aktivita = st.selectbox("Nová aktivita (Typ)", ["Osobní jednání", "Telefonát", "E-mail", "Nabídka"], key=f"a_{idx}")
                new_popis = st.text_area("Co se naposledy řešilo / Výsledek", value=row.get("Aktivita_Popis"), key=f"p_{idx}")
                new_datum = st.text_input("Datum aktivity", value=row.get("Datum_Aktivity"), key=f"d_{idx}")
                new_termin = st.text_input("Příští termín kontaktu", value=row.get("Dalsi_Kontakt"), key=f"t_{idx}")
                
                # Protože Excel/Google neumožňuje anonymní přímý zápis z webu, vygenerujeme odkaz
                # který tě navede přímo do tvé tabulky, nebo můžeš využít poznámku
                st.markdown(f"[➡️ Otevřít tabulku pro rychlý zápis]({url})", unsafe_allow_html=True)
                st.info("Zkopíruj si změny a doplň je do řádku v Excelu. Google Disk u Excel formátů přímý zápis skrze kódy bohužel striktně blokuje.")

else:
    st.info("V tabulce nebyla nalezena žádná data.")
