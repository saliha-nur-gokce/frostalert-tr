import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import FROST_THRESHOLD, SENSITIVITY_TABLE

st.set_page_config(page_title="Methodology — FrostAlert-TR", page_icon="❄️", layout="wide")
from utils.styles import inject_global_css
inject_global_css()

st.markdown("""
<style>
[data-testid="stMainBlockContainer"] { padding-top: 0 !important; }
[data-testid="stAppViewContainer"] { background: #000 !important; }
section[data-testid="stSidebar"] + div { background: #000 !important; }
[data-testid="stHeader"] { background: #000 !important; border-bottom: none !important; }
[data-testid="stDecoration"] { display: none !important; }
.stMainBlockContainer { background: #000 !important; }
header[data-testid="stHeader"] { background-color: #000 !important; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_hero_image() -> str:
    import base64
    p = Path(__file__).parent.parent / "images" / "vegetables.png"
    if p.exists():
        with open(p, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{b64}"
    return ""


hero_src = load_hero_image()
hero_bg_css = (
    f"background-image:url({hero_src}); background-size:cover; background-position:center;"
    if hero_src else ""
)

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.markdown(f"""
<div style="
    {hero_bg_css}
    background-color:#000;
    position:relative;
    min-height:300px;
    margin:-1rem -1rem 0 -1rem;
    overflow:hidden;
">
<div style="position:absolute; inset:0; background:rgba(0,0,0,0.82);"></div>
<div style="position:relative; z-index:2; padding:56px; max-width:700px;">
<div style="display:inline-block; border:1px solid #555; color:#555; font-size:0.7em;
font-weight:600; letter-spacing:2px; padding:4px 12px; border-radius:20px; margin-bottom:28px;">
SDG 2 · SDG 13 · CSSM 550 · KOÇ ÜNİVERSİTESİ · 2026</div>
<h1 style="color:#ffffff; font-size:3.2em; font-weight:900; letter-spacing:-1.5px;
margin:0 0 16px 0; line-height:1.1;">
<span style="color:#ffffff;font-weight:900">METHODOLOGY</span><br>
<span style="color:#7ec8e3;font-weight:900">& ABOUT</span></h1>
<p style="color:#cccccc; font-size:1.05em; line-height:1.65; margin:0;">
Province-level frost risk scoring — empirical model, data sources, and design decisions.</p>
</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Risk Score Formula
# ---------------------------------------------------------------------------
st.markdown("""
<div style="padding:0 8px;">
<div style="color:#ffffff; font-size:26px; font-weight:700; letter-spacing:1px;
border-bottom:1px solid #1e3448; padding-bottom:12px; margin:48px 0 24px;">
RISK SCORE FORMULA
</div>
</div>
""", unsafe_allow_html=True)

components.html("""
<script>
window.MathJax = {tex: {displayMath: [['\\\\[','\\\\]']]}};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
<div style="background:#0a1628;border:1px solid #1e3448;border-radius:8px;
padding:24px;text-align:center;color:#fff;font-size:1.1em">
\\[ \\text{Risk}_{ij} = E_i \\times S_j \\times P_{ij} \\times 100 \\]
</div>
""", height=120)

col_e, col_s, col_p = st.columns(3)

with col_e:
    st.markdown("""
<div style="background:rgba(255,255,255,0.03); border:1px solid #1e3448;
border-top:3px solid #7ec8e3; border-radius:8px; padding:20px;">
<div style="color:#7ec8e3; font-weight:700; font-size:18px; margin-bottom:12px;">E — Frost Exposure</div>
<div style="color:#aaaaaa; font-size:17px; line-height:1.6;">
Province-level metric derived from the Open-Meteo 16-day forecast.
Normalized min-max across all 81 provinces before multiplication.
Range: 0 (no frost) → 1 (all 16 days below threshold).
</div>
</div>
""", unsafe_allow_html=True)
    components.html("""
<style>html,body{margin:0;padding:0;background:#0a0a0a;}</style>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
<div style="color:#fff;text-align:center;margin-top:8px">
\\[ E_i = \\dfrac{\\text{days with min temp} < -2.0°C}{16} \\]
</div>
""", height=80)

with col_s:
    st.markdown("""
<div style="background:rgba(255,255,255,0.03); border:1px solid #1e3448;
border-top:3px solid #ffd944; border-radius:8px; padding:20px;">
<div style="color:#ffd944; font-weight:700; font-size:18px; margin-bottom:12px;">S — Price Sensitivity</div>
<div style="color:#aaaaaa; font-size:17px; line-height:1.6;">
Crop-level metric from province-level Two-Way Fixed Effects regressions.
Interpretation: % price change one month after a frost shock.
Min-max normalized across non-flagged products only.
Flagged products (negative Lag1 or zero dormancy response) → S = 0.
</div>
</div>
""", unsafe_allow_html=True)
    components.html("""
<style>html,body{margin:0;padding:0;background:#0a0a0a;}</style>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
<div style="color:#fff;text-align:center;margin-top:8px">
\\[ S_j = \\text{Lag1 coefficient} \\times 100 \\]
</div>
""", height=70)

with col_p:
    st.markdown("""
<div style="background:rgba(255,255,255,0.03); border:1px solid #1e3448;
border-top:3px solid #7ec8e3; border-radius:8px; padding:20px;">
<div style="color:#7ec8e3; font-weight:700; font-size:18px; margin-bottom:12px;">P — Production Share</div>
<div style="color:#aaaaaa; font-size:17px; line-height:1.6;">
Province × crop metric from TÜİK production data (2022–2024 average).
Hybrid normalization (2-stage):
</div>
<div style="margin:12px 0">
<div style="color:#7ec8e3;font-size:17px;line-height:2.2">
· national_share = product total / basket total<br>
· city_share_within = city's share of national production<br>
· P_combined = national_share × city_share_within<br>
· Global min-max → P_norm
</div>
</div>
<div style="color:#aaaaaa; font-size:15px; margin-top:10px; line-height:1.5;">
Rationale: pure global normalization causes Domates to dominate; hybrid balances both.
</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sensitivity table — built dynamically from SENSITIVITY_TABLE
# ---------------------------------------------------------------------------
rows_html = ""
category_bgs = {
    "Vegetables":   "rgba(76,175,80,0.07)",
    "Citrus":       "rgba(255,152,0,0.07)",
    "Citrus/Other": "rgba(255,152,0,0.07)",
    "Pome":         "rgba(91,141,184,0.07)",
    "Stone fruit":  "rgba(126,200,227,0.07)",
}
for i, (product, info) in enumerate(SENSITIVITY_TABLE.items()):
    flag_val = info["flag"]
    if flag_val is None:
        flag_text = "—"
        flag_color = "#555"
    elif flag_val == "insufficient_signal":
        flag_text = "⚠ Insufficient signal"
        flag_color = "#7ec8e3"
    else:
        flag_text = "⚠ Zero response (dormancy)"
        flag_color = "#ffd944"
    sj_display = f"{info['sj']:.2f}"
    row_bg = "rgba(255,255,255,0.02)" if i % 2 == 0 else "transparent"
    category = info.get("category", "")
    cat_bg = category_bgs.get(category, "transparent")
    rows_html += (
        f'<tr style="background:{row_bg};">'
        f'<td style="padding:13px 16px;border-bottom:1px solid #0d1f33;'
        f'background:{cat_bg};color:#cccccc;font-weight:600">{product}</td>'
        f'<td style="background:{cat_bg};color:#cccccc; padding:13px 16px; border-bottom:1px solid #0d1f33;">{category}</td>'
        f'<td style="color:#ffd944; font-weight:600; text-align:right; padding:13px 16px;'
        f' border-bottom:1px solid #0d1f33;">{sj_display}</td>'
        f'<td style="padding:13px 16px; border-bottom:1px solid #0d1f33; white-space:nowrap;">'
        f'<span style="color:{flag_color}; font-size:14px;">{flag_text}</span></td>'
        f'</tr>\n'
    )

st.markdown(f"""
<div style="padding:0 8px;">
<div style="color:#ffffff; font-size:26px; font-weight:700; letter-spacing:1px;
border-bottom:1px solid #1e3448; padding-bottom:12px; margin:48px 0 24px;">
PRODUCT BASKET &amp; SENSITIVITY VALUES
</div>
<div style="overflow-y:auto;max-height:380px;border-radius:6px">
<table style="width:100%; border-collapse:collapse; font-size:17px;">
<thead>
<tr style="background:#b8960a;">
<th style="color:#ffffff; font-weight:600; text-align:left; padding:13px 16px; border-bottom:1px solid #1e3448;">Product</th>
<th style="color:#ffffff; font-weight:600; text-align:left; padding:13px 16px; border-bottom:1px solid #1e3448;">Category</th>
<th style="color:#ffffff; font-weight:600; text-align:right; padding:13px 16px; border-bottom:1px solid #1e3448;">Sj (%)</th>
<th style="color:#ffffff; font-weight:600; text-align:left; padding:13px 16px; border-bottom:1px solid #1e3448;">Flag</th>
</tr>
</thead>
<tbody>
{rows_html}
</tbody>
</table>
</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Empirical Model
# ---------------------------------------------------------------------------
st.markdown("""
<div style="padding:0 8px;">
<div style="color:#ffffff; font-size:26px; font-weight:700; letter-spacing:1px;
border-bottom:1px solid #1e3448; padding-bottom:12px; margin:48px 0 24px;">
EMPIRICAL MODEL
</div>
</div>
""", unsafe_allow_html=True)

components.html("""
<style>html,body{margin:0;padding:0;background:#0a1628;}</style>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
<div style="color:#fff;text-align:center;padding:16px 0">
\\[ \\Delta \\log P_{it} = \\beta_0 + \\sum_{l=0}^{3} \\beta_l \\cdot \\text{Frost}_{i,t-l} + \\gamma X_{it} + \\alpha_i + \\delta_t + \\mu_m + \\varepsilon_{it} \\]
</div>
""", height=100)

st.markdown("""
<div style="padding:0 8px;">
<div style="background:#0a1628; border:1px solid #1e3448; border-radius:8px; padding:24px; color:#fff;">
<div style="color:#aaaaaa; font-size:17px; line-height:2.0;">
<span style="color:#cccccc; font-weight:600;">Two-Way Fixed Effects</span> with clustered standard errors (city level):<br>
<span style="color:#7ec8e3;">•</span> Frost dummy: 1 if monthly min_temp &lt; –2.0°C (threshold from GBR Partial Dependence Plot)<br>
<span style="color:#7ec8e3;">•</span> Controls (X): Production_Quantity, wind_speed, precipitation, humidity<br>
<span style="color:#7ec8e3;">•</span> Fixed effects: province (α), year (δ), month (μ) — month FE added for seasonality<br>
<span style="color:#7ec8e3;">•</span> <span style="font-weight:600;">Lag1</span> used as Sj (price effect materializes one month after shock)<br>
<span style="color:#7ec8e3;">•</span> Clustering: standard errors clustered at city level
</div>
</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Data Sources
# ---------------------------------------------------------------------------
st.markdown("""
<div style="padding:0 8px;">
<div style="color:#ffffff; font-size:26px; font-weight:700; letter-spacing:1px;
border-bottom:1px solid #1e3448; padding-bottom:12px; margin:48px 0 24px;">
DATA SOURCES
</div>
<div style="overflow-x:auto;">
<table style="width:100%; border-collapse:collapse; font-size:17px;">
<thead>
<tr style="background:#0a1628;">
<th style="color:#7ec8e3; font-weight:600; text-align:left; padding:10px 14px;
border-bottom:1px solid #1e3448; width:140px;">Source</th>
<th style="color:#7ec8e3; font-weight:600; text-align:left; padding:10px 14px;
border-bottom:1px solid #1e3448;">Content</th>
</tr>
</thead>
<tbody>
<tr style="background:rgba(255,255,255,0.02);">
<td style="color:#ffd944; font-weight:600; padding:9px 14px; border-bottom:1px solid #0d1f33;">TÜİK</td>
<td style="color:#cccccc; padding:9px 14px; border-bottom:1px solid #0d1f33;">Farm-gate prices (monthly, 162 products, 81 provinces, 2014–2024)</td>
</tr>
<tr>
<td style="color:#ffd944; font-weight:600; padding:9px 14px; border-bottom:1px solid #0d1f33;">TÜİK</td>
<td style="color:#cccccc; padding:9px 14px; border-bottom:1px solid #0d1f33;">Annual production quantities by province and product</td>
</tr>
<tr style="background:rgba(255,255,255,0.02);">
<td style="color:#ffd944; font-weight:600; padding:9px 14px; border-bottom:1px solid #0d1f33;">ERA5-Land</td>
<td style="color:#cccccc; padding:9px 14px; border-bottom:1px solid #0d1f33;">Monthly min temperature via Open-Meteo historical API</td>
</tr>
<tr>
<td style="color:#ffd944; font-weight:600; padding:9px 14px; border-bottom:1px solid #0d1f33;">Open-Meteo</td>
<td style="color:#cccccc; padding:9px 14px; border-bottom:1px solid #0d1f33;">16-day daily min temperature forecast (no API key required)</td>
</tr>
<tr style="background:rgba(255,255,255,0.02);">
<td style="color:#ffd944; font-weight:600; padding:9px 14px; border-bottom:1px solid #0d1f33;">TÜİK CPI</td>
<td style="color:#cccccc; padding:9px 14px; border-bottom:1px solid #0d1f33;">Consumer price index for real price deflation (base: Jan 2024)</td>
</tr>
</tbody>
</table>
</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Limitations
# ---------------------------------------------------------------------------
st.markdown("""
<div style="padding:0 8px;">
<div style="color:#ffffff; font-size:26px; font-weight:700; letter-spacing:1px;
border-bottom:1px solid #1e3448; padding-bottom:12px; margin:48px 0 24px;">
LIMITATIONS
</div>

<div style="background:rgba(255,255,255,0.03); border-left:3px solid #ffd944;
border-radius:0 6px 6px 0; padding:12px 16px; margin-bottom:10px;">
<div style="color:#ffd944; font-weight:700; font-size:17px;">Monthly resolution</div>
<div style="color:#aaaaaa; font-size:17px; line-height:1.7; margin-top:4px;">
Cannot detect within-month price dynamics. A frost on the 28th is indistinguishable from one on the 2nd.
Event study windows may additionally show price increases preceding the labeled shock month, reflecting either
anticipatory market responses or earlier frost exposure within the same winter season.
</div>
</div>

<div style="background:rgba(255,255,255,0.03); border-left:3px solid #ffd944;
border-radius:0 6px 6px 0; padding:12px 16px; margin-bottom:10px;">
<div style="color:#ffd944; font-weight:700; font-size:17px;">2025 data unavailable</div>
<div style="color:#aaaaaa; font-size:17px; line-height:1.7; margin-top:4px;">
TÜİK has not published 2025 farm-gate prices. Historical analysis ends December 2024.
</div>
</div>

<div style="background:rgba(255,255,255,0.03); border-left:3px solid #ffd944;
border-radius:0 6px 6px 0; padding:12px 16px; margin-bottom:10px;">
<div style="color:#ffd944; font-weight:700; font-size:17px;">Event study coverage</div>
<div style="color:#aaaaaa; font-size:17px; line-height:1.7; margin-top:4px;">
High-production provinces for some crops (e.g. Antalya and İzmir for Domates) rarely experience frost,
making it impossible to construct event study windows for the most economically significant city–product pairs.
The risk score reflects potential impact under a frost scenario, not observed historical events.
</div>
</div>

<div style="background:rgba(255,255,255,0.03); border-left:3px solid #ffd944;
border-radius:0 6px 6px 0; padding:12px 16px; margin-bottom:10px;">
<div style="color:#ffd944; font-weight:700; font-size:17px;">Compound shocks</div>
<div style="color:#aaaaaa; font-size:17px; line-height:1.7; margin-top:4px;">
Co-occurring droughts, cold snaps, and logistics disruptions cannot be decomposed with the current model.
</div>
</div>

<div style="background:rgba(255,255,255,0.03); border-left:3px solid #ffd944;
border-radius:0 6px 6px 0; padding:12px 16px; margin-bottom:10px;">
<div style="color:#ffd944; font-weight:700; font-size:17px;">Stone fruit spring window</div>
<div style="color:#aaaaaa; font-size:17px; line-height:1.7; margin-top:4px;">
Stone fruits (cherry, apricot, peach, plum, strawberry, sour cherry) are dormant in winter; their critical
vulnerability window is <span style="color:#fff; font-weight:600;">April–May</span>.
Spring frost coefficients are reserved for thesis extension.
</div>
</div>

<div style="background:rgba(255,255,255,0.03); border-left:3px solid #ffd944;
border-radius:0 6px 6px 0; padding:12px 16px; margin-bottom:10px;">
<div style="color:#ffd944; font-weight:700; font-size:17px;">hal.gov.tr</div>
<div style="color:#aaaaaa; font-size:17px; line-height:1.7; margin-top:4px;">
The Hal (wholesale market) price system offers higher-frequency data and is a natural complement to this
dashboard. Integration is excluded due to price-level differences (wholesale vs. farm-gate) and scope constraints.
</div>
</div>

<div style="background:rgba(255,255,255,0.03); border-left:3px solid #ffd944;
border-radius:0 6px 6px 0; padding:12px 16px; margin-bottom:10px;">
<div style="color:#ffd944; font-weight:700; font-size:17px;">Prototype framing</div>
<div style="color:#aaaaaa; font-size:17px; line-height:1.7; margin-top:4px;">
This is a course capstone demonstration, not a production system.
TARSİM integration, real-time alerts, and multi-hazard stacking are future work.
</div>
</div>

</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# About
# ---------------------------------------------------------------------------
st.markdown("""
<div style="padding:0 8px; margin-bottom:48px;">
<div style="color:#ffffff; font-size:26px; font-weight:700; letter-spacing:1px;
border-bottom:1px solid #1e3448; padding-bottom:12px; margin:48px 0 24px;">
ABOUT
</div>
<div style="background:rgba(14,31,51,0.8); border:1px solid #1e3448; border-radius:8px;
padding:24px 28px; margin-top:8px;">
<div style="color:#7ec8e3; font-weight:700; font-size:18px; margin-bottom:12px;">About FrostAlert-TR</div>
<div style="color:#aaaaaa; line-height:1.7; font-size:17px;">
<b style="color:#cccccc;">FrostAlert-TR</b> was developed as the capstone project for CSSM 550 — Digital Solutions
for SDGs (Koç University, CSS Master's Program, 2026).<br><br>
It operationalizes empirical results from CSSM 502 (Advanced Data Analysis) and adapts
the IPCC Exposure–Sensitivity framework to the agricultural price transmission channel.<br><br>
<span style="color:#ffd944;">SDG alignment: SDG 2 (Zero Hunger), SDG 13 (Climate Action)</span><br><br>
<span style="color:#aaaaaa;">Policy context: The 2025 Turkish spring frost crisis affected 65 provinces and 16 fruit
product groups, triggering TL 46.5 billion in combined TARSİM and government disbursements.
Existing early warning systems (FAO GIEWS, NASA Harvest) are cereal-centric and do not
cover Turkey's perishable fruit and vegetable sector.</span>
</div>
</div>
</div>
""", unsafe_allow_html=True)
