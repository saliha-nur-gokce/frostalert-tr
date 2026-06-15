# FrostAlert-TR

**A Province-Level Frost Risk Early Warning Dashboard for Turkish Agricultural Markets**

Live dashboard: [frostalert-tr-1.streamlit.app](https://frostalert-tr-1.streamlit.app)

Capstone project for CSSM 550 – Digital Solutions for SDGs  
Koç University, CSS Master's Program, 2026  
**SDG 2 (Zero Hunger) · SDG 13 (Climate Action)**

---

## What This Project Does

FrostAlert-TR translates province-level frost forecasts into agricultural price risk signals for Turkey's 81 provinces. It answers a simple question: if a frost is coming in the next 16 days, which province, which crop, and how much price pressure should we expect?

The dashboard operationalizes empirical results from a Two-Way Fixed Effects panel model (CSSM 502, Advanced Data Analysis) and adapts the IPCC Exposure-Sensitivity framework to the agricultural price transmission channel — an application not previously implemented for Turkey's non-cereal markets.

**Target users:** TARSİM (Turkey's agricultural insurance pool), agricultural extension services, policymakers tracking climate-driven inflationary risk.

---

## Theoretical Framework

### Why This Gap Exists

Turkey is structurally exposed to frost-driven food price volatility for three reasons: Mediterranean climate risk above the global average, agroclimatic heterogeneity across 81 provinces, and food items accounting for over 25% of the CPI basket. Yet no existing tool connects province-level frost forecasts to producer-price risk:

- **FAO GIEWS** and **NASA Harvest** operate through cereal-centric frameworks. Turkey is explicitly excluded from GIEWS price monitoring.
- **TARSİM** relies on ex-post damage assessment, not anticipatory price signals.
- The **World Bank CCDR (2024)** explicitly recommends scaling up early warning systems for Turkish agriculture — this project is a direct response to that recommendation.

### Literature Anchors

Two findings from the literature shaped the model design:

1. Climate-price transmission is threshold-driven, not linear — price volatility spikes sharply after biological stress points are exceeded (Arellano-González et al., 2023).
2. ~85% of post-shock price adjustments are driven by *expectations* of scarcity, not physical supply loss (Letta et al., 2022). Markets start pricing in the shock before the harvest is lost.

Product heterogeneity matters: continuously-harvested perishables (tomatoes, peppers, eggplant) have no inventory buffer, so frost translates directly to farm-gate price. Stone fruits with winter dormancy absorb frost with zero price response in the November–March window.

---

## Risk Score Formula

```
Risk_ij = E_i × S_j × P_ij × 100
```

All three components normalized to [0, 1] before multiplication.

| Component | Definition | Source |
|-----------|-----------|--------|
| **E_i** | Frost Exposure — fraction of forecast days below −2°C biological threshold, min-max normalized across 81 provinces | Open-Meteo API (live) or ERA5-Land (historical) |
| **S_j** | Price Sensitivity — Lag1 TWFE coefficient × 100, min-max normalized across non-flagged products | Product-specific FE regressions (CSSM 502) |
| **P_ij** | Production Share — province × crop production weight, hybrid normalized | TÜİK annual production data (2022–2024 average) |

**Multiplicative logic:** if any component equals zero (no local production, zero dormancy response, no frost exposure), the risk score collapses to zero. No false alarms.

### P Normalization — Design Decision

Global normalization caused Domates to dominate the entire matrix (Antalya's production volume is orders of magnitude larger than other province-product pairs). Within-product normalization overcorrected, inflating Roka because Eskişehir is its only major producer.

**Final approach — two-stage hybrid:**
1. `national_share` = product's total production / all basket products' total nationally
2. `city_share_within` = city's share of that product's national production
3. `P_combined` = national_share × city_share_within
4. Global min-max normalize P_combined → P_norm

This keeps Domates appropriately dominant while making other crops visible.

---

## Empirical Model

**Two-Way Fixed Effects** panel model with clustered standard errors (city level):

```
Δ log P_it = β₀ + Σ βₗ · Frost_{i,t-l} + γ X_it + α_i + δ_t + μ_m + ε_it
```

| Parameter | Value |
|-----------|-------|
| Panel | 81 provinces × 17 crops × 2014–2024 (monthly) |
| Dependent variable | CPI-deflated farm-gate price (log), base: Jan 2024 |
| Frost threshold | −2.0°C (data-driven via GBR Partial Dependence Plot) |
| Key coefficient | Lag1 frost days below −2°C |
| Fixed effects | Province (α), year (δ), month (μ) |
| Controls | precipitation, humidity |
| Excluded | max_temp (multicollinearity with min_temp) |
| Clustering | Standard errors clustered at city level |

Month FE (C(Month)) added for seasonality control — coefficients shrank moderately but direction and significance held, treated as a robustness finding.

### Product Basket Selection

~80 TÜİK products were scanned using the same threshold, lag structure, and seasonality controls. Selection criterion: significant positive Lag1 coefficient.

- **Removed:** Kabak, Armut, Üzüm (inconsistent or negative signal)
- **Added:** Roka, Turp, Nar (significant positive signal)
- **Final basket:** 17 products

### Sensitivity Table (Sj = Lag1 coefficient × 100)

| Product | Sj (%) | Flag | Category |
|---------|--------|------|----------|
| Patlıcan | 16.93 | — | Vegetables |
| Domates | 15.79 | — | Vegetables |
| Hıyar | 14.18 | — | Vegetables |
| Biber | 10.61 | — | Vegetables |
| Roka | 9.64 | — | Vegetables |
| Nar | 6.08 | — | Citrus/Other |
| Ispanak | 5.06 | — | Vegetables |
| Mandalina | 2.52 | — | Citrus |
| Turp | 2.58 | — | Vegetables |
| Portakal | 0.00 | ⚠ Insufficient signal | Citrus |
| Elma | 0.00 | ⚠ Insufficient signal | Pome |
| Kiraz | 0.00 | ⚠ Zero response (dormancy) | Stone fruit |
| Vişne | 0.00 | ⚠ Zero response (dormancy) | Stone fruit |
| Kayısı | 0.00 | ⚠ Zero response (dormancy) | Stone fruit |
| Şeftali | 0.00 | ⚠ Zero response (dormancy) | Stone fruit |
| Erik | 0.00 | ⚠ Zero response (dormancy) | Stone fruit |
| Çilek | 0.00 | ⚠ Zero response (dormancy) | Stone fruit |

Stone fruits return Sj = 0 in the winter panel due to biological dormancy (November–March). This is the correct biological inference, not a model failure. Their critical vulnerability window is April–May (spring frost); empirical coefficients for that window are reserved for the thesis phase.

---

## Dashboard Structure

| Page | Content |
|------|---------|
| `app.py` | Landing page — project overview, policy context, key metrics |
| `1_Risk_Map.py` | Choropleth risk map — 3 exposure modes, province/product selector, top-10 table, time series |
| `2_Product_Detail.py` | Whisker plot (TWFE coefficients), 12 curated historical frost event studies |
| `3_Methodology.py` | Full model specification, sensitivity table, data sources, limitations |

### Exposure Modes

- **Live forecast:** Open-Meteo 16-day daily min temperature, cached 6h
- **Historical:** 12 seasons (2014–2024 average + individual seasons), ERA5-Land via Open-Meteo
- **Simulate:** Uniform frost shock across all 81 provinces (E_norm = frost_days / 16)

---

## Repository Structure

```
frostalert_tr/
├── app.py                          # Landing page
├── config.py                       # Constants, SENSITIVITY_TABLE, PRODUCT_DISPLAY_NAMES
├── requirements.txt
├── data/
│   ├── thesis_dataset_deflated_final.csv   # 76 MB main dataset (in git)
│   ├── city_coordinates.csv                # 81 provinces with lat/lon
│   ├── turkey_provinces.geojson            # Choropleth boundaries
│   ├── whisker_data.csv                    # Precomputed TWFE coefficients
│   ├── global_ref_max.json                 # Runtime cache (gitignored)
│   └── ref_max_{product}.json             # Runtime cache (gitignored)
├── pages/
│   ├── 1_Risk_Map.py
│   ├── 2_Product_Detail.py
│   └── 3_Methodology.py
└── utils/
    ├── event_study.py      # Curated frost event study plots
    ├── forecast.py         # Open-Meteo API + simulated exposure
    ├── risk_score.py       # E×S×P computation, normalization, caching
    ├── styles.py           # Global dark theme CSS
    └── time_series.py      # Price + temperature history plots
```

---

## Data Sources

| Source | Content |
|--------|---------|
| TÜİK | Farm-gate prices (monthly, 162 products, 81 provinces, 2014–2024) |
| TÜİK | Annual production quantities by province and product |
| TÜİK CPI | Consumer price index for real price deflation (base: Jan 2024) |
| ERA5-Land via Open-Meteo | Monthly min temperature, historical reanalysis |
| Open-Meteo | 16-day daily min temperature forecast (no API key required) |

---

## Limitations

- **Monthly resolution:** TÜİK prices are monthly averages; within-month price dynamics after a frost event are undetectable.
- **2025 data unavailable:** TÜİK has not published 2025 farm-gate prices. Historical analysis ends December 2024.
- **Spring frost window:** Stone fruits are dormant November–March. April–May spring frost analysis requires separate empirical estimation (reserved for thesis).
- **Compound events:** Co-occurring shocks (e.g. frost + earthquake-related logistics disruption, February 2023) cannot be decomposed.
- **Uncertainty quantification:** No confidence intervals on Sj estimates; risk score is a point estimate. Probabilistic risk tiers are future work.
- **Spatial autocorrelation:** Province fixed effects absorb some but not all cross-province spillovers.
- **Prototype framing:** This is a capstone demonstration. TARSİM integration, real-time alerts, and multi-hazard stacking are future work.

---

## Key Findings

**Vegetable price sensitivity:** Continuously-harvested perishables (Biber, Patlıcan, Hıyar) show the strongest and most consistent Lag1 price response. No inventory buffer means frost translates directly to farm-gate price within one month.

**The Antalya Paradox:** Turkey's highest-production provinces (Antalya, Mersin, Adana) are climatically insulated from frost. High P, near-zero E — risk score collapses. Geographic concentration of production modulates shock transmission. This also explains why event studies cannot be constructed for the most economically significant city–product pairs.

**Stone fruit zero response:** Sj = 0 for all stone fruits in the winter panel. This is correct biological inference — dormant crops do not respond to frost. The model is working as intended.

---

## Thesis Extension (Next Steps)

- Spring frost layer: April–May window, 42 candidate crops identified (`df_spring_frost_candidates`)
- Uncertainty bands on Sj estimates
- Hal (wholesale market) prices as a higher-frequency complement to TÜİK farm-gate prices
- Spatial autocorrelation testing
- EN/TR language toggle
- Mobile responsiveness

---

## Academic Context

**Course:** CSSM 550 – Digital Solutions for SDGs, Koç University, CSS Master's Program, 2026

**Empirical foundation:** CSSM 502 (Advanced Data Analysis) — panel regression results operationalized into dashboard.

**Methodological contribution:** Adaptation of the IPCC Exposure-Sensitivity framework to the agricultural price transmission channel. Not previously implemented for Turkish non-cereal markets.

**Policy relevance:** Directly addresses the anticipatory gap in TARSİM's risk assessment and responds to the World Bank CCDR (2024) recommendation to scale up agricultural early warning systems in Turkey.
