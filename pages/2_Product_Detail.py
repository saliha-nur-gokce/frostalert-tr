import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    MAIN_DATA_PATH, PRODUCT_BASKET,
)
from utils.event_study import build_event_study_plot, find_worst_frost_event

st.set_page_config(page_title="Product Detail — FrostAlert-TR", layout="wide")

DEFAULT_CITY    = "Konya"
DEFAULT_PRODUCT = "Biber"
DEFAULT_YEAR    = 2023
DEFAULT_MONTH   = 2

WHISKER_DATA_PATH = Path(__file__).parent.parent / "data" / "whisker_data.csv"

CATEGORY_COLORS = {
    "Vegetables":   "#2ca02c",
    "Citrus":       "#ff7f0e",
    "Pome":         "#9467bd",
    "Stone fruit":  "#1f77b4",
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
        marker=dict(symbol="square", color="#1f77b4", size=9),
        error_x=dict(
            type="data",
            symmetric=False,
            array=lag2["Error_Max"].tolist(),
            arrayminus=lag2["Error_Min"].tolist(),
            color="#1f77b4",
            thickness=1.5,
            width=5,
        ),
    ))

    fig.add_trace(go.Scatter(
        x=lag1["Coef"],
        y=DISPLAY_ORDER,
        mode="markers",
        name="1 Month Later (Lag 1)",
        marker=dict(symbol="circle", color="#d62728", size=9),
        error_x=dict(
            type="data",
            symmetric=False,
            array=lag1["Error_Max"].tolist(),
            arrayminus=lag1["Error_Min"].tolist(),
            color="#d62728",
            thickness=1.5,
            width=5,
        ),
    ))

    fig.add_vline(x=0, line_color="black", line_width=1)

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
        xaxis_title="Price Impact (%)",
        yaxis_title=None,
        template="plotly_white",
        height=520,
        margin=dict(l=20, r=120, t=50, b=40),
        legend=dict(orientation="h", y=-0.08, x=0),
        yaxis=dict(autorange="reversed"),
    )
    return fig


st.title("Product Detail")
st.markdown("Heterogeneous frost-price impacts by product and historical event study.")

st.subheader("Heterogeneous impact of frost shocks on prices (Lag 1 + Lag 2)")

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

st.subheader("Historical event study")

with st.sidebar:
    st.header("Event study controls")
    selected_product = st.selectbox("Product", PRODUCT_BASKET,
                                    index=PRODUCT_BASKET.index(DEFAULT_PRODUCT))
    with st.spinner("Loading province list…"):
        df = load_detail_data()
    cities = sorted(df["City"].dropna().unique().tolist())
    default_idx = cities.index(DEFAULT_CITY) if DEFAULT_CITY in cities else 0
    selected_city = st.selectbox("Province", cities, index=default_idx)

    auto_detect = st.checkbox("Auto-detect worst frost event", value=True)

    if not auto_detect:
        year  = st.number_input("Year",  min_value=2014, max_value=2024, value=DEFAULT_YEAR)
        month = st.number_input("Month", min_value=1,    max_value=12,   value=DEFAULT_MONTH)
    else:
        year, month = None, None

with st.spinner("Running event study…"):
    if auto_detect:
        event = find_worst_frost_event(df, selected_city, selected_product)
        if event is None:
            st.info(
                f"No frost event (min_temp < –2°C) found for **{selected_city} / {selected_product}**. "
                "Showing default event: Konya / Biber, Feb 2023."
            )
            event_year, event_month = DEFAULT_YEAR, DEFAULT_MONTH
        else:
            event_year, event_month = event
    else:
        event_year, event_month = int(year), int(month)

    caption = (
        f"Worst frost event detected: **{event_month}/{event_year}** — "
        f"{selected_city} / {selected_product}"
        if auto_detect
        else f"Custom event: {event_month}/{event_year}"
    )
    st.caption(caption)
    fig = build_event_study_plot(df, selected_city, selected_product, event_year, event_month)
    st.plotly_chart(fig, use_container_width=True)
