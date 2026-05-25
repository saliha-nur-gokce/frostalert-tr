import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import FROST_THRESHOLD, SENSITIVITY_TABLE

st.set_page_config(page_title="Methodology — FrostAlert-TR", layout="wide")

st.title("Methodology & About")

# ---------------------------------------------------------------------------
# Risk score formula
# ---------------------------------------------------------------------------

st.header("Risk Score Formula")
st.latex(r"\text{Risk}_{ij} = E_i \times S_j \times P_{ij} \times 100")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("E — Frost Exposure")
    st.markdown(f"""
Province-level metric derived from the **Open-Meteo 16-day forecast**.

$$E_i = \\frac{{\\text{{days with min\\_temp}} < {FROST_THRESHOLD}°C}}{{16}}$$

Normalized min-max across all 81 provinces before multiplication.
Range: 0 (no frost) → 1 (all 16 days below threshold).
""")

with col2:
    st.subheader("S — Price Sensitivity")
    st.markdown("""
Crop-level metric from **province-level Two-Way Fixed Effects** regressions
(CSSM 502, May 2026).

$$S_j = \\text{Lag1 coefficient} \\times 100$$

Interpretation: % price change one month after a frost shock.
Min-max normalized across **non-flagged** products only.
Flagged products (negative Lag1 or zero dormancy response) → S = 0.
""")

with col3:
    st.subheader("P — Production Share")
    st.markdown("""
Province × crop metric from TÜİK production data (2022–2024 average).

**Hybrid normalization (2-stage):**
1. `national_share` = product's total production / all basket products' total
2. `city_share_within` = city's share of that product's national production
3. `P_combined = national_share × city_share_within`
4. Global min-max → P_norm

Rationale: pure global normalization causes Domates to dominate;
pure within-product normalization inflates Roka. Hybrid balances both.
""")

# ---------------------------------------------------------------------------
# Sensitivity table
# ---------------------------------------------------------------------------

st.markdown("---")
st.header("Product Basket & Sensitivity Values")

import pandas as pd

rows = []
for product, info in SENSITIVITY_TABLE.items():
    flag_display = {
        None: "—",
        "insufficient_signal": "⚠ Insufficient signal (Lag1 < 0)",
        "zero_response":       "⚠ Zero response (dormancy) — spring window",
    }.get(info["flag"], info["flag"])
    rows.append({
        "Product": product,
        "Category": info["category"],
        "Sj (%)": info["sj"],
        "Flag": flag_display,
    })

st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Model specification
# ---------------------------------------------------------------------------

st.markdown("---")
st.header("Empirical Model")
st.markdown("""
**Two-Way Fixed Effects** with clustered standard errors (city level):

$$\\Delta \\log P_{it} = \\beta_0 + \\sum_{l=0}^{3} \\beta_l \\cdot \\text{Frost}_{i,t-l} + \\gamma X_{it} + \\alpha_i + \\delta_t + \\mu_m + \\varepsilon_{it}$$

- Frost dummy: 1 if monthly min_temp < –2.0°C (threshold from GBR Partial Dependence Plot)
- Controls (X): Production_Quantity, wind_speed, precipitation, humidity
- Fixed effects: province (α), year (δ), month (μ) — month FE added for seasonality
- **Lag1** used as Sj (price effect materializes one month after shock)
- Clustering: standard errors clustered at city level
""")

# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------

st.markdown("---")
st.header("Data Sources")

st.table(pd.DataFrame([
    {"Source": "TÜİK",       "Content": "Farm-gate prices (monthly, 162 products, 81 provinces, 2014–2024)"},
    {"Source": "TÜİK",       "Content": "Annual production quantities by province and product"},
    {"Source": "ERA5-Land",  "Content": "Monthly min temperature via Open-Meteo historical API"},
    {"Source": "Open-Meteo", "Content": "16-day daily min temperature forecast (no API key required)"},
    {"Source": "TÜİK CPI",   "Content": "Consumer price index for real price deflation (base: Jan 2024)"},
]))

# ---------------------------------------------------------------------------
# Limitations
# ---------------------------------------------------------------------------

st.markdown("---")
st.header("Limitations")

st.markdown("""
- **Monthly resolution.** Cannot detect within-month price dynamics. A frost on the 28th
  is indistinguishable from one on the 2nd.
- **2025 data unavailable.** TÜİK has not published 2025 farm-gate prices.
  Historical analysis ends December 2024.
- **Compound shocks.** Co-occurring droughts, cold snaps, and logistics disruptions
  cannot be decomposed with the current model.
- **Stone fruit spring window.** Stone fruits (cherry, apricot, peach, plum, strawberry,
  sour cherry) are dormant in winter; their critical vulnerability window is **April–May**.
  Spring frost coefficients are reserved for thesis extension.
- **hal.gov.tr.** The Hal (wholesale market) price system offers higher-frequency data
  and is a natural complement to this dashboard. Integration is excluded due to
  price-level differences (wholesale vs. farm-gate) and scope constraints.
- **Prototype framing.** This is a course capstone demonstration, not a production system.
  TARSİM integration, real-time alerts, and multi-hazard stacking are future work.
""")

# ---------------------------------------------------------------------------
# About
# ---------------------------------------------------------------------------

st.markdown("---")
st.header("About")

st.markdown("""
**FrostAlert-TR** was developed as the capstone project for CSSM 550 — Digital Solutions
for SDGs (Koç University, CSS Master's Program, 2026).

It operationalizes empirical results from CSSM 502 (Advanced Data Analysis) and adapts
the IPCC Exposure–Sensitivity framework to the agricultural price transmission channel.

**SDG alignment:** SDG 2 (Zero Hunger), SDG 13 (Climate Action)

**Policy context:** The 2025 Turkish spring frost crisis affected 65 provinces and 16 fruit
product groups, triggering TL 46.5 billion in combined TARSİM and government disbursements.
Existing early warning systems (FAO GIEWS, NASA Harvest) are cereal-centric and do not
cover Turkey's perishable fruit and vegetable sector.
""")
