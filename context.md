# FrostAlert-TR — Project Context for Claude Code
*Last updated: May 27, 2026*

---

## 1. What This Project Is

**FrostAlert-TR** is a Streamlit-based interactive dashboard that translates province-level frost
forecasts into agricultural price risk signals for Turkey's 81 provinces.

- **Course:** CSSM 550 – Digital Solutions for SDGs (Koç University, CSS Master's program)
- **Deadline:** June 11, 2026
- **SDG alignment:** SDG 2 (Zero Hunger), SDG 13 (Climate Action)
- **Framing:** Stage 1 of a longer thesis arc on spring frost risk and Turkish agricultural price dynamics
- **Target users:** TARSİM (Turkey's agricultural insurance pool), agricultural extension services, policymakers

The dashboard is explicitly a **prototype**, not a production system. Scope is intentionally
limited given concurrent coursework and timeline.

---

## 2. Empirical Foundation

The dashboard is built on top of a completed empirical analysis from CSSM 502 (Advanced
Data Analysis). **No new ML model is trained.** The dashboard operationalizes existing results.

### Key methodological decisions (already finalized):
- Frost threshold: **-2.0°C** (biological fallback, data-driven via GBR PDP)
- Shock variable: binary dummy, min_temp < -2.0°C
- Model: **Two-Way Fixed Effects** with clustered standard errors (city level)
- Controls: `Production_Quantity`, `wind_speed`, `precipitation`, `humidity`
- Fixed effects: `C(City)`, `C(Year)`, `C(Month)` — month FE added for seasonality control
- Lag structure: Lag0 through Lag3; **Lag1 used as Sj** (sensitivity) in risk score
- Clustering analysis: attempted but dropped (stone fruit zero vectors corrupted results;
  whisker plot conveys same information more cleanly)

---

## 3. Data Assets

### 3.1 Main Dataset
- **File:** `thesis_dataset_deflated_final.csv`
- **Path (in repo):** `data/thesis_dataset_deflated_final.csv` (76 MB, committed to GitHub)
- **Size:** ~76 MB, 357,901 rows
- **Coverage:** January 2014 – December 2024, 81 provinces, 162 products
- **Key columns:**
  - `Product_Name` — TÜİK product code + Turkish name, e.g. `01.13.34.00.01. (Domates (Sofralık)) - Kilogram`
  - `City` — Province name in Turkish (Title Case), e.g. `Ankara`, `İzmir`
  - `Year`, `Month` — integer
  - `date` — datetime, first of month (e.g. `2022-01-01`)
  - `Real_Price` — CPI-deflated farm-gate price (base: January 2024), TL/kg
  - `Production_Quantity` — annual production quantity (tons), merged from TÜİK; same value
    repeated for all months of that year (expected, result of annual→monthly merge)
  - `min_temp` — monthly minimum temperature (°C), from ERA5-Land via Open-Meteo
  - `precipitation`, `humidity`, `wind_speed` — meteorological controls

### 3.2 Additional Data Files

**`data/city_coordinates.csv`** (in repo)
- 81 provinces with `City`, `Latitude`, `Longitude`
- All city names verified to match main dataset exactly (zero mismatches)

**`data/turkey_provinces.geojson`** — bundled inside the project
- Loaded from `Path(__file__).parent / "data" / "turkey_provinces.geojson"`
- Falls back to downloading from GitHub (cihadturhan/tr-geojson) if not present
- Province names normalized via `GEOJSON_TO_CITY` dict in config.py

**`data/whisker_data.csv`** — bundled inside the project
- Columns: `Product`, `Lag`, `Coef`, `Error_Min`, `Error_Max`
- Used by `build_whisker_plot()` in Page 2 (Product Detail)
- Source: product-specific FE regression output (CSSM 502, May 2026)

**`data/global_ref_max.json`** and **`data/ref_max_{product}.json`**
- Runtime-generated cache files for color scale anchoring
- **Excluded from git** (`.gitignore`). Recomputed automatically on first run.

### 3.3 Image Assets

**`images/frost_image.png`** — 1.7 MB original — **excluded from git** (`.gitignore`)
**`images/frost_image_small.jpg`** — 194 KB resized version (1400px wide, RGB, quality=75)
- Used on landing page (`app.py`) as right-side background
- Loaded via `load_frost_image()` with `@st.cache_data`

**`images/vegetables.png`** — hero background on Methodology page (base64, cached)

### 3.4 Deprecated / Do Not Use

**`risk_score_historical.csv`** — previously computed risk scores
- **Do not use as static input.** Sj values computed from an earlier (incorrect) sensitivity table.
- Risk scores must be recomputed at runtime from the main dataset using the corrected
  SENSITIVITY_TABLE in config.py.

---

## 4. Product Basket (Final)

17 products in dashboard. Selected via data-driven scan of 80 products (Lag1, -2°C threshold,
seasonality-controlled FE). Selection criterion: positive and statistically significant Lag1
coefficient OR theoretical phenological category membership.

### Sensitivity table (Sj = Lag1 coefficient × 100, percent price impact):

Source: product-specific FE regression output (`df_coef` table, verified May 2026).

| Turkish key | Display name | Sj (%) | Flag | Category |
|-------------|-------------|--------|------|----------|
| Domates  | Tomato      | 15.79 | — | Vegetables |
| Biber    | Pepper      | 10.61 | — | Vegetables |
| Patlıcan | Eggplant    | 16.93 | — | Vegetables |
| Hıyar    | Cucumber    | 14.18 | — | Vegetables |
| Ispanak  | Spinach     |  5.06 | — | Vegetables |
| Roka     | Arugula     |  9.64 | — | Vegetables |
| Turp     | Radish      |  2.58 | — | Vegetables |
| Mandalina| Mandarin    |  2.52 | — | Citrus |
| Nar      | Pomegranate |  6.08 | — | Citrus |
| Portakal | Orange      |  0.0  | insufficient_signal (Lag1 negative) | Citrus |
| Elma     | Apple       |  0.0  | insufficient_signal (Lag1 negative) | Pome |
| Kiraz    | Cherry      |  0.0  | zero_response (dormancy) | Stone fruit |
| Vişne    | Sour Cherry |  0.0  | zero_response (dormancy) | Stone fruit |
| Kayısı   | Apricot     |  0.0  | zero_response (dormancy) | Stone fruit |
| Şeftali  | Peach       |  0.0  | zero_response (dormancy) | Stone fruit |
| Erik     | Plum        |  0.0  | zero_response (dormancy) | Stone fruit |
| Çilek    | Strawberry  |  0.0  | zero_response (dormancy) | Stone fruit |

**Why flagged products are kept in the dashboard:**
- Stone fruits: winter window Lag1 = 0 due to biological dormancy. Dashboard shows
  "Risk window for this crop is April–May" warning with yellow border.
- Elma, Portakal: Lag1 negative — likely inventory buffering / harvest-season interaction.
  Floor at zero, show "insufficient frost signal" flag with blue border.

---

## 5. Risk Score Formula

```
Risk_ij = E_i × S_j × P_ij × 100
```

All three components normalized to [0, 1] before multiplication; final score scaled to [0, 100].

### E_i — Frost Exposure (province level)
- **Historical mode:** fraction of winter months (Nov–Mar) with min_temp < -2.0°C,
  configurable season (12 season options, 2014–2025 partial)
- **Live forecast mode:** Open-Meteo 16-day forecast, fraction of days < -2.0°C
- **Simulation mode:** uniform frost_days/16 for all provinces (demo)
- Normalization: min-max across all 81 provinces
- `HISTORICAL_YEARS = [2022, 2023, 2024]` — used for production norms only
- `EXPOSURE_YEARS_FULL = list(range(2014, 2025))` — used for full historical exposure

### S_j — Sensitivity (crop level)
- Source: Lag1 coefficient × 100 from product-specific FE scan
- Negative values → floor at zero, flag = `insufficient_signal`
- Zero dormancy response → flag = `zero_response`
- Normalization: min-max across non-flagged products only; flagged → S_norm = 0.0

### P_ij — Production Share (province × crop)
- Source: `Production_Quantity` from main dataset, 2022–2024 average
- **Hybrid normalization** (two-stage):
  1. `national_share`: product's total production / all basket products' total nationally
  2. `city_share_within`: city's share of that product's national production
  3. `P_combined = national_share × city_share_within`
  4. Min-max normalize P_combined globally → P_norm
- Rationale: pure global normalization caused Domates to dominate; pure within-product
  normalization inflated Roka. Hybrid balances both.
- NA values (city doesn't produce that crop) → P_norm = 0 → risk_score = 0

### Color scale anchoring:
- **All products mode:** `global_reference_max` — max risk score across all 12 seasons × 17 products
- **Single product mode:** `product_reference_max` — max risk score for that product across all 12 seasons
- Both computed at startup and cached to `data/global_ref_max.json` / `data/ref_max_{product}.json`

---

## 6. Historical Season Coverage

12 seasons available in the "Historical exposure" dropdown:

```
"2014–2024 average"  → full 2014–2024 winter months (EXPOSURE_YEARS_FULL)
"2014–2015"          → [(2014,11),(2014,12),(2015,1),(2015,2),(2015,3)]
...
"2023–2024"          → [(2023,11),(2023,12),(2024,1),(2024,2),(2024,3)]
"2024–2025 (partial)"→ [(2024,11),(2024,12)]
```

Defined in `_SEASON_FILTERS` dict in `utils/risk_score.py`.

---

## 7. Weather API

**Open-Meteo** — no API key required, free, ERA5-Land based.

```python
url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": lat,
    "longitude": lon,
    "daily": "temperature_2m_min",
    "forecast_days": 16,
    "timezone": "Europe/Istanbul"
}
```

Live forecast for all 81 provinces fetched on demand and cached with `@st.cache_data(ttl=21600)` (6h).

---

## 8. Dashboard Structure (3 pages + landing)

### app.py — Landing Page
- Full-viewport dark layout (`#000` background)
- Right-side frost image (`images/frost_image_small.jpg`, base64-encoded, cached)
- Left panel: title "FROST ALERT / TR" rendered as `<div>` (not `<h1>`) to avoid styles.py override
- Policy context box (2025 crisis: 65 provinces, TL 46.5B disbursements)
- Timeline metrics row: 81 provinces · 17 crops · 16d forecast · E×S×P
- Global CSS injected via `from utils.styles import inject_global_css`
- Additional landing-page-specific CSS: zero padding, hidden decoration bar

### Page 1 — 1_Risk_Map.py
- Two-line div heading: "FROST RISK" (white) / "MAP" (ice-blue `#7ec8e3`)
- Product selector (top + bottom, bidirectionally synced via session state)
- Exposure mode radio: Live forecast / Historical (12 seasons) / Simulate
- Choropleth map: `px.choropleth_mapbox` with `carto-darkmatter` tile
  - "All products": max risk score per province, `global_reference_max` color scale
  - Single product: grey for no-production provinces, colored for producers
  - Gold highlight border (`#FFD700`, width=3) for selected province
  - Map click → updates `selected_city_key` session state → `st.rerun()`
- Top-10 table: custom HTML builder with `_risk_color()` heatmap on risk score cells
  (dark yellow → deep red interpolation based on score/max_score)
  - All products columns: #, City, Max Risk Score, Top Crop
  - Single product columns: #, City, Risk Score, Exposure, Prod. Share
  - Header colors: gold for label columns, red (`#ff6b6b`) for risk score column
- Province detail panel (metrics: E, S, P breakdown)
- Province lookup selectbox synced via `selected_city_key` session state
- Time series section: dual-axis price + temperature history (2014–2024)
  - `_active_city` fallback prevents "None" in caption/banner
  - `_active_product_key` reverse-lookup converts display name → Turkish key before passing to `build_time_series_plot`

### Page 2 — 2_Product_Detail.py
- Two-line div heading: "PRODUCT" (white) / "DETAIL" (ice-blue)
- Section headings via inline `h3` with `color:#ffd944` (gold)
- Section 1: dynamic Plotly whisker plot from `data/whisker_data.csv`
  - Lag1 (red circles) + Lag2 (blue squares) with confidence intervals
  - Category background bands: Vegetables, Citrus, Pome, Stone fruit
- Section 2: historical event study from 12 curated events (hardcoded `CURATED_EVENTS` list)
  - Product names translated to English via `_translate_event_label()` in selectbox
  - Original Turkish label used for data lookup; reverse index used to find event dict
  - `build_event_study_plot()` from `utils/event_study.py`
  - Shows worst frost month, ±3 month price window, dual-axis Plotly chart

### Page 3 — 3_Methodology.py
- Fully rewritten in HTML using `st.markdown(unsafe_allow_html=True)` and `streamlit.components.v1`
- MathJax via CDN (`components.html`) for formula rendering
- Dark theme: black background, `#7ec8e3` blue, `#ffd944` gold accents
- Hero section with `images/vegetables.png` as background (base64, `@st.cache_data`)
- Sensitivity table dynamically built from `SENSITIVITY_TABLE` with pastel category row backgrounds
- No `st.header`, `st.dataframe`, `st.latex` anywhere on this page

---

## 9. File Structure (current)

```
frostalert_tr/
├── app.py                          # Landing page + global CSS entry point
├── config.py                       # All constants and sensitivity table
├── context.md                      # This file
├── requirements.txt                # streamlit>=1.45.0, pandas, plotly, requests, numpy
├── .gitignore                      # excludes __pycache__, .DS_Store, cached JSON, frost_image.png
├── data/
│   ├── city_coordinates.csv        # 81 provinces with lat/lon (in git)
│   ├── thesis_dataset_deflated_final.csv  # 76 MB main dataset (in git)
│   ├── turkey_provinces.geojson    # GeoJSON for choropleth (in git)
│   ├── whisker_data.csv            # FE regression whisker data (in git)
│   ├── global_ref_max.json         # runtime cache — NOT in git
│   └── ref_max_{product}.json      # runtime cache — NOT in git
├── images/
│   ├── frost_image.png             # 1.7 MB original — NOT in git
│   ├── frost_image_small.jpg       # 194 KB web version (in git)
│   └── vegetables.png              # Methodology page hero (in git)
├── pages/
│   ├── 1_Risk_Map.py
│   ├── 2_Product_Detail.py
│   └── 3_Methodology.py
└── utils/
    ├── __init__.py
    ├── event_study.py              # find_worst_frost_event + build_event_study_plot
    ├── forecast.py                 # fetch_all_forecasts + compute_simulated_exposure
    ├── risk_score.py               # compute_historical_exposure, compute_production_norms,
    │                               # compute_risk_scores, compute_product_reference_max
    ├── styles.py                   # inject_global_css() — shared dark theme CSS
    └── time_series.py              # build_time_series_plot
```

### config.py paths (relative, works locally and on Streamlit Cloud):
```python
_BASE = Path(__file__).parent
MAIN_DATA_PATH = str(_BASE / "data" / "thesis_dataset_deflated_final.csv")
COORDS_PATH    = str(_BASE / "data" / "city_coordinates.csv")
GEOJSON_PATH   = _BASE / "data" / "turkey_provinces.geojson"
```

---

## 10. Key Config Parameters

```python
FROST_THRESHOLD     = -2.0
FORECAST_DAYS       = 16
HISTORICAL_YEARS    = [2022, 2023, 2024]        # production norms only
EXPOSURE_YEARS_FULL = list(range(2014, 2025))   # full historical exposure
WINTER_MONTHS       = [11, 12, 1, 2, 3]
MAP_CENTER          = {"lat": 39.0, "lon": 35.5}
MAP_ZOOM            = 5.0
MAP_STYLE           = "carto-darkmatter"
COLOR_SCALE         = "YlOrRd"
```

---

## 11. Session State Keys (Page 1)

```python
st.session_state["selected_product_key"]  # English display name OR "All products (max risk)"
st.session_state["selected_city_key"]     # Turkish city name OR None (until user selects)
st.session_state["_product_top"]          # widget key — English display name
st.session_state["_product_bottom"]       # widget key — English display name
st.session_state["_city_select"]          # widget key — Turkish city name
```

**Important:** `selected_product_key` stores the **English display name** (e.g. `"Tomato"`),
NOT the Turkish internal key. Both `_product_top` and `_product_bottom` do the same.
The Turkish key is resolved at use-time via `_REVERSE_MAP = {v: k for k, v in PRODUCT_DISPLAY_NAMES.items()}`.

`_product_top` and `_product_bottom` are initialized on first load to `selected_product_key`
before the selectbox widgets are rendered (prevents `KeyError` on first rerun).

Both callbacks (`_on_product_change_top`, `_on_product_change_bottom`) sync the other
widget key to keep the two selectors in lockstep.

Map click handler reads `map_selection.selection.points[0].get("location")` and updates
both `selected_city_key` and `_city_select`, then calls `st.rerun()`.

`selected_city_key = None` on initial load — no city is auto-highlighted. All city-dependent
code uses `_active_city = st.session_state.get("selected_city_key") or selected_city` as
a safe fallback to the selectbox return value.

---

## 12. Styling Architecture

All pages call `inject_global_css()` from `utils/styles.py` immediately after `st.set_page_config()`.
`app.py` also calls it but adds a small additional block for landing-page-specific layout
(zero padding, hidden decoration bar, `#000` background overrides).

### Color palette:
| Token | Value | Usage |
|-------|-------|-------|
| Main bg | `#0a0a0a` | Page background |
| Card bg | `#111111` | Plot bg, sidebar |
| Border | `#2a2a2a` | Dividers, widget borders |
| Ice blue | `#7ec8e3` | Accent headings, temp line |
| Muted blue | `#8ab4cc` | Axis labels, captions |
| Body text | `#e8f4f8` | General text |
| Gold | `#ffd944` | Section headings, warnings |
| Red | `#ff6b6b` | Frost events, price spikes |
| Purple | `#a78bfa` | Frost threshold line |

### Page headings:
- All page titles are `<div>` elements (not `<h1>`) to avoid the `h1 { color:#7ec8e3 !important }` rule in styles.py overriding white title text.
- Two-line pattern: first span white (`#ffffff`), second span ice-blue (`#7ec8e3`).
- Section headings use `st.markdown("<h3 style='color:#ffd944;...'>")` inline overrides.

### Plotly charts:
All charts use `template="plotly_dark"` with:
- `paper_bgcolor="#0a0a0a"`, `plot_bgcolor="#111111"`
- `dragmode=False`, `fixedrange=True` on all axes
- `title_font=dict(color="#8ab4cc")`, `font=dict(color="#e8f4f8")`
- Empty-figure fallback branches also apply dark theme (prevents white flash)

---

## 13. What Has Been Completed

- [x] All three dashboard pages fully implemented and running
- [x] Landing page (app.py) with hero layout, frost image, timeline metrics
- [x] Risk score formula (E × S × P × 100) with hybrid P normalization
- [x] 12-season historical exposure coverage (2014–2024 average + 11 individual seasons)
- [x] Live 16-day Open-Meteo forecast mode
- [x] Simulation mode (uniform frost shock demo)
- [x] Per-product and global color scale anchoring across all seasons
- [x] Map click → province selection with gold highlight border
- [x] Synchronized product selector (top + bottom of Risk Map page, bidirectional)
- [x] Province lookup with session state persistence
- [x] Full 2014–2024 dual-axis time series (price + temperature)
- [x] Event study: 12 curated historical events, dual-axis Plotly
- [x] Whisker plot: dynamic from whisker_data.csv with CI error bars
- [x] Methodology page: formula cards, sensitivity table, empirical model, limitations
- [x] Dark theme fully applied across all pages (plotly_dark, #0a0a0a palette, Inter font)
- [x] Frost image resized (1.7 MB → 194 KB) and cached
- [x] Methodology page fully rewritten in dark theme HTML with MathJax
- [x] vegetables.png integrated as hero background on Methodology page
- [x] File-based cache for global_ref_max and per-product ref_max (data/*.json)
- [x] English product display names in all UI elements (selectboxes, tables, captions, map titles)
- [x] `_risk_color()` heatmap in top-10 table (dark yellow → deep red gradient on risk score cells)
- [x] `PRODUCT_DISPLAY_NAMES` mapping in config.py (Turkish key → English display name)
- [x] None-bug fix: `_active_city` fallback prevents "None" in captions/banners on initial load
- [x] `_active_product_key` reverse lookup: English display name → Turkish key for data filtering
- [x] Deployed to GitHub: `https://github.com/saliha-nur-gokce/frostalert-tr`
- [x] Streamlit Cloud ready: relative paths in config.py, requirements.txt updated to streamlit>=1.45.0

---

## 14. Current Open Issues / Known Limitations

- **Spring frost extension** (April–May window for stone fruits) not implemented.
  Documented as future work in Methodology page limitations section.
- **2025 TÜİK data** not yet available. Historical analysis ends December 2024.
- **76 MB CSV in git**: above GitHub's recommended 50 MB but below 100 MB hard limit.
  Works on Streamlit Cloud. If repo grows, consider Git LFS.
- **Streamlit version:** `>=1.45.0` in requirements.txt.

---

## 15. Academic Context

**Literature gap argument:** Global early warning systems (FAO GIEWS, NASA Harvest,
AgMIP) are cereal-centric. Turkey's food inflation is driven by perishable fruits and
vegetables. GIEWS explicitly excludes Turkey from price monitoring. No existing tool connects
province-level frost forecasts to producer-price risk.

**Policy hook:** 2025 frost crisis — 65 provinces, 16 fruit product groups, TL 46.5 billion in
combined TARSİM + government disbursements. TARSİM relies on ex-post damage
assessment, not anticipatory price signals.

**Methodological contribution:** Adaptation of IPCC Exposure-Sensitivity framework to
agricultural price transmission channel — not previously implemented for Turkish markets.

**Thesis extension:** Spring frost analysis for stone fruits (April–May window), incorporating
2025 TÜİK data when published. Dashboard spring frost layer is a stretch goal for capstone;
full empirical treatment reserved for thesis.
