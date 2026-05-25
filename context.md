# FrostAlert-TR — Project Context for Claude Code
*Last updated: May 2026*

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
- **Path (local):** `/Users/salihanurgokce/Desktop/SCHOOL/CSS/CSSM502/project/finalData/thesis_dataset_deflated_final.csv`
- **Size:** ~80 MB, 357,901 rows
- **Coverage:** January 2014 – December 2024, 81 provinces, 162 products
- **Key columns:**
  - `Product_Name` — TÜİK product code + Turkish name, e.g. `01.13.34.00.01. (Domates (Sofralık)) - Kilogram`
  - `City` — Province name in Turkish (Title Case), e.g. `Ankara`, `İzmir`
  - `Year`, `Month` — integer
  - `date` — datetime, first of month (e.g. `2022-01-01`)
  - `Real_Price` — CPI-deflated farm-gate price (base: January 2024), TL/kg
  - `Production_Quantity` — annual production quantity (tons), merged from TÜİK; same value
    repeated for all months of that year (this is expected, result of annual→monthly merge)
  - `min_temp` — monthly minimum temperature (°C), from ERA5-Land via Open-Meteo
  - `precipitation`, `humidity`, `wind_speed` — meteorological controls
  - `days_below_0` through `days_below_-5` — count of days below each threshold per month
  - `false_spring_event` — binary dummy
  - `CPI_Index` — used for deflation
  - `Log_Price` — created in-session: `np.log(Real_Price)`

### 3.2 Additional Data Files

**`city_coordinates.csv`**
- Path: `/Users/salihanurgokce/Desktop/SCHOOL/CSS/CSSM502/project/finalData/city_coordinates.csv`
- 81 provinces with `City`, `Latitude`, `Longitude`
- All city names verified to match main dataset exactly (zero mismatches)

**`spring_frost_candidates.csv`** — 42 products with zero winter response
- These are candidates for spring frost extension (April–May window)
- If time permits before June 11: add spring frost analysis as optional dashboard layer
- If not: documented as future work in Methodology page

### 3.3 Static Figure Assets

**Whisker plot:**
- Path: `/Users/salihanurgokce/Desktop/SCHOOL/CSS/CSSM502/project/projectFinal/HeterogeneousImpactofFrostShocksonPrices.png`
- Used in: Page 2 (Product Detail), static display

**Event study (default figure):**
- Path: `/Users/salihanurgokce/Desktop/SCHOOL/CSS/CSSM502/project/graphs_agriculture/ag_event_study.png`
- Used in: Page 2 (Product Detail), shown before user selects a custom city-product combo
- Default combination: Konya + Biber, February 2023

### 3.4 Risk Score CSV (do NOT use directly)

**`risk_score_historical.csv`** — 1,377 city-product pairs, previously computed
- **Do not use as static input.** Sj values were computed from an earlier (incorrect) sensitivity
  table. Risk scores must be recomputed at runtime from the main dataset using the corrected
  SENSITIVITY_TABLE in config.py.
- File is kept for reference/debugging only.

---

## 4. Product Basket (Final)

17 products in dashboard. Selected via data-driven scan of 80 products (Lag1, -2°C threshold,
seasonality-controlled FE). Selection criterion: positive and statistically significant Lag1
coefficient OR theoretical phenological category membership.

### Sensitivity table (Sj = Lag1 coefficient × 100, percent price impact):

Source: product-specific FE regression output (`df_coef` table, verified May 2026).

| Product | Turkish name | Sj (%) | Flag | Category |
|---------|-------------|--------|------|----------|
| Domates | Tomato | 15.79 | — | Vegetables |
| Biber | Pepper | 10.61 | — | Vegetables |
| Patlıcan | Eggplant | 16.93 | — | Vegetables |
| Hıyar | Cucumber | 14.18 | — | Vegetables |
| Ispanak | Spinach | 5.06 | — | Vegetables |
| Roka | Arugula | 9.64 | — | Vegetables |
| Turp | Radish (combined Kırmızı+Bayır regression) | 2.58 | — | Vegetables |
| Mandalina | Mandarin | 2.52 | — | Citrus |
| Nar | Pomegranate | 6.08 | — | Citrus/Other |
| Portakal | Orange | 0.0 | ✓ insufficient_signal (Lag1 negative) | Citrus |
| Elma | Apple | 0.0 | ✓ insufficient_signal (Lag1 negative) | Pome |
| Kiraz | Cherry | 0.0 | ✓ zero response (dormancy) | Stone fruit |
| Vişne | Sour Cherry | 0.0 | ✓ zero response (dormancy) | Stone fruit |
| Kayısı | Apricot | 0.0 | ✓ zero response (dormancy) | Stone fruit |
| Şeftali | Peach | 0.0 | ✓ zero response (dormancy) | Stone fruit |
| Erik | Plum | 0.0 | ✓ zero response (dormancy) | Stone fruit |
| Çilek | Strawberry | 0.0 | ✓ zero response (dormancy) | Stone fruit |

**Why flagged products are kept in the dashboard:**
- Stone fruits: winter window Lag1 = 0 due to biological dormancy — this IS the robustness
  check argument. Dashboard shows "Risk window for this crop is April–May" warning.
- Elma: Lag1 negative across all varieties (Golden, Amasya, Starking, Granny Smith) —
  likely inventory buffering. Floor at zero, show "insufficient frost signal" flag.
- Portakal: Lag1 negative (-6.08%), likely harvest-period seasonality interaction.
  Floor at zero, show "insufficient frost signal" flag.

---

## 5. Risk Score Formula

```
Risk_ij = E_i × S_j × P_ij
```

All three components normalized to [0, 1] before multiplication, final score scaled to [0, 100].

### E_i — Frost Exposure (province level)
- **Historical version:** fraction of winter months (Nov–Mar) with min_temp < -2°C,
  computed over 2022–2024
- **Forecast version (dashboard):** number of days in 16-day Open-Meteo forecast window
  with min_temp < -2°C, normalized 0–1 (min=0, max=16)
- Normalization: min-max across all 81 provinces

### S_j — Sensitivity (crop level)
- Source: Lag1 coefficient from product-specific FE scan
- Negative values → floor at zero, set `insufficient_signal = True`
- Normalization: min-max across non-flagged products only
- Flagged products get Sj_norm = 0.0

### P_ij — Production Share (province × crop)
- Source: `Production_Quantity` from main dataset, 2022–2024 average
- **Hybrid normalization** (two-stage):
  1. `national_share`: product's total production as fraction of all basket products nationally
  2. `city_share_within`: city's share of that product's national production
  3. `P_combined = national_share × city_share_within`
  4. Min-max normalize P_combined globally → P_norm
- Rationale: global normalization made Domates dominate everything; within-product
  normalization made Roka #1 (distortion). Hybrid balances both.
- NA values (city doesn't produce that crop) → P_norm = 0 → risk_score = 0

### Known results:
- Top risk cities: Bitlis, Konya, Afyonkarahisar, Muş, Van
- Antalya: E=0 (no frost), risk=0 despite being #1 producer — correct
- Ardahan: E=1.0 (maximum frost) but P=0 for all basket products — correct (spatial mismatch)

---

## 6. Phenological Windows

| Category | Activation window | Dashboard behavior |
|----------|------------------|-------------------|
| Vegetables | November – March | Normal risk score shown |
| Citrus / Nar | November – March | Normal risk score shown |
| Pome (Elma) | November – March | Risk shown but "insufficient signal" flag |
| Stone fruits | November – March | Risk = 0, show warning: "Risk window is April–May" |

Spring frost analysis for stone fruits (April–May window) is a stretch goal — if time permits
before June 11, add as optional dashboard layer. If not, document as future work in Methodology
page. Dashboard structure is designed to accommodate this without restructuring.

---

## 7. Weather API

**Open-Meteo** — no API key required, free, ERA5-Land based.

```python
import requests

def fetch_forecast(lat, lon, city_name):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_min",
        "forecast_days": 16,
        "timezone": "Europe/Istanbul"
    }
    response = requests.get(url, params=params)
    data = response.json()
    # Returns: data['daily']['time'] (list of dates), data['daily']['temperature_2m_min'] (list of floats)
```

Tested and working. Returns 16 daily min_temp values.
For dashboard: fetch all 81 provinces on load (or cache), compute E_i dynamically.

---

## 8. Dashboard Structure (3 pages)

### Page 1 — Risk Map (Overview)
- Sidebar: product dropdown (17 products)
- Main: choropleth map of Turkey, 81 provinces colored by risk_score for selected product
- Clicking a province → sidebar shows E, S, P values + risk score breakdown
- Stone fruit selected → banner: "Risk window for this crop is April–May (spring frost)"
- Data source: Open-Meteo 16-day forecast → E computed live; S and P from precomputed tables

### Page 2 — Product Detail
- Top: whisker plot (static, all products, Lag1 + Lag2 with CI) — use saved PNG
- Bottom: dynamic event study
  - User selects province + product
  - Auto-detects most severe historical frost event for that combination
  - Shows ±3 month price window around event
  - Default: Konya + Biber, February 2023 (paper's Figure 3)

### Page 3 — Methodology & About
- Risk score formula with component explanation
- Backtesting note: correlation of historical risk scores vs observed Lag1 price changes
  (simple version: high-risk province-product pairs show statistically higher price increases)
- Data sources table
- Limitations: monthly resolution, 2025 TÜİK data not yet available, compound shocks
  cannot be decomposed, spring frost coefficients pending
- hal.gov.tr note: higher-frequency complement, not integrated due to price-level difference

---

## 9. Key Design Constraints

- **No new ML model.** Dashboard uses precomputed FE coefficients only.
- **No 2025 data.** TÜİK has not published 2025 farm-gate prices yet. Historical analysis
  ends December 2024.
- **Monthly resolution.** Cannot detect within-month price dynamics.
- **Prototype framing.** Not a production system. Methodological limitations documented.
- **English-only code.** All variable names, comments, and output messages in English.
- **Streamlit.** No other framework.

---

## 10. Files to Create / Expected File Structure

```
frostalert_tr/
├── app.py                  # Streamlit entry point, page routing
├── context.md              # This file
├── config.py               # Constants: THRESHOLD, BASKET, SENSITIVITY_TABLE, city coordinates
├── data/
│   └── (no large files — main CSV loaded from local path via config.py)
├── pages/
│   ├── 1_Risk_Map.py
│   ├── 2_Product_Detail.py
│   └── 3_Methodology.py
└── utils/
    ├── forecast.py         # Open-Meteo fetch + E computation
    ├── risk_score.py       # E × S × P computation (computed at runtime, cached)
    └── event_study.py      # Dynamic event study logic
```

### Local file paths (hardcoded in config.py):
```python
MAIN_DATA_PATH = "/Users/salihanurgokce/Desktop/SCHOOL/CSS/CSSM502/project/finalData/thesis_dataset_deflated_final.csv"
COORDS_PATH    = "/Users/salihanurgokce/Desktop/SCHOOL/CSS/CSSM502/project/finalData/city_coordinates.csv"
WHISKER_PATH   = "/Users/salihanurgokce/Desktop/SCHOOL/CSS/CSSM502/project/projectFinal/HeterogeneousImpactofFrostShocksonPrices.png"
EVENT_STUDY_PATH = "/Users/salihanurgokce/Desktop/SCHOOL/CSS/CSSM502/project/graphs_agriculture/ag_event_study.png"
```

### Performance note:
Main dataset is ~80MB. Use `@st.cache_data` on all data loading functions so the file is
read once per session, not on every page interaction.

---

## 11. What Still Needs to Be Done

**Core (must finish before June 11):**
1. ~~City coordinates CSV~~ — done, 81 provinces verified
2. Open-Meteo fetch for all 81 provinces — tested for Ankara, needs scaling + caching
3. Risk score recomputation at runtime (E × S × P) with corrected sensitivity table
4. Streamlit skeleton — page routing, sidebar, layout
5. Choropleth map — Folium or Plotly, Turkey GeoJSON
6. Dynamic event study — auto-detect worst frost event per city-product, plot window
7. Stone fruit warning banner + Portakal/Elma insufficient signal flag

**Stretch goals (if time permits):**
8. Backtesting — correlation of historical risk scores vs observed Lag1 price changes
9. Spring frost layer — April–May window for stone fruits
10. EN/TR language toggle — lowest priority, add last

**Not in scope:**
- Deployment to Streamlit Community Cloud (optional, not required for submission)
- hal.gov.tr integration (documented as future work)

---

## 12. Academic Context

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
