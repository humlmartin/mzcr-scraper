import streamlit as st
import pandas as pd
import plotly.express as px
import io
import requests

st.set_page_config(
    page_title="MZCR Explorer",
    page_icon="🏥",
    layout="wide",
)

# ── ČÍSELNÍKY ─────────────────────────────────────────────────────────────────
KRAJE = {
    "CZ010":"Praha","CZ020":"Středočeský","CZ031":"Jihočeský","CZ032":"Plzeňský",
    "CZ041":"Karlovarský","CZ042":"Ústecký","CZ051":"Liberecký","CZ052":"Královéhradecký",
    "CZ053":"Pardubický","CZ063":"Kraj Vysočina","CZ064":"Jihomoravský",
    "CZ071":"Olomoucký","CZ072":"Zlínský","CZ080":"Moravskoslezský",
}
ODBORNOSTI = {
    "001":"Všeobecné lékařství","002":"Praktický lékař pro děti","003":"Zubní lékařství",
    "014":"Chirurgie","019":"Ortopedie","022":"Neurologie","023":"Psychiatrie",
    "025":"Dermatovenerologie","026":"Urologie","027":"Oftalmologie","028":"ORL",
    "101":"Vnitřní lékařství","102":"Kardiologie","103":"Pneumologie",
    "104":"Gastroenterologie","105":"Nefrologie","106":"Endokrinologie",
    "107":"Revmatologie","108":"Hematologie","109":"Onkologie",
    "201":"Gynekologie","204":"Urologie","207":"Dětské lékařství",
    "301":"Anesteziologie","305":"Radiologie","321":"Rehabilitace",
    "401":"Klinická biochemie","404":"Mikrobiologie","405":"Patologie",
    "501":"Záchranná služba",
}
VYKONY = {
    "901":"Návštěva registrujícího lékaře","902":"Preventivní prohlídka",
    "903":"Cílené vyšetření","904":"Konziliární vyšetření",
    "910":"EKG","912":"Spirometrie","913":"UZ vyšetření",
    "916":"Odběr krve","917":"Aplikace infúze","918":"Injekce i.m./s.c.",
    "921":"Biochemie","922":"Krevní obraz","925":"Moč - chemie + sediment",
    "930":"RTG","931":"CT","932":"MRI","933":"Endoskopie",
    "950":"Vakcinace","09511":"Biochemické vyšetření","09543":"Krevní obraz KO+diff",
}

# ── KATALOG ───────────────────────────────────────────────────────────────────
CATALOG = {
    "Výkony zdravotní péče": [
        {"name": "Výkony per organizace (IČO) — aktuální",   "url": "https://data.mzcr.cz/data/distribuce/367/Otevrena-data-NR-04-02-vykony-ico.csv",                             "code": "NR-04-02", "size": "326 MB"},
        {"name": "Výkony per organizace (IČO) — 2024",        "url": "https://data.mzcr.cz/data/distribuce/367/Otevrena-data-NR-04-02-Vykony-ICO-2024-01.csv",                    "code": "NR-04-02", "size": "300 MB"},
        {"name": "Výkony per pracoviště + odbornost + měsíc", "url": "https://data.mzcr.cz/data/distribuce/363/Otevrena-data-NR-04-24-vykony-rok-mesic-icz-odbornost.csv",        "code": "NR-04-24", "size": ""},
        {"name": "Výkony dle formy péče + odbornost",         "url": "https://data.mzcr.cz/data/distribuce/365/Otevrena-data-NR-04-25-vykony-forma-odbornost.csv",                "code": "NR-04-25", "size": ""},
        {"name": "Výkony per odbornost (celá ČR)",            "url": "https://data.mzcr.cz/data/distribuce/368/Otevrena-data-NR-04-06-vykony-odbornost.csv",                      "code": "NR-04-06", "size": ""},
        {"name": "Výkony plný detail (IČZ+odbornost+dg.)",   "url": "https://data.mzcr.cz/data/distribuce/376/Otevrena-data-NR-04-01-Vykony-2024-01.csv",                        "code": "NR-04-01", "size": "1.7 GB"},
        {"name": "Výkony dle věku a pohlaví",                 "url": "https://data.mzcr.cz/data/distribuce/370/Otevrena-data-NR-04-08-vykony-vek-pohlavi.csv",                    "code": "NR-04-08", "size": ""},
        {"name": "Výkony + tříznaková diagnóza (MKN)",        "url": "https://data.mzcr.cz/data/distribuce/374/Otevrena-data-NR-04-05-Triznakove-diagnozy-MKN-2024-01.csv",       "code": "NR-04-05", "size": ""},
        {"name": "Diagnóza per odbornost",                    "url": "https://data.mzcr.cz/data/distribuce/371/Otevrena-data-NR-04-09-diagnoza-odbornost.csv",                    "code": "NR-04-09", "size": ""},
    ],
    "Hospitalizace": [
        {"name": "Hospitalizace",                 "url": "https://data.mzcr.cz/data/distribuce/338/Otevrena-data-NR-04-18-hospitalizace.csv",           "code": "NR-04-18", "size": ""},
        {"name": "Hospitalizace + diagnózy",      "url": "https://data.mzcr.cz/data/distribuce/339/Otevrena-data-NR-04-19-hospitalizace-diagnoza.csv",   "code": "NR-04-19", "size": ""},
        {"name": "Hospitalizace + DRG skupiny",   "url": "https://data.mzcr.cz/data/distribuce/341/Otevrena-data-NR-04-21-hospitalizace-drg.csv",        "code": "NR-04-21", "size": ""},
    ],
    "Léčivé přípravky": [
        {"name": "Léčiva — agregát (ATC × rok)",      "url": "https://data.mzcr.cz/data/distribuce/330/Otevrena-data-NR-04-60-lecive-pripravky.csv",                     "code": "NR-04-60", "size": ""},
        {"name": "Léčiva — pracoviště + měsíc",       "url": "https://data.mzcr.cz/data/distribuce/328/Otevrena-data-NR-04-60-lecive-pripravky-sukl-mesic-icp.csv",      "code": "NR-04-60", "size": ""},
        {"name": "Léčiva — noví pacienti",            "url": "https://data.mzcr.cz/data/distribuce/396/Otevrena-data-NR-04-93-lecive-pripravky-novi-pacienti.csv",       "code": "NR-04-93", "size": ""},
    ],
    "Ostatní": [
        {"name": "Mortalita — zhoubné nádory",    "url": "https://data.mzcr.cz/data/distribuce/377/Otevrena-data-NR-07-02-mortalita-zhoubne-nadory-2024-01.csv",    "code": "NR-07-02", "size": ""},
        {"name": "Záchranná služba — výjezdy",    "url": "https://data.mzcr.cz/data/distribuce/314/Otevrena-data-NR-04-10-zachranna-sluzba.csv",                    "code": "NR-04-10", "size": ""},
        {"name": "Číselník IČZ → název, IČO",     "url": "https://data.mzcr.cz/data/distribuce/362/Otevrena-data-OIS-12-02-ciselnik-icz-pojistovny.csv",            "code": "OIS-12-02","size": ""},
    ],
}

# ── NAČÍTÁNÍ DAT ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data(url: str, filters: dict) -> pd.DataFrame:
    """Načte CSV po chuncích, filtruje za běhu — šetří RAM."""
    chunks = []
    chunk_size = 100_000

    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0))
        downloaded = 0
        raw = b""

        prog = st.progress(0, text="Stahuju data…")

        for chunk in r.iter_content(chunk_size=1024 * 512):  # 512 KB bloky
            raw += chunk
            downloaded += len(chunk)
            if total:
                pct = downloaded / total
                mb_done = downloaded / 1024 / 1024
                mb_total = total / 1024 / 1024
                prog.progress(pct, text=f"Načteno {mb_done:.1f} / {mb_total:.1f} MB ({pct*100:.0f}%)")

        prog.progress(1.0, text="Parsuju CSV…")

        import io as _io
        df_full = pd.read_csv(
            _io.BytesIO(raw),
            dtype=str,  # vše jako text — kódy neformátujeme
            encoding="utf-8-sig",
            low_memory=False,
        )

    prog.empty()

    # Aplikuj filtry
    df = df_full.copy()
    if filters.get("rok") and "rok" in df.columns:
        df = df[df["rok"].astype(str) == str(filters["rok"])]
    if filters.get("ico") and any(c in df.columns for c in ["ico","ICO","icz","ICZ"]):
        id_col = next(c for c in ["ico","ICO","icz","ICZ"] if c in df.columns)
        vals = [v.strip() for v in filters["ico"].replace(";",",").split(",") if v.strip()]
        df = df[df[id_col].isin(vals)]
    if filters.get("kod") and "kod" in df.columns:
        df = df[df["kod"] == str(filters["kod"])]
    if filters.get("odbornost"):
        for col in ["odbornost","odbornost_predepisujici"]:
            if col in df.columns:
                df = df[df[col] == str(filters["odbornost"])]
                break

    # Přidej popisné sloupce
    if "kod" in df.columns:
        df["vykon_nazev"] = df["kod"].map(VYKONY).fillna("")
    for col in ["odbornost","odbornost_predepisujici"]:
        if col in df.columns:
            df[col + "_nazev"] = df[col].map(ODBORNOSTI).fillna("")
    for col in ["kraj_kod","KRAJ_KOD"]:
        if col in df.columns:
            df[col + "_nazev"] = df[col].map(KRAJE).fillna("")

    # Numerické sloupce
    for num_col in ["suma_mnozstvi","pocet_kontaktu","pocet_pacientu","suma_uhrad","uhrada_ZP"]:
        if num_col in df.columns:
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce")

    return df


# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main .block-container { padding-top: 1.5rem; }
    div[data-testid="stMetric"] { background: #f8f7f4; border-radius: 8px; padding: 12px 16px; }
</style>
""", unsafe_allow_html=True)

st.title("🏥 MZCR Explorer")
st.caption("Otevřená data ÚZIS ČR · data.mzcr.cz")

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Datová sada")

    # Výběr skupiny
    group = st.selectbox("Skupina", list(CATALOG.keys()))
    items = CATALOG[group]
    item_names = [f"{i['name']} {'· '+i['size'] if i['size'] else ''}" for i in items]
    idx = st.selectbox("Soubor", range(len(items)), format_func=lambda i: item_names[i])
    selected = items[idx]

    st.caption(f"`{selected['code']}`")

    st.divider()
    st.header("Filtry před načtením")
    st.caption("Filtrují za běhu — šetří paměť")

    f_rok = st.text_input("Rok", placeholder="např. 2024")
    f_ico = st.text_input("IČO / IČZ", placeholder="46523782, 12345678")
    f_kod = st.text_input("Kód výkonu", placeholder="např. 910")
    f_odb = st.text_input("Odbornost", placeholder="např. 001")

    load_btn = st.button("▶ Načíst data", type="primary", use_container_width=True)

    st.divider()
    st.caption("nebo vlastní URL:")
    custom_url = st.text_input("URL souboru", placeholder="https://data.mzcr.cz/…")

# ── HLAVNÍ OBSAH ──────────────────────────────────────────────────────────────
if load_btn or ("df" in st.session_state and st.session_state.get("loaded_url") == (custom_url or selected["url"])):

    url = custom_url if custom_url else selected["url"]
    filters = {"rok": f_rok, "ico": f_ico, "kod": f_kod, "odbornost": f_odb}

    if load_btn:
        st.cache_data.clear()  # při novém načtení vždy čerstvá data
        with st.spinner(f"Načítám {url.split('/')[-1]}…"):
            try:
                df = load_data(url, filters)
                st.session_state["df"] = df
                st.session_state["loaded_url"] = url
            except Exception as e:
                st.error(f"Chyba: {e}")
                st.stop()
    else:
        df = st.session_state["df"]

    st.success(f"Načteno {len(df):,} řádků · {df.shape[1]} sloupců".replace(",", " "))

    # ── METRIKY ──────────────────────────────────────────────────────────────
    num_col = next((c for c in ["suma_mnozstvi","pocet_kontaktu","pocet_pacientu","suma_uhrad"] if c in df.columns), None)
    id_col  = next((c for c in ["ico","ICO","icz","ICZ"] if c in df.columns), None)
    odb_col = next((c for c in ["odbornost","odbornost_predepisujici"] if c in df.columns), None)

    cols_m = st.columns(5)
    cols_m[0].metric("Řádků", f"{len(df):,}".replace(",", " "))
    cols_m[1].metric("IČO/IČZ", f"{df[id_col].nunique():,}".replace(",", " ") if id_col else "—")
    cols_m[2].metric("Kódů výkonů", f"{df['kod'].nunique():,}".replace(",", " ") if "kod" in df.columns else "—")
    cols_m[3].metric("Odborností", f"{df[odb_col].nunique():,}".replace(",", " ") if odb_col else "—")
    cols_m[4].metric(f"Σ {num_col or '—'}", f"{df[num_col].sum():,.0f}".replace(",", " ") if num_col else "—")

    st.divider()

    # ── TABS ─────────────────────────────────────────────────────────────────
    tab_data, tab_ico, tab_kod, tab_odb, tab_graf = st.tabs([
        "📋 Data", "🏢 Souhrn IČO", "🔢 Souhrn kód", "👨‍⚕️ Souhrn odbornost", "📊 Grafy"
    ])

    # ── POST-LOAD FILTR ───────────────────────────────────────────────────────
    with tab_data:
        with st.expander("🔍 Filtrovat v načtených datech", expanded=False):
            fc = st.columns(6)
            pf_rok = fc[0].text_input("Rok", key="pf_rok", placeholder="vše")
            pf_ico = fc[1].text_input("IČO/IČZ", key="pf_ico", placeholder="vše")
            pf_kod = fc[2].text_input("Kód výkonu", key="pf_kod", placeholder="vše")
            pf_odb = fc[3].text_input("Odbornost", key="pf_odb", placeholder="vše")
            pf_min = fc[4].number_input("Min množství", key="pf_min", value=None, placeholder="vše")
            pf_max = fc[5].number_input("Max množství", key="pf_max", value=None, placeholder="vše")

        dff = df.copy()
        if pf_rok: dff = dff[dff.get("rok", pd.Series()).astype(str) == pf_rok]
        if pf_ico and id_col:
            vals = [v.strip() for v in pf_ico.replace(";",",").split(",") if v.strip()]
            dff = dff[dff[id_col].isin(vals)]
        if pf_kod and "kod" in dff.columns: dff = dff[dff["kod"] == pf_kod]
        if pf_odb and odb_col: dff = dff[dff[odb_col] == pf_odb]
        if pf_min is not None and num_col: dff = dff[dff[num_col] >= pf_min]
        if pf_max is not None and num_col: dff = dff[dff[num_col] <= pf_max]

        st.caption(f"{len(dff):,} řádků".replace(",", " "))
        st.dataframe(dff, use_container_width=True, height=500)

        # Export
        col_exp1, col_exp2 = st.columns([1, 4])
        with col_exp1:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                dff.to_excel(writer, index=False, sheet_name="Data")
            st.download_button(
                "⬇ Excel",
                data=buf.getvalue(),
                file_name=f"mzcr_export_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    # ── SOUHRN IČO ───────────────────────────────────────────────────────────
    with tab_ico:
        if id_col:
            agg = {id_col: "first", "count": (id_col, "count")}
            if num_col: agg[f"Σ {num_col}"] = (num_col, "sum")
            if "kod" in df.columns: agg["unik. kódů"] = ("kod", "nunique")
            grp = df.groupby(id_col).agg(**{k: v for k, v in agg.items() if k != id_col}).reset_index()
            if num_col: grp = grp.sort_values(f"Σ {num_col}", ascending=False)
            st.dataframe(grp, use_container_width=True, height=500)
        else:
            st.info("Soubor neobsahuje IČO/IČZ.")

    # ── SOUHRN KÓD ───────────────────────────────────────────────────────────
    with tab_kod:
        if "kod" in df.columns:
            agg_k = {"Počet řádků": ("kod", "count")}
            if num_col: agg_k[f"Σ {num_col}"] = (num_col, "sum")
            if id_col: agg_k["unik. IČO"] = (id_col, "nunique")
            grp_k = df.groupby("kod").agg(**agg_k).reset_index()
            grp_k["název výkonu"] = grp_k["kod"].map(VYKONY).fillna("")
            if num_col: grp_k = grp_k.sort_values(f"Σ {num_col}", ascending=False)
            st.dataframe(grp_k[["kod","název výkonu"] + [c for c in grp_k.columns if c not in ["kod","název výkonu"]]],
                         use_container_width=True, height=500)
        else:
            st.info("Soubor neobsahuje sloupec 'kod'.")

    # ── SOUHRN ODBORNOST ─────────────────────────────────────────────────────
    with tab_odb:
        if odb_col:
            agg_o = {"Počet řádků": (odb_col, "count")}
            if num_col: agg_o[f"Σ {num_col}"] = (num_col, "sum")
            if "kod" in df.columns: agg_o["unik. kódů"] = ("kod", "nunique")
            grp_o = df.groupby(odb_col).agg(**agg_o).reset_index()
            grp_o["název odbornosti"] = grp_o[odb_col].map(ODBORNOSTI).fillna("")
            if num_col: grp_o = grp_o.sort_values(f"Σ {num_col}", ascending=False)
            st.dataframe(grp_o[[odb_col,"název odbornosti"] + [c for c in grp_o.columns if c not in [odb_col,"název odbornosti"]]],
                         use_container_width=True, height=500)
        else:
            st.info("Soubor neobsahuje sloupec odbornost.")

    # ── GRAFY ────────────────────────────────────────────────────────────────
    with tab_graf:
        if not num_col:
            st.info("Pro grafy je potřeba numerický sloupec (suma_mnozstvi, pocet_kontaktu…).")
        else:
            g1, g2 = st.columns(2)

            with g1:
                st.subheader("Top 20 kódů výkonů")
                if "kod" in df.columns:
                    top_kod = df.groupby("kod")[num_col].sum().nlargest(20).reset_index()
                    top_kod["název"] = top_kod["kod"].map(VYKONY).fillna(top_kod["kod"])
                    fig = px.bar(top_kod, x=num_col, y="název", orientation="h",
                                 color_discrete_sequence=["#1a1916"])
                    fig.update_layout(yaxis=dict(autorange="reversed"), height=500,
                                      margin=dict(l=0,r=0,t=20,b=0))
                    st.plotly_chart(fig, use_container_width=True)

            with g2:
                st.subheader("Top 15 odborností")
                if odb_col:
                    top_odb = df.groupby(odb_col)[num_col].sum().nlargest(15).reset_index()
                    top_odb["název"] = top_odb[odb_col].map(ODBORNOSTI).fillna(top_odb[odb_col])
                    fig2 = px.bar(top_odb, x=num_col, y="název", orientation="h",
                                  color_discrete_sequence=["#1d7a4a"])
                    fig2.update_layout(yaxis=dict(autorange="reversed"), height=500,
                                       margin=dict(l=0,r=0,t=20,b=0))
                    st.plotly_chart(fig2, use_container_width=True)

            # Trend dle roku
            if "rok" in df.columns:
                st.subheader("Vývoj v čase")
                df["rok_n"] = pd.to_numeric(df["rok"], errors="coerce")
                trend = df.groupby("rok_n")[num_col].sum().reset_index()
                fig3 = px.line(trend, x="rok_n", y=num_col, markers=True,
                               color_discrete_sequence=["#1a1916"])
                fig3.update_layout(height=350, margin=dict(l=0,r=0,t=20,b=0))
                st.plotly_chart(fig3, use_container_width=True)

else:
    st.info("👈 Vlevo vyber datovou sadu a klikni **Načíst data**")
    st.markdown("""
    **Jak to funguje:**
    1. Vyber skupinu a soubor z katalogu vlevo
    2. Volitelně nastav filtry (rok, IČO, kód výkonu…)
    3. Klikni Načíst — data se stáhnou přímo z data.mzcr.cz
    4. Prohlíží, filtruj, exportuj do Excelu nebo koukej na grafy
    """)
