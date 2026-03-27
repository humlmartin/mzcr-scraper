import streamlit as st
import pandas as pd
import plotly.express as px
import io
import requests
from html.parser import HTMLParser

st.set_page_config(
    page_title="MZCR Explorer",
    page_icon="🏥",
    layout="wide",
)

# ═══════════════════════════════════════════════════════════════════════════════
# ČÍSELNÍKY
# ═══════════════════════════════════════════════════════════════════════════════
KRAJE = {
    "CZ010":"Praha","CZ020":"Středočeský","CZ031":"Jihočeský","CZ032":"Plzeňský",
    "CZ041":"Karlovarský","CZ042":"Ústecký","CZ051":"Liberecký","CZ052":"Královéhradecký",
    "CZ053":"Pardubický","CZ063":"Kraj Vysočina","CZ064":"Jihomoravský",
    "CZ071":"Olomoucký","CZ072":"Zlínský","CZ080":"Moravskoslezský",
    "CZ0100":"Praha","CZ0200":"Středočeský","CZ0642":"Brno-město","CZ0643":"Brno-venkov",
    "CZ0806":"Ostrava-město","CZ020B":"Středočeský",
}
ODBORNOSTI = {
    "001":"Všeobecné lékařství","002":"Prakt. lékař pro děti","003":"Zubní lékařství",
    "004":"Lékárenství","006":"Fyzioterapie","014":"Chirurgie","017":"Cévní chirurgie",
    "019":"Ortopedie","020":"Plastická chirurgie","021":"Neurochirurgie",
    "022":"Neurologie","023":"Psychiatrie","025":"Dermatovenerologie",
    "026":"Urologie","027":"Oftalmologie","028":"ORL","030":"Gynekologie",
    "101":"Vnitřní lékařství","102":"Kardiologie","103":"Pneumologie",
    "104":"Gastroenterologie","105":"Nefrologie","106":"Endokrinologie",
    "107":"Revmatologie","108":"Hematologie","109":"Onkologie",
    "110":"Radiační onkologie","111":"Geriatrie","112":"Infekční lékařství",
    "113":"Alergologie","201":"Gynekologie a porodnictví","207":"Dětské lékařství",
    "208":"Neonatologie","301":"Anesteziologie","303":"Urgentní medicína",
    "305":"Radiologie","321":"Rehabilitace","401":"Klinická biochemie",
    "404":"Mikrobiologie","405":"Patologie","501":"Záchranná služba","600":"Lékárna",
}
_VYKONY_BASE = {
    "901":"Návštěva registrujícího lékaře","902":"Preventivní prohlídka",
    "903":"Cílené vyšetření","904":"Konziliární vyšetření","905":"Telefonická konzultace",
    "906":"Pohotovostní péče","907":"Pohotovostní návštěva","908":"Návštěva — doprovod",
    "909":"Dispenzarizace","910":"EKG","911":"EKG Holter","912":"Spirometrie",
    "913":"UZ vyšetření","914":"Preventivní prohlídka rozšířená",
    "916":"Odběr krve","917":"Aplikace infúze","918":"Injekce i.m./s.c.",
    "919":"Injekce i.v.","921":"Biochemie","922":"Krevní obraz",
    "923":"Koagulace (INR)","924":"Sérologické vyšetření",
    "925":"Moč — chemie + sediment","926":"Stěr","927":"Kultivace",
    "928":"Glykémie kapilární","929":"PSA","930":"RTG","931":"CT","932":"MRI",
    "933":"Endoskopie","934":"Kolposkopie","935":"Tonometrie","936":"Audiometrie",
    "937":"Alergologické testy","938":"Fyzikální terapie","939":"Rehabilitace",
    "940":"Edukace pacienta","941":"Ošetření rány","943":"Incize","944":"Excize",
    "945":"Sutura","946":"Sádrování","948":"Injekce do kloubu","950":"Vakcinace",
    "951":"Desenzibilizace","952":"Cévkování","956":"Kyslíková terapie",
    # 5místné kódy
    "09511":"Biochemické vyšetření","09543":"Krevní obraz KO+diff",
    "09119":"EKG","09123":"Spirometrie","09133":"EKG Holter",
    "09216":"Echokardiografie","11503":"RTG hrudníku",
    "11521":"CT vyšetření","11527":"MRI vyšetření",
    "11550":"Sonografie břicha","11551":"Sonografie malé pánve",
    "13022":"Gastroskopie","13023":"Kolonoskopie",
    "01011":"Vyšetření prakt. lékařem","01013":"Preventivní prohlídka",
    "01021":"Návštěva u pacienta","01111":"Dispenzární prohlídka",
    "22001":"Gynekologické vyšetření","22011":"Cytologický stěr",
    "23001":"Dětské vyšetření","26001":"Neurologické vyšetření",
    "27001":"Oftalmologické vyšetření","28001":"ORL vyšetření",
    "29001":"Stomatologické vyšetření","29011":"Extrakce zubu",
    "31001":"Interní vyšetření","85011":"Vakcinace",
}
# Automaticky přidej varianty s nulami: 901 → 00901, 00901 → 901
VYKONY = dict(_VYKONY_BASE)
for _k, _v in list(_VYKONY_BASE.items()):
    VYKONY[_k.zfill(5)] = _v        # 901 → 00901
    _stripped = _k.lstrip("0") or "0"
    VYKONY[_stripped] = _v           # 00901 → 901
POHLAVI = {"1":"Muž","2":"Žena","M":"Muž","F":"Žena","Z":"Žena"}
VEKOVE_SKUPINY = {
    "66000004":"0–4 let","66005009":"5–9 let","66010014":"10–14 let",
    "66015019":"15–19 let","66020024":"20–24 let","66025029":"25–29 let",
    "66030034":"30–34 let","66035039":"35–39 let","66040044":"40–44 let",
    "66045049":"45–49 let","66050054":"50–54 let","66055059":"55–59 let",
    "66060064":"60–64 let","66065069":"65–69 let","66070074":"70–74 let",
    "66075079":"75–79 let","66080084":"80–84 let","66085999":"85+ let",
}

# ═══════════════════════════════════════════════════════════════════════════════
# KATALOG — ověřené URL (složka/přesný název souboru)
# ═══════════════════════════════════════════════════════════════════════════════
BASE = "https://data.mzcr.cz/data/distribuce/"

CATALOG = {
    "Výkony zdravotní péče": [
        {"name":"Výkony per org. (IČO) — aktuální",          "dir":"367","file":"Otevrena-data-NR-04-02-vykony-ico.csv",                            "code":"NR-04-02","size":"326 MB"},
        {"name":"Výkony per org. (IČO) — 2024",              "dir":"367","file":"Otevrena-data-NR-04-02-Vykony-ICO-2024-01.csv",                   "code":"NR-04-02","size":"300 MB"},
        {"name":"Výkony per pracoviště + odbornost + měsíc", "dir":"363","file":"Otevrena-data-NR-04-24-vykony-rok-mesic-icz-odbornost.csv",       "code":"NR-04-24","size":""},
        {"name":"Výkony dle formy péče + odbornost",         "dir":"365","file":"Otevrena-data-NR-04-25-vykony-forma-odbornost.csv",               "code":"NR-04-25","size":""},
        {"name":"Výkony per odbornost (celá ČR)",            "dir":"368","file":"Otevrena-data-NR-04-06-vykony-odbornost.csv",                     "code":"NR-04-06","size":""},
        {"name":"Výkony plný detail (IČZ+odbornost+dg.)",   "dir":"376","file":"Otevrena-data-NR-04-01-Vykony-2024-01.csv",                       "code":"NR-04-01","size":"1.7 GB"},
        {"name":"Výkony per pracoviště — roční",             "dir":"359","file":"Otevrena-data-NR-04-23-vykony-icz-odbornost-rocni.csv",           "code":"NR-04-23","size":""},
        {"name":"Výkony dle věku a pohlaví",                 "dir":"370","file":"Otevrena-data-NR-04-08-vykony-vek-pohlavi.csv",                   "code":"NR-04-08","size":""},
        {"name":"Výkony + tříznaková diagnóza (MKN)",        "dir":"374","file":"Otevrena-data-NR-04-05-Triznakove-diagnozy-MKN-2024-01.csv",      "code":"NR-04-05","size":""},
        {"name":"Diagnóza per odbornost",                    "dir":"371","file":"Otevrena-data-NR-04-09-diagnoza-odbornost.csv",                   "code":"NR-04-09","size":""},
        {"name":"Diagnóza per pracoviště (IČZ)",             "dir":"364","file":"Otevrena-data-NR-04-26-diagnoza-icz.csv",                         "code":"NR-04-26","size":""},
    ],
    "Hospitalizace": [
        {"name":"Hospitalizace",               "dir":"338","file":"Otevrena-data-NR-04-18-hospitalizace.csv",          "code":"NR-04-18","size":""},
        {"name":"Hospitalizace + diagnózy",    "dir":"339","file":"Otevrena-data-NR-04-19-hospitalizace-diagnoza.csv", "code":"NR-04-19","size":""},
        {"name":"Hospitalizace + výkony",      "dir":"340","file":"Otevrena-data-NR-04-20-hospitalizace-vykony.csv",   "code":"NR-04-20","size":""},
        {"name":"Hospitalizace + DRG",         "dir":"341","file":"Otevrena-data-NR-04-21-hospitalizace-drg.csv",      "code":"NR-04-21","size":""},
    ],
    "Léčivé přípravky": [
        {"name":"Léčiva — agregát (ATC × rok)",  "dir":"330","file":"Otevrena-data-NR-04-60-lecive-pripravky.csv",                    "code":"NR-04-60","size":""},
        {"name":"Léčiva — pracoviště + měsíc",   "dir":"328","file":"Otevrena-data-NR-04-60-lecive-pripravky-sukl-mesic-icp.csv",     "code":"NR-04-60","size":""},
        {"name":"Léčiva — noví pacienti",        "dir":"396","file":"Otevrena-data-NR-04-93-lecive-pripravky-novi-pacienti.csv",      "code":"NR-04-93","size":""},
        {"name":"Léčiva per pracoviště (IČZ)",   "dir":"361","file":"Otevrena-data-NR-04-17-lecive-pripravky-icz.csv",                "code":"NR-04-17","size":""},
    ],
    "Zdravotnické prostředky": [
        {"name":"Zdrav. prostředky — kód, měsíc, IČZ", "dir":"379","file":"Otevrena-data-NR-04-68-zdravotnicke-prostredky-kod-mesic-icz.csv","code":"NR-04-68","size":""},
        {"name":"Zdrav. prostředky per IČZ",            "dir":"382","file":"Otevrena-data-NR-04-86-zdravotnicke-prostredky-icz.csv",          "code":"NR-04-86","size":""},
    ],
    "Ostatní": [
        {"name":"Záchranná služba — výjezdy",  "dir":"314","file":"Otevrena-data-NR-04-10-zachranna-sluzba.csv",                        "code":"NR-04-10","size":""},
        {"name":"Mortalita — zhoubné nádory",  "dir":"377","file":"Otevrena-data-NR-07-02-mortalita-zhoubne-nadory-2024-01.csv",         "code":"NR-07-02","size":""},
        {"name":"Číselník IČZ → název, IČO",   "dir":"362","file":"Otevrena-data-OIS-12-02-ciselnik-icz-pojistovny.csv",                "code":"OIS-12-02","size":""},
        {"name":"Zdravotnická technika",        "dir":"401","file":"Otevrena-data-SSS-04-01-zdravotnicka-technika-zarizeni.csv",         "code":"SSS-04-01","size":""},
    ],
}

def get_url(item):
    return f"{BASE}{item['dir']}/{item['file']}"

# ═══════════════════════════════════════════════════════════════════════════════
# LIVE LOOKUP — zjistí skutečný název souboru v složce
# ═══════════════════════════════════════════════════════════════════════════════
class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, val in attrs:
                if name == "href" and val and "." in val and "?" not in val and ".." not in val:
                    self.links.append(val.split("/")[-1])

@st.cache_data(ttl=3600, show_spinner=False)
def get_actual_filename(dir_id: str) -> list[str]:
    """Vrátí seznam skutečných CSV souborů ve složce."""
    try:
        r = requests.get(f"{BASE}{dir_id}/", timeout=10)
        p = LinkParser()
        p.feed(r.text)
        return [f for f in p.links if f.endswith(".csv")]
    except:
        return []

# ═══════════════════════════════════════════════════════════════════════════════
# NAČÍTÁNÍ DAT
# cache_data vyžaduje hashable args — předáváme string URL a tuple filtrů
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False, max_entries=3)
def load_data(url: str, f_rok: str, f_ico: str, f_kod: str, f_odb: str) -> pd.DataFrame:
    progress = st.progress(0, text="Připojuji se…")
    status   = st.empty()

    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        total     = int(r.headers.get("Content-Length", 0))
        raw_bytes = b""
        downloaded = 0

        for chunk in r.iter_content(chunk_size=512 * 1024):  # 512 KB bloky
            raw_bytes  += chunk
            downloaded += len(chunk)
            if total:
                pct     = downloaded / total
                mb_done = downloaded / 1024 / 1024
                mb_tot  = total / 1024 / 1024
                progress.progress(pct, text=f"Stahuju… {mb_done:.1f} / {mb_tot:.1f} MB ({pct*100:.0f}%)")
            else:
                mb_done = downloaded / 1024 / 1024
                progress.progress(0.5, text=f"Stahuju… {mb_done:.1f} MB")

    progress.progress(1.0, text="Parsuju CSV…")
    status.caption(f"Načteno {downloaded/1024/1024:.1f} MB — parsuju…")

    df = pd.read_csv(
        io.BytesIO(raw_bytes),
        dtype=str,
        encoding="utf-8-sig",
        low_memory=False,
    )

    progress.empty()
    status.empty()

    # ── FILTRY ────────────────────────────────────────────────────────────────
    id_col  = next((c for c in ["ico","ICO","icz","ICZ"] if c in df.columns), None)
    odb_col = next((c for c in ["odbornost","odbornost_predepisujici"] if c in df.columns), None)

    if f_rok and "rok" in df.columns:
        df = df[df["rok"].str.strip() == f_rok.strip()]
    if f_ico and id_col:
        vals = {v.strip() for v in f_ico.replace(";",",").split(",") if v.strip()}
        df = df[df[id_col].isin(vals)]
    if f_kod and "kod" in df.columns:
        df = df[df["kod"].str.strip() == f_kod.strip()]
    if f_odb and odb_col:
        df = df[df[odb_col].str.strip() == f_odb.strip()]

    # ── OBOHACENÍ ─────────────────────────────────────────────────────────────
    if "kod" in df.columns:
        # kódy mohou mít přidané nuly (00901 → 901) — zkusíme obě varianty
        def lookup_vykon(k):
            k = str(k).strip()
            return VYKONY.get(k) or VYKONY.get(k.lstrip("0")) or VYKONY.get(k.lstrip("0").zfill(5)) or ""
        df.insert(df.columns.get_loc("kod")+1, "vykon_nazev",
                  df["kod"].apply(lookup_vykon))

    if odb_col:
        df.insert(df.columns.get_loc(odb_col)+1, f"{odb_col}_nazev",
                  df[odb_col].map(ODBORNOSTI).fillna(""))

    for col in ["kraj_kod","KRAJ_KOD","kraj_bydliste","kraj_zarizeni"]:
        if col in df.columns:
            df[col+"_nazev"] = df[col].map(KRAJE).fillna("")

    for col in ["pohlavi","POHLAVI"]:
        if col in df.columns:
            df[col+"_nazev"] = df[col].map(POHLAVI).fillna("")

    for col in ["umrti_vek_kategorie_kod","vek_kategorie","vekova_skupina"]:
        if col in df.columns:
            df[col+"_nazev"] = df[col].map(VEKOVE_SKUPINY).fillna("")

    # Numerické sloupce
    for nc in ["suma_mnozstvi","pocet_kontaktu","pocet_pacientu","suma_uhrad","uhrada_ZP","pocet_baleni"]:
        if nc in df.columns:
            df[nc] = pd.to_numeric(df[nc], errors="coerce")

    return df

# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def fmt(n):
    """Formátuje číslo s mezerou jako oddělovačem tisíců."""
    if pd.isna(n): return "—"
    return f"{int(n):,}".replace(",", " ")

def get_num_col(df):
    return next((c for c in ["suma_mnozstvi","pocet_kontaktu","pocet_pacientu","suma_uhrad","uhrada_ZP","pocet_baleni"] if c in df.columns), None)

def get_id_col(df):
    return next((c for c in ["ico","ICO","icz","ICZ"] if c in df.columns), None)

def get_odb_col(df):
    return next((c for c in ["odbornost","odbornost_predepisujici"] if c in df.columns), None)

# ═══════════════════════════════════════════════════════════════════════════════
# UI
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
  .main .block-container { padding-top: 1.2rem; padding-bottom: 0.5rem; }
  [data-testid="stMetric"] { background: #f8f7f4; border-radius: 8px; padding: 10px 14px; }
  [data-testid="stMetricLabel"] { font-size: 11px !important; color: #9a9790 !important; }
  [data-testid="stMetricValue"] { font-size: 22px !important; font-weight: 600 !important; }
  div.stTabs [data-baseweb="tab"] { font-size: 13px; }
</style>
""", unsafe_allow_html=True)

st.title("🏥 MZCR Explorer")
st.caption("Otevřená data ÚZIS ČR · data.mzcr.cz")

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📂 Datová sada")

    group  = st.selectbox("Skupina", list(CATALOG.keys()), label_visibility="collapsed")
    items  = CATALOG[group]
    i_names = [f"{it['name']}{'  ·  '+it['size'] if it['size'] else ''}" for it in items]
    idx    = st.selectbox("Soubor", range(len(items)), format_func=lambda i: i_names[i], label_visibility="collapsed")
    item   = items[idx]

    # Zkusí najít skutečný název souboru
    real_files = get_actual_filename(item["dir"])
    if real_files and item["file"] not in real_files:
        st.warning(f"⚠ Soubor `{item['file']}` nenalezen. Dostupné:\n\n" + "\n\n".join(f"- `{f}`" for f in real_files))
        item = dict(item, file=real_files[0])  # použij první dostupný

    url = get_url(item)
    st.caption(f"`{item['code']}` · [{item['file']}]({url})")

    st.divider()
    st.header("🔍 Filtry před načtením")
    st.caption("Filtrují za běhu — šetří paměť. Prázdné = vše načíst.")

    f_rok = st.text_input("Rok", placeholder="např. 2024")
    f_ico = st.text_input("IČO / IČZ", placeholder="např. 46523782")
    f_kod = st.text_input("Kód výkonu", placeholder="např. 910")
    f_odb = st.text_input("Odbornost", placeholder="např. 001 = Všeobecné lék.")

    if not any([f_rok, f_ico, f_kod, f_odb]):
        st.warning("⚠ Žádný filtr — načte se celý soubor (může být 300 MB+).")

    load_btn = st.button("▶ Načíst data", type="primary", use_container_width=True)

    st.divider()
    with st.expander("Vlastní URL"):
        custom_url = st.text_input("URL souboru CSV", placeholder="https://data.mzcr.cz/…")
        if custom_url:
            url = custom_url

# ── NAČÍTÁNÍ ──────────────────────────────────────────────────────────────────
cache_key = (url, f_rok, f_ico, f_kod, f_odb)

if load_btn:
    # Vymažeme cache pro tuto kombinaci aby se vždy stáhla čerstvá data
    load_data.clear()
    try:
        df = load_data(url, f_rok, f_ico, f_kod, f_odb)
        st.session_state["df"] = df
        st.session_state["cache_key"] = cache_key
    except Exception as e:
        st.error(f"Chyba: {e}")
        st.stop()

elif "df" in st.session_state:
    df = st.session_state["df"]
else:
    st.info("👈 Vlevo vyber datovou sadu a klikni **Načíst data**.")
    st.markdown("""
    **Jak to funguje:**
    1. Vyber skupinu a soubor
    2. Volitelně nastav filtry (šetří paměť při velkých souborech)
    3. Klikni **Načíst data**
    4. Prohlíží, filtruj, vizualizuj, exportuj do Excelu
    """)
    st.stop()

# ── VÝSLEDKY ──────────────────────────────────────────────────────────────────
nc     = get_num_col(df)
id_col = get_id_col(df)
odb_col= get_odb_col(df)

# Metriky
m = st.columns(5)
m[0].metric("Řádků",        fmt(len(df)))
m[1].metric("IČO/IČZ",      fmt(df[id_col].nunique()) if id_col else "—")
m[2].metric("Kódů výkonů",  fmt(df["kod"].nunique()) if "kod" in df.columns else "—")
m[3].metric("Odborností",   fmt(df[odb_col].nunique()) if odb_col else "—")
m[4].metric(f"Σ {nc or '?'}", fmt(df[nc].sum()) if nc else "—")

st.divider()

# ── ZÁLOŽKY ───────────────────────────────────────────────────────────────────
t_data, t_ico, t_kod, t_odb, t_graf, t_exp = st.tabs([
    "📋 Data", "🏢 Souhrn IČO", "🔢 Souhrn kód",
    "👨‍⚕️ Souhrn odbornost", "📊 Grafy", "⬇ Export"
])

# ────────────────────────────────────────────────────────────────────────────
# TAB: DATA
# ────────────────────────────────────────────────────────────────────────────
with t_data:
    with st.expander("🔍 Filtrovat v načtených datech"):
        c = st.columns(6)
        pf_rok = c[0].text_input("Rok",       key="pf_rok", placeholder="vše")
        pf_ico = c[1].text_input("IČO/IČZ",   key="pf_ico", placeholder="vše")
        pf_kod = c[2].text_input("Kód výkonu",key="pf_kod", placeholder="vše")
        pf_odb = c[3].text_input("Odbornost", key="pf_odb", placeholder="vše")
        pf_min = c[4].number_input("Min",     key="pf_min", value=None, placeholder="vše", min_value=0)
        pf_max = c[5].number_input("Max",     key="pf_max", value=None, placeholder="vše", min_value=0)

    dff = df.copy()
    if pf_rok and "rok" in dff.columns:
        dff = dff[dff["rok"].astype(str) == pf_rok]
    if pf_ico and id_col:
        vals = {v.strip() for v in pf_ico.replace(";",",").split(",") if v.strip()}
        dff = dff[dff[id_col].isin(vals)]
    if pf_kod and "kod" in dff.columns:
        dff = dff[dff["kod"] == pf_kod]
    if pf_odb and odb_col:
        dff = dff[dff[odb_col] == pf_odb]
    if pf_min is not None and nc:
        dff = dff[dff[nc] >= pf_min]
    if pf_max is not None and nc:
        dff = dff[dff[nc] <= pf_max]

    st.caption(f"Zobrazeno **{fmt(len(dff))}** řádků")
    st.dataframe(dff, use_container_width=True, height=520)

# ────────────────────────────────────────────────────────────────────────────
# TAB: SOUHRN IČO
# ────────────────────────────────────────────────────────────────────────────
with t_ico:
    if id_col:
        agg = {id_col: "first"}
        agg["Počet řádků"] = (id_col, "count")
        if nc:           agg[f"Σ {nc}"]     = (nc,    "sum")
        if "kod" in df.columns: agg["Unik. kódů"] = ("kod", "nunique")
        grp = df.groupby(id_col).agg(**{k:v for k,v in agg.items() if k!=id_col}).reset_index()
        if nc: grp = grp.sort_values(f"Σ {nc}", ascending=False)
        st.dataframe(grp, use_container_width=True, height=600)
    else:
        st.info("Soubor neobsahuje IČO/IČZ.")

# ────────────────────────────────────────────────────────────────────────────
# TAB: SOUHRN KÓD
# ────────────────────────────────────────────────────────────────────────────
with t_kod:
    if "kod" in df.columns:
        agg_k = {"Počet řádků": ("kod","count")}
        if nc:      agg_k[f"Σ {nc}"]  = (nc,"sum")
        if id_col:  agg_k["Unik. IČO"] = (id_col,"nunique")
        grp_k = df.groupby("kod").agg(**agg_k).reset_index()
        def lv(k):
            k = str(k).strip()
            return VYKONY.get(k) or VYKONY.get(k.lstrip("0")) or "—"
        grp_k.insert(1, "Název výkonu", grp_k["kod"].apply(lv))
        if nc: grp_k = grp_k.sort_values(f"Σ {nc}", ascending=False)
        st.dataframe(grp_k, use_container_width=True, height=600)
    else:
        st.info("Soubor neobsahuje sloupec 'kod'.")

# ────────────────────────────────────────────────────────────────────────────
# TAB: SOUHRN ODBORNOST
# ────────────────────────────────────────────────────────────────────────────
with t_odb:
    if odb_col:
        agg_o = {"Počet řádků": (odb_col,"count")}
        if nc:           agg_o[f"Σ {nc}"]    = (nc,"sum")
        if "kod" in df.columns: agg_o["Unik. kódů"] = ("kod","nunique")
        grp_o = df.groupby(odb_col).agg(**agg_o).reset_index()
        grp_o.insert(1, "Název odbornosti", grp_o[odb_col].map(ODBORNOSTI).fillna("—"))
        if nc: grp_o = grp_o.sort_values(f"Σ {nc}", ascending=False)
        st.dataframe(grp_o, use_container_width=True, height=600)
    else:
        st.info("Soubor neobsahuje sloupec odbornost.")

# ────────────────────────────────────────────────────────────────────────────
# TAB: GRAFY
# ────────────────────────────────────────────────────────────────────────────
with t_graf:
    if not nc:
        st.info("Pro grafy je potřeba numerický sloupec.")
    else:
        col_a, col_b = st.columns(2)

        with col_a:
            if "kod" in df.columns:
                st.subheader("Top 20 kódů výkonů")
                top = df.groupby("kod")[nc].sum().nlargest(20).reset_index()
                top["Název"] = top["kod"].apply(lambda k: VYKONY.get(k) or VYKONY.get(k.lstrip("0")) or k)
                top["Popisek"] = top["Název"] + "  (" + top["kod"] + ")"
                fig = px.bar(top, x=nc, y="Popisek", orientation="h",
                             color_discrete_sequence=["#1a1916"], height=520)
                fig.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=0,r=0,t=10,b=0))
                st.plotly_chart(fig, use_container_width=True)

        with col_b:
            if odb_col:
                st.subheader("Top 15 odborností")
                top_o = df.groupby(odb_col)[nc].sum().nlargest(15).reset_index()
                top_o["Název"] = top_o[odb_col].map(ODBORNOSTI).fillna(top_o[odb_col])
                top_o["Popisek"] = top_o["Název"] + "  (" + top_o[odb_col] + ")"
                fig2 = px.bar(top_o, x=nc, y="Popisek", orientation="h",
                              color_discrete_sequence=["#1d7a4a"], height=520)
                fig2.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=0,r=0,t=10,b=0))
                st.plotly_chart(fig2, use_container_width=True)

        if "rok" in df.columns:
            st.subheader("Vývoj v čase")
            df["_rok"] = pd.to_numeric(df["rok"], errors="coerce")
            trend = df.groupby("_rok")[nc].sum().reset_index()
            trend.columns = ["rok", nc]
            fig3 = px.line(trend, x="rok", y=nc, markers=True,
                           color_discrete_sequence=["#1a1916"])
            fig3.update_layout(height=320, margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig3, use_container_width=True)

# ────────────────────────────────────────────────────────────────────────────
# TAB: EXPORT
# ────────────────────────────────────────────────────────────────────────────
with t_exp:
    st.subheader("Export do Excelu")
    st.caption("Exportuje aktuální data včetně popisných sloupců.")

    which = st.radio("Co exportovat", ["Všechna načtená data", "Pouze filtrovaná data (z záložky Data)"], horizontal=True)

    if st.button("⬇ Generovat Excel", type="primary"):
        export_df = dff if which.startswith("Pouze") else df

        with st.spinner(f"Generuji Excel — {fmt(len(export_df))} řádků…"):
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                export_df.to_excel(writer, index=False, sheet_name="Data")

                # Souhrn kód
                if "kod" in df.columns:
                    sk = export_df.groupby("kod").agg(
                        Nazev=("kod", lambda x: VYKONY.get(x.iloc[0], "—")),
                        Pocet_radku=("kod","count"),
                        **({f"Suma_{nc}": (nc,"sum")} if nc else {})
                    ).reset_index()
                    sk.to_excel(writer, index=False, sheet_name="Souhrn_Kod")

                # Souhrn IČO
                if id_col:
                    si = export_df.groupby(id_col).agg(
                        Pocet_radku=(id_col,"count"),
                        **({f"Suma_{nc}": (nc,"sum")} if nc else {}),
                        **( {"Unik_kody": ("kod","nunique")} if "kod" in export_df.columns else {})
                    ).reset_index()
                    si.to_excel(writer, index=False, sheet_name="Souhrn_ICO")

        fname = f"mzcr_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx"
        st.download_button(
            label=f"📥 Stáhnout {fname}",
            data=buf.getvalue(),
            file_name=fname,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
