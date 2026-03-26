# MZCR Explorer

Streamlit aplikace pro prohlížení otevřených dat ÚZIS ČR z data.mzcr.cz.

## Nasazení na Railway

1. Nahraj tento repozitář na GitHub
2. Jdi na [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
3. Vyber repozitář → Railway automaticky detekuje `railway.toml` a nasadí aplikaci
4. Za 2–3 minuty běží na vygenerované URL

## Lokální spuštění

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Funkce

- Katalog 20+ datových sad NRHZS
- Streamované načítání velkých CSV (300 MB+) přímo z data.mzcr.cz
- Filtry před i po načtení
- Souhrny per IČO, kód výkonu, odbornost
- Grafy (top výkony, top odbornosti, trend v čase)
- Export do Excelu
