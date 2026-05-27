import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import MAIN_DATA_PATH, PRODUCT_DISPLAY_NAMES
from utils.event_study import build_event_study_plot

st.set_page_config(page_title="Product Detail — FrostAlert-TR", page_icon="❄️", layout="wide")

from utils.styles import inject_global_css
inject_global_css()

WHISKER_DATA_PATH = Path(__file__).parent.parent / "data" / "whisker_data.csv"

CURATED_EVENTS = [
    {"label": "Burdur — Biber (Jan 2022, +62%)",         "city": "Burdur",     "product": "Biber",     "year": 2022, "month": 1},
    {"label": "Konya — Biber (Feb 2023, +57%)",           "city": "Konya",      "product": "Biber",     "year": 2023, "month": 2},
    {"label": "Gümüşhane — Ispanak (Jan 2019, +45%)",     "city": "Gümüşhane", "product": "Ispanak",   "year": 2019, "month": 1},
    {"label": "Kütahya — Ispanak (Jan 2019, +44%)",       "city": "Kütahya",   "product": "Ispanak",   "year": 2019, "month": 1},
    {"label": "Karaman — Biber (Feb 2023, +42%)",         "city": "Karaman",    "product": "Biber",     "year": 2023, "month": 2},
    {"label": "Karaman — Patlıcan (Feb 2023, +27%)",      "city": "Karaman",    "product": "Patlıcan",  "year": 2023, "month": 2},
    {"label": "Bilecik — Ispanak (Jan 2017, +26%)",       "city": "Bilecik",    "product": "Ispanak",   "year": 2017, "month": 1},
    {"label": "Ankara — Ispanak (Jan 2017, +17%)",        "city": "Ankara",     "product": "Ispanak",   "year": 2017, "month": 1},
    {"label": "Kırşehir — Biber (Feb 2023, +17%)",        "city": "Kırşehir",  "product": "Biber",     "year": 2023, "month": 2},
    {"label": "Tokat — Ispanak (Jan 2017, +8%)",          "city": "Tokat",      "product": "Ispanak",   "year": 2017, "month": 1},
    {"label": "Bartın — Mandalina (Jan 2017, +8%)",       "city": "Bartın",    "product": "Mandalina", "year": 2017, "month": 1},
    {"label": "Karaman — Domates (Feb 2023, +4%)",        "city": "Karaman",    "product": "Domates",   "year": 2023, "month": 2},
]

CATEGORY_COLORS = {
    "Vegetables":  "#4ade80",
    "Citrus":      "#fb923c",
    "Pome":        "#c084fc",
    "Stone fruit": "#38bdf8",
}

PRODUCT_CATEGORIES = {
    "Tomato":      "Vegetables",
    "Pepper":      "Vegetables",
    "Eggplant":    "Vegetables",
    "Cucumber":    "Vegetables",
    "Spinach":     "Vegetables",
    "Arugula":     "Vegetables",
    "Radish":      "Vegetables",
    "Orange":      "Citrus",
    "Mandarin":    "Citrus",
    "Pomegranate": "Citrus",
    "Apple":       "Pome",
    "Cherry":      "Stone fruit",
    "Sour Cherry": "Stone fruit",
    "Apricot":     "Stone fruit",
    "Peach":       "Stone fruit",
    "Plum":        "Stone fruit",
    "Strawberry":  "Stone fruit",
}

DISPLAY_ORDER = [
    "Tomato", "Pepper", "Eggplant", "Cucumber", "Spinach", "Arugula", "Radish",
    "Orange", "Mandarin", "Pomegranate",
    "Apple",
    "Cherry", "Sour Cherry", "Apricot", "Peach", "Plum", "Strawberry",
]


@st.cache_data(show_spinner=False)
def load_detail_data() -> pd.DataFrame:
    cols = ["City", "Year", "Month", "date", "Product_Name",
            "Real_Price", "Production_Quantity", "min_temp"]
    return pd.read_csv(MAIN_DATA_PATH, usecols=cols, parse_dates=["date"])


@st.cache_data(show_spinner=False)
def load_whisker_data() -> pd.DataFrame:
    return pd.read_csv(WHISKER_DATA_PATH)


def build_whisker_plot(df_viz: pd.DataFrame) -> go.Figure:
    lag1 = df_viz[df_viz["Lag"] == 1].set_index("Product").reindex(DISPLAY_ORDER)
    lag2 = df_viz[df_viz["Lag"] == 2].set_index("Product").reindex(DISPLAY_ORDER)

    fig = go.Figure()

    category_spans = {}
    for i, product in enumerate(DISPLAY_ORDER):
        cat = PRODUCT_CATEGORIES.get(product, "Vegetables")
        if cat not in category_spans:
            category_spans[cat] = [i, i]
        else:
            category_spans[cat][1] = i

    for cat, (y0, y1) in category_spans.items():
        color = CATEGORY_COLORS[cat]
        fig.add_hrect(
            y0=y0 - 0.5, y1=y1 + 0.5,
            fillcolor=color, opacity=0.07,
            layer="below", line_width=0,
        )

    fig.add_trace(go.Scatter(
        x=lag2["Coef"],
        y=DISPLAY_ORDER,
        mode="markers",
        name="2 Months Later (Lag 2)",
        marker=dict(symbol="square", color="#7ec8e3", size=9),
        error_x=dict(
            type="data",
            symmetric=False,
            array=lag2["Error_Max"].tolist(),
            arrayminus=lag2["Error_Min"].tolist(),
            color="#7ec8e3",
            thickness=1.5,
            width=5,
        ),
    ))

    fig.add_trace(go.Scatter(
        x=lag1["Coef"],
        y=DISPLAY_ORDER,
        mode="markers",
        name="1 Month Later (Lag 1)",
        marker=dict(symbol="circle", color="#ff6b6b", size=9),
        error_x=dict(
            type="data",
            symmetric=False,
            array=lag1["Error_Max"].tolist(),
            arrayminus=lag1["Error_Min"].tolist(),
            color="#ff6b6b",
            thickness=1.5,
            width=5,
        ),
    ))

    fig.add_vline(x=0, line_color="#4a5568", line_width=1)

    for cat, (y0, y1) in category_spans.items():
        fig.add_annotation(
            x=1.01, y=(y0 + y1) / 2,
            xref="paper", yref="y",
            text=cat,
            showarrow=False,
            font=dict(size=10, color=CATEGORY_COLORS[cat]),
            xanchor="left",
        )

    fig.update_layout(
        title="Heterogeneous Impact of Frost Shocks on Prices (Lag 1 & Lag 2)",
        title_font=dict(color="#8ab4cc"),
        font=dict(color="#e8f4f8"),
        yaxis_title=None,
        template="plotly_dark",
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#111111",
        height=520,
        margin=dict(l=20, r=120, t=50, b=40),
        legend=dict(orientation="h", y=-0.08, x=0, font=dict(color="#e8f4f8")),
        xaxis=dict(
            title="Price Impact (%)",
            tickfont=dict(color="#8ab4cc"),
            title_font=dict(color="#8ab4cc"),
            gridcolor="rgba(255,255,255,0.06)",
            zerolinecolor="#4a5568",
        ),
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(color="#e8f4f8"),
            gridcolor="rgba(255,255,255,0.04)",
        ),
    )
    return fig


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

st.markdown("""
<div style='font-size:2.2em;font-weight:900;letter-spacing:-0.5px;margin-bottom:0.5em;line-height:1.1'>
<span style='color:#ffffff'>PRODUCT</span><br>
<span style='color:#7ec8e3'>DETAIL</span>
</div>
""", unsafe_allow_html=True)
st.markdown("Heterogeneous frost-price impacts by product and historical event study.")

# ---------------------------------------------------------------------------
# Section 1: Whisker plot
# ---------------------------------------------------------------------------

st.markdown("<h3 style='color:#ffd944 !important;font-weight:700'>Heterogeneous impact of frost shocks on prices (Lag 1 + Lag 2)</h3>", unsafe_allow_html=True)

if WHISKER_DATA_PATH.exists():
    df_viz = load_whisker_data()
    fig_whisker = build_whisker_plot(df_viz)
    st.plotly_chart(fig_whisker, use_container_width=True)
    st.caption(
        "Two-Way Fixed Effects regression with city-clustered standard errors. "
        "Stone fruits show near-zero response during winter dormancy (Nov–Mar); "
        "price risk window for these crops is April–May."
    )
else:
    st.warning(f"Whisker data not found at: {WHISKER_DATA_PATH}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Section 2: Historical event study
# ---------------------------------------------------------------------------

st.markdown("<h3 style='color:#ffd944 !important;font-weight:700'>Historical event study</h3>", unsafe_allow_html=True)

with st.spinner("Loading data…"):
    df = load_detail_data()

def _translate_event_label(label: str) -> str:
    for tr, en in PRODUCT_DISPLAY_NAMES.items():
        label = label.replace(f"— {tr} ", f"— {en} ")
    return label

_translated_labels = [_translate_event_label(e["label"]) for e in CURATED_EVENTS]

selected_label = st.selectbox("Select event", options=_translated_labels, index=1)
original_label = CURATED_EVENTS[_translated_labels.index(selected_label)]["label"]
st.caption(
    "Price change (%) calculated as mean real price in the 3 months following "
    "the frost event vs. 3 months prior."
)

event = next(e for e in CURATED_EVENTS if e["label"] == original_label)
city    = event["city"]
product = event["product"]
year    = event["year"]
month   = event["month"]

with st.spinner("Rendering event study…"):
    fig = build_event_study_plot(df, city, product, year, month)
    st.plotly_chart(fig, use_container_width=True)

from config import PRODUCT_FILTER_MAP
filt = PRODUCT_FILTER_MAP.get(product, product)
event_row = df[
    (df["City"] == city)
    & (df["Product_Name"].str.contains(filt, na=False, regex=False))
    & (df["Year"] == year)
    & (df["Month"] == month)
]
if not event_row.empty:
    min_temp_val = event_row["min_temp"].min()
    st.caption(f"Worst frost recorded: {min_temp_val:.1f}°C ({month}/{year})")
