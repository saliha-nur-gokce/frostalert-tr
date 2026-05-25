import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    COLOR_SCALE, COORDS_PATH, GEOJSON_PATH, GEOJSON_URL,
    GEOJSON_TO_CITY, MAIN_DATA_PATH, MAP_CENTER, MAP_STYLE,
    MAP_ZOOM, PRODUCT_BASKET, SENSITIVITY_TABLE,
)
from utils.forecast import fetch_all_forecasts, compute_simulated_exposure
from utils.risk_score import compute_historical_exposure, compute_production_norms, compute_risk_scores

st.set_page_config(page_title="Risk Map — FrostAlert-TR", layout="wide")

# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_coords() -> pd.DataFrame:
    return pd.read_csv(COORDS_PATH)


@st.cache_data(show_spinner=False)
def load_main(cols: list[str]) -> pd.DataFrame:
    df = pd.read_csv(MAIN_DATA_PATH, usecols=cols, parse_dates=["date"])
    return df


@st.cache_data(show_spinner=False)
def load_geojson() -> dict:
    if GEOJSON_PATH.exists():
        with open(GEOJSON_PATH, encoding="utf-8") as f:
            return json.load(f)
    r = requests.get(GEOJSON_URL, timeout=30)
    r.raise_for_status()
    data = r.json()
    GEOJSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(GEOJSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data


@st.cache_data(show_spinner=False)
def compute_global_reference_max(_main_df: pd.DataFrame) -> float:
    _seasons = ["2022–2024 average", "2022–2023", "2023–2024", "2024–2025 (partial)"]
    _prod_norm = compute_production_norms(_main_df)
    _all_scores: list[float] = []
    for _season in _seasons:
        _exp = compute_historical_exposure(_main_df, _season)
        for _p in PRODUCT_BASKET:
            _all_scores.extend(
                compute_risk_scores(_exp, _prod_norm, _p)["risk_score"].tolist()
            )
    return max(max(_all_scores) if _all_scores else 0.1, 0.1)


def normalize_geojson_names(geojson: dict) -> dict:
    """Apply GEOJSON_TO_CITY corrections to feature properties."""
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        for key in ("name", "NAME", "il_adi", "province"):
            if key in props:
                props[key] = GEOJSON_TO_CITY.get(props[key], props[key])
    # Strip all properties except the name key to prevent label rendering
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        name_val = props.get("name") or props.get("NAME") or props.get("il_adi") or props.get("province") or ""
        feature["properties"] = {"name": name_val}
    return geojson


# ---------------------------------------------------------------------------
# Detect the property key used for province names in the loaded GeoJSON
# ---------------------------------------------------------------------------

def detect_name_key(geojson: dict) -> str:
    candidates = ("name", "NAME", "il_adi", "province", "NAME_1")
    features = geojson.get("features", [])
    if not features:
        return "name"
    props = features[0].get("properties", {})
    for key in candidates:
        if key in props:
            return key
    return next(iter(props), "name")


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

st.title("Frost Risk Map")

_col_product, _col_mode = st.columns([1, 2])
with _col_product:
    selected_product = st.selectbox("Product", ["All products (max risk)"] + PRODUCT_BASKET, index=0)
with _col_mode:
    mode = st.radio(
        "Exposure mode",
        [
            "🌡️ Live forecast (16-day)",
            "📊 Historical exposure (2022–2024 winter avg)",
            "🧪 Simulate winter conditions (demo)",
        ],
        index=1,
        horizontal=True,
    )

if mode == "📊 Historical exposure (2022–2024 winter avg)":
    hist_season = st.selectbox(
        "Winter season",
        ["2022–2024 average", "2022–2023", "2023–2024", "2024–2025 (partial)"],
        index=0,
    )
else:
    hist_season = "2022–2024 average"

if mode == "🧪 Simulate winter conditions (demo)":
    sim_frost_days = st.slider("Simulated frost days", min_value=1, max_value=16, value=5, step=1)
else:
    sim_frost_days = 5

# Stone fruit warning
if selected_product != "All products (max risk)":
  info = SENSITIVITY_TABLE[selected_product]
if selected_product != "All products (max risk)" and info["flag"] == "zero_response":
    st.warning(
        f"**{selected_product}** is a stone fruit. Winter (Nov–Mar) frost has no detected "
        "price effect during dormancy. The relevant risk window is **April–May** (spring frost). "
        "Risk scores shown below reflect production exposure only; price sensitivity = 0.",
        icon="⚠️",
    )
elif selected_product != "All products (max risk)" and info["flag"] == "insufficient_signal":
    st.info(
        f"**{selected_product}**: the Lag1 frost coefficient is negative across all varieties, "
        "likely due to harvest-season inventory effects. Price sensitivity is set to 0. "
        "Risk scores reflect exposure × production share only.",
        icon="ℹ️",
    )

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

with st.spinner("Loading data…"):
    coords_df  = load_coords()
    geojson    = normalize_geojson_names(load_geojson())
    name_key   = detect_name_key(geojson)
    needed_cols = ["City", "Year", "Month", "date", "Product_Name",
                   "Real_Price", "Production_Quantity", "min_temp"]
    main_df    = load_main(needed_cols)
    global_reference_max = compute_global_reference_max(main_df)

if mode == "🌡️ Live forecast (16-day)":
    with st.spinner("Fetching 16-day forecasts for 81 provinces…"):
        exposure_df = fetch_all_forecasts(coords_df)
elif mode == "🧪 Simulate winter conditions (demo)":
    exposure_df = compute_simulated_exposure(coords_df, sim_frost_days)
else:
    with st.spinner("Computing historical exposure…"):
        exposure_df = compute_historical_exposure(main_df, hist_season)

with st.spinner("Computing risk scores…"):
    prod_norm_df = compute_production_norms(main_df)
    if selected_product == "All products (max risk)":
        all_scores = []
        for _p in PRODUCT_BASKET:
            _df_p = compute_risk_scores(exposure_df, prod_norm_df, _p)[["City", "risk_score"]].copy()
            _df_p["top_crop"] = _p
            all_scores.append(_df_p)
        _all_df = pd.concat(all_scores, ignore_index=True)
        _idx = _all_df.groupby("City")["risk_score"].idxmax()
        risk_df = _all_df.loc[_idx].reset_index(drop=True)
        risk_df.loc[risk_df["risk_score"] == 0, "top_crop"] = ""

    else:
        risk_df = compute_risk_scores(exposure_df, prod_norm_df, selected_product)
        risk_df["top_crop"] = selected_product

_today = date.today()
_forecast_end = _today + timedelta(days=16)
max_score = max(float(risk_df["risk_score"].max()), 0.1)

if mode == "🌡️ Live forecast (16-day)":
    st.info(
        f"**Forecast window:** {_today.strftime('%d %b %Y')} → "
        f"{_forecast_end.strftime('%d %b %Y')} (16 days) · "
        f"Source: Open-Meteo ERA5-Land · Cache refreshes every 6 hours"
        f" | Max risk score: {max_score:.1f}",
        icon="🌡️",
    )
elif mode == "📊 Historical exposure (2022–2024 winter avg)":
    st.info(f"Historical exposure: {hist_season} | Max risk score: {max_score:.1f}", icon="📊")
else:
    st.warning("⚠️ Simulation mode: uniform frost shock applied to all provinces. Not a real forecast.")
    st.info(
        f"Simulation: {sim_frost_days}-day uniform frost shock applied to all provinces"
        f" | Max risk score: {max_score:.1f}",
        icon="🧪",
    )

# ---------------------------------------------------------------------------
# Choropleth map
# ---------------------------------------------------------------------------

risk_df = risk_df.rename(columns={"risk_score": "display_score"})

if selected_product == "All products (max risk)":
    risk_df["top_crop_label"] = risk_df["top_crop"].apply(
        lambda x: x if x else "No significant risk detected"
    )
    _hover_data = {"City": True, "display_score": ":.1f", "top_crop_label": True}
    _labels = {"display_score": "Max Risk Score", "top_crop_label": "Highest-risk crop"}
else:
    _hover_data = {
        "City": True, "display_score": ":.1f",
        "E_norm": ":.3f", "S_norm": ":.3f", "production_pct": ":.1f",
    }
    _labels = {
        "display_score": "Risk Score",
        "E_norm": "Exposure (norm)",
        "S_norm": "Sensitivity (norm)",
        "production_pct": "Production share (%)",
    }

if selected_product == "All products (max risk)":
    fig = px.choropleth_mapbox(
        risk_df,
        geojson=geojson,
        locations="City",
        featureidkey=f"properties.{name_key}",
        color="display_score",
        color_continuous_scale=COLOR_SCALE,
        range_color=(0, global_reference_max),
        mapbox_style=MAP_STYLE,
        zoom=MAP_ZOOM,
        center=MAP_CENTER,
        opacity=0.75,
        hover_data=_hover_data,
        labels=_labels,
        title=f"Frost Price Risk — {selected_product}",
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        height=580,
        coloraxis_colorbar=dict(title="Risk Score"),
        showlegend=False,
    )
    fig.update_traces(marker_line_width=0.5, marker_line_color="white")
    fig.update_traces(text=None)
else:
    risk_df["has_production"] = risk_df["P_norm"] > 0
    _prod_df   = risk_df[risk_df["has_production"]].copy()
    _noprod_df = risk_df[~risk_df["has_production"]].copy()

    _fig_prod = px.choropleth_mapbox(
        _prod_df,
        geojson=geojson,
        locations="City",
        featureidkey=f"properties.{name_key}",
        color="display_score",
        color_continuous_scale=COLOR_SCALE,
        range_color=(0, global_reference_max),
        mapbox_style=MAP_STYLE,
        zoom=MAP_ZOOM,
        center=MAP_CENTER,
        opacity=0.75,
        hover_data=_hover_data,
        labels=_labels,
    )

    _grey_trace = go.Choroplethmapbox(
        geojson=geojson,
        locations=_noprod_df["City"].tolist(),
        z=[0] * len(_noprod_df),
        featureidkey=f"properties.{name_key}",
        colorscale=[[0, "#cccccc"], [1, "#cccccc"]],
        showscale=False,
        marker=dict(opacity=0.75, line=dict(width=0.5, color="white")),
        text=[f"City: {c} — No recorded production for this crop." for c in _noprod_df["City"]],
        hovertemplate="%{text}<extra></extra>",
        name="No production",
    )

    fig = go.Figure(data=[_grey_trace] + list(_fig_prod.data))
    fig.update_layout(
        mapbox=_fig_prod.layout.mapbox,
        coloraxis=_fig_prod.layout.coloraxis,
        margin=dict(l=0, r=0, t=40, b=0),
        height=580,
        coloraxis_colorbar=dict(title="Risk Score"),
        showlegend=False,
        title=f"Frost Price Risk — {selected_product}",
    )
    fig.update_traces(marker_line_width=0.5, marker_line_color="white")

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Province detail panel (top 10 + selected province lookup)
# ---------------------------------------------------------------------------

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Top 10 highest-risk provinces")
    if selected_product == "All products (max risk)":
        top10 = (
            risk_df.sort_values("display_score", ascending=False)
            .head(10)[["City", "display_score", "top_crop"]]
            .reset_index(drop=True)
        )
        top10.index += 1
        st.dataframe(
            top10.rename(columns={"display_score": "Max Risk Score", "top_crop": "Top Crop"}),
            use_container_width=True,
        )
    else:
        top10 = (
            risk_df.sort_values("display_score", ascending=False)
            .head(10)[["City", "display_score", "E_norm", "S_norm", "P_norm"]]
            .reset_index(drop=True)
        )
        top10.index += 1
        st.dataframe(
            top10.rename(columns={
                "display_score": "Risk Score",
                "E_norm": "Exposure",
                "S_norm": "Sensitivity",
                "P_norm": "Prod. Share",
            }),
            use_container_width=True,
        )

with col2:
    st.subheader("Province lookup")
    cities_sorted = sorted(risk_df["City"].tolist())
    selected_city = st.selectbox("Select province", cities_sorted)
    row = risk_df[risk_df["City"] == selected_city].iloc[0]
    if selected_product == "All products (max risk)":
        st.metric("Max Risk Score", f"{row['display_score']:.1f}")
        _top_crop_display = row["top_crop"] if row["top_crop"] else "No significant risk detected"
        st.caption(f"Highest-risk crop: **{_top_crop_display}**")
    else:
        st.metric("Risk Score", f"{row['display_score']:.1f}")
        st.caption(f"Highest-risk crop: **{row['top_crop']}**")
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Exposure (E)", f"{row['E_norm']:.3f}")
        mc2.metric("Sensitivity (S)", f"{row['S_norm']:.3f}")
        mc3.metric("Production Share", f"{row['production_pct']:.1f}%")
        st.caption(f"P (normalized): {row['P_norm']:.3f} — used in risk score calculation")
        if row["flag"]:
            flag_msg = {
                "zero_response":       "Spring frost crop — winter sensitivity = 0",
                "insufficient_signal": "Insufficient frost signal — sensitivity floored at 0",
            }.get(row["flag"], row["flag"])
            st.caption(f"Flag: {flag_msg}")
