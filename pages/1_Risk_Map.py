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
    MAP_ZOOM, PRODUCT_BASKET, PRODUCT_DISPLAY_NAMES, SENSITIVITY_TABLE,
)
from utils.forecast import fetch_all_forecasts, compute_simulated_exposure
from utils.time_series import build_time_series_plot
from utils.risk_score import compute_historical_exposure, compute_production_norms, compute_risk_scores, compute_product_reference_max

st.set_page_config(page_title="Risk Map — FrostAlert-TR", page_icon="❄️", layout="wide")

from utils.styles import inject_global_css
inject_global_css()

st.markdown("""
<style>
table.top10-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.88em;
}
table.top10-table th {
    background-color: #1a1a1a !important;
    color: #8ab4cc !important;
    padding: 8px 10px;
    text-align: left;
    border-bottom: 1px solid #2a2a2a;
}
table.top10-table td {
    color: #e8f4f8 !important;
    padding: 7px 10px;
    border-bottom: 1px solid #1a1a1a;
}
table.top10-table tr:hover td {
    background-color: #1a1a1a;
}
</style>
""", unsafe_allow_html=True)

if "selected_product_key" not in st.session_state:
    st.session_state["selected_product_key"] = "All products (max risk)"
if "selected_city_key" not in st.session_state:
    st.session_state["selected_city_key"] = None

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
    import json
    cache_path = Path(__file__).parent.parent / "data" / "global_ref_max.json"
    if cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)["value"]
    _seasons = [
        "2014–2024 average",
        "2014–2015", "2015–2016", "2016–2017", "2017–2018",
        "2018–2019", "2019–2020", "2020–2021", "2021–2022",
        "2022–2023", "2023–2024", "2024–2025 (partial)",
    ]
    _prod_norm = compute_production_norms(_main_df)
    _all_scores: list[float] = []
    for _season in _seasons:
        _exp = compute_historical_exposure(_main_df, _season)
        for _p in PRODUCT_BASKET:
            _all_scores.extend(
                compute_risk_scores(_exp, _prod_norm, _p)["risk_score"].tolist()
            )
    result = max(max(_all_scores) if _all_scores else 0.1, 0.1)
    cache_path.parent.mkdir(exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump({"value": result}, f)
    return result


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


def _risk_color(score: float, max_score: float) -> str:
    """Interpolate from dark yellow (#ffd944) to deep red (#dc2626) based on score/max_score ratio."""
    if max_score <= 0:
        return "#ffd944"
    t = min(score / max_score, 1.0)
    r = int(255 + (220 - 255) * t)
    g = int(217 + (38  - 217) * t)
    b = int(68  + (38  - 68)  * t)
    return f"#{r:02x}{g:02x}{b:02x}"


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

st.markdown("""
<div style='font-size:2.2em;font-weight:900;letter-spacing:-0.5px;margin-bottom:0.5em;line-height:1.1'>
<span style='color:#ffffff'>FROST RISK</span><br>
<span style='color:#7ec8e3'>MAP</span>
</div>
""", unsafe_allow_html=True)

_DISPLAY_OPTIONS = ["All products (max risk)"] + [PRODUCT_DISPLAY_NAMES.get(p, p) for p in PRODUCT_BASKET]
_REVERSE_DISPLAY_MAP = {PRODUCT_DISPLAY_NAMES.get(p, p): p for p in PRODUCT_BASKET}

_col_product, _col_mode = st.columns([1, 2])
with _col_product:
    def _on_product_change_top():
        _dv = st.session_state["_product_top"]
        st.session_state["selected_product_key"] = _REVERSE_DISPLAY_MAP.get(_dv, _dv)

    _cur_display = PRODUCT_DISPLAY_NAMES.get(
        st.session_state["selected_product_key"],
        st.session_state["selected_product_key"],
    )
    selected_product_display = st.selectbox(
        "Product",
        _DISPLAY_OPTIONS,
        key="_product_top",
        index=_DISPLAY_OPTIONS.index(_cur_display),
        on_change=_on_product_change_top,
    )
    selected_product = _REVERSE_DISPLAY_MAP.get(selected_product_display, selected_product_display)
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
        [
            "2014–2024 average",
            "2014–2015", "2015–2016", "2016–2017", "2017–2018",
            "2018–2019", "2019–2020", "2020–2021", "2021–2022",
            "2022–2023", "2023–2024", "2024–2025 (partial)",
        ],
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
    if info["flag"] == "zero_response":
        st.markdown(f"""
<div style="background:#1a1a0a;border-left:4px solid #ffd944;padding:12px 16px;
border-radius:4px;margin-bottom:12px;color:#e8f4f8">
<b>⚠ Spring frost crop</b><br>
<span style="font-size:0.92em">{PRODUCT_DISPLAY_NAMES.get(selected_product, selected_product)} is dormant in winter (Nov–Mar).
No price effect detected in this window. Critical risk period: <b>April–May</b>.</span>
</div>
""", unsafe_allow_html=True)
    elif info["flag"] == "insufficient_signal":
        st.markdown(f"""
<div style="background:#0a1628;border-left:4px solid #7ec8e3;padding:12px 16px;
border-radius:4px;margin-bottom:12px;color:#e8f4f8">
<b>ℹ Insufficient frost signal</b><br>
<span style="font-size:0.92em">Lag1 coefficient is negative for {PRODUCT_DISPLAY_NAMES.get(selected_product, selected_product)},
likely due to harvest-season inventory effects. Price sensitivity set to 0.</span>
</div>
""", unsafe_allow_html=True)

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

_ref_cache = Path(__file__).parent.parent / "data" / "global_ref_max.json"
if not _ref_cache.exists():
    with st.spinner("Initializing color scale (first run only)…"):
        global_reference_max = compute_global_reference_max(main_df)
else:
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

if selected_product != "All products (max risk)":
    product_reference_max = compute_product_reference_max(main_df, selected_product)
else:
    product_reference_max = global_reference_max

if mode == "🌡️ Live forecast (16-day)":
    icon, border_color, msg = "🌡️", "#7ec8e3", f"<b style='color:#ffffff'>Forecast window:</b> {_today:%d %b %Y} → {_forecast_end:%d %b %Y} (16 days) · Source: Open-Meteo · Cache: 6h · Max risk score: <b style='color:#ffffff'>{max_score:.1f}</b>"
elif mode == "📊 Historical exposure (2022–2024 winter avg)":
    icon, border_color, msg = "📊", "#4ade80", f"<b style='color:#ffffff'>Historical exposure:</b> {hist_season} · Max risk score: <b style='color:#ffffff'>{max_score:.1f}</b>"
else:
    icon, border_color, msg = "⚠️", "#ffd944", f"<b style='color:#ffffff'>Simulation:</b> {sim_frost_days}-day uniform frost shock · Max risk score: <b style='color:#ffffff'>{max_score:.1f}</b>"

st.markdown(f"""
<div style="background:#162236;border-left:4px solid {border_color};border-radius:4px;padding:10px 16px;margin-bottom:8px;color:#e8f4f8">
{icon} {msg}
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Choropleth map
# ---------------------------------------------------------------------------

risk_df = risk_df.rename(columns={"risk_score": "display_score"})
cities_sorted = sorted(risk_df["City"].tolist())

if selected_product == "All products (max risk)":
    risk_df["top_crop_label"] = risk_df["top_crop"].apply(
        lambda x: x if x else "No significant risk detected"
    )
    _hover_data = {"City": True, "display_score": ":.2f", "top_crop_label": True}
    _labels = {"display_score": "Max Risk Score", "top_crop_label": "Highest-risk crop"}
else:
    _hover_data = {
        "City": True, "display_score": ":.2f",
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
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#0a0a0a",
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
        range_color=(0, product_reference_max),
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
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#0a0a0a",
        coloraxis_colorbar=dict(title="Risk Score"),
        showlegend=False,
        title=f"Frost Price Risk — {PRODUCT_DISPLAY_NAMES.get(selected_product, selected_product)}",
    )
    fig.update_traces(marker_line_width=0.5, marker_line_color="white")

_highlight_city = st.session_state["selected_city_key"]
if _highlight_city is not None:
    _highlight_row = risk_df[risk_df["City"] == _highlight_city]
if _highlight_city is not None and not _highlight_row.empty:
    _highlight_trace = go.Choroplethmapbox(
        geojson=geojson,
        locations=[_highlight_city],
        z=[0],
        featureidkey=f"properties.{name_key}",
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
        showscale=False,
        marker=dict(
            opacity=1.0,
            line=dict(width=3, color="#FFD700")
        ),
        hoverinfo="skip",
        name="Selected province",
        showlegend=False,
    )
    fig.add_trace(_highlight_trace)

map_selection = st.plotly_chart(
    fig,
    use_container_width=True,
    on_select="rerun",
    key="choropleth_map",
)
if map_selection and map_selection.selection and map_selection.selection.points:
    clicked_city = map_selection.selection.points[0].get("location")
    if clicked_city and clicked_city in cities_sorted:
        st.session_state["selected_city_key"] = clicked_city
        st.session_state["_city_select"] = clicked_city
        st.rerun()

# ---------------------------------------------------------------------------
# Province detail panel (top 10 + selected province lookup)
# ---------------------------------------------------------------------------

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("<h3 style='color:#ffd944;font-weight:700;margin-bottom:8px'>Top 10 highest-risk provinces</h3>", unsafe_allow_html=True)
    if selected_product == "All products (max risk)":
        top10 = (
            risk_df.sort_values("display_score", ascending=False)
            .head(10)[["City", "display_score", "top_crop"]]
            .reset_index(drop=True)
        )
        top10.index += 1
        _rows_html = ""
        for _rank, _r in top10.iterrows():
            _score = _r["display_score"]
            _color = _risk_color(_score, max_score)
            _crop_disp = PRODUCT_DISPLAY_NAMES.get(_r["top_crop"], _r["top_crop"])
            _rows_html += (
                f"<tr>"
                f"<td style='color:#8ab4cc'>{_rank}</td>"
                f"<td>{_r['City']}</td>"
                f"<td style='background:linear-gradient(90deg,{_color}22 0%,transparent 100%);"
                f"color:{_color};font-weight:600'>{_score:.2f}</td>"
                f"<td>{_crop_disp}</td>"
                f"</tr>"
            )
        _tbl_html = (
            "<table class='top10-table'>"
            "<thead><tr>"
            "<th style='color:#ffd944'>#</th>"
            "<th style='color:#ffd944'>City</th>"
            "<th style='color:#ff6b6b'>Max Risk Score</th>"
            "<th style='color:#ffd944'>Top Crop</th>"
            "</tr></thead>"
            f"<tbody>{_rows_html}</tbody>"
            "</table>"
        )
        st.markdown(_tbl_html, unsafe_allow_html=True)
    else:
        top10 = (
            risk_df.sort_values("display_score", ascending=False)
            .head(10)[["City", "display_score", "E_norm", "P_norm"]]
            .reset_index(drop=True)
        )
        top10.index += 1
        _rows_html = ""
        for _rank, _r in top10.iterrows():
            _score = _r["display_score"]
            _color = _risk_color(_score, max_score)
            _rows_html += (
                f"<tr>"
                f"<td style='color:#8ab4cc'>{_rank}</td>"
                f"<td>{_r['City']}</td>"
                f"<td style='background:linear-gradient(90deg,{_color}22 0%,transparent 100%);"
                f"color:{_color};font-weight:600'>{_score:.2f}</td>"
                f"<td>{_r['E_norm']:.3f}</td>"
                f"<td>{_r['P_norm']:.3f}</td>"
                f"</tr>"
            )
        _tbl_html = (
            "<table class='top10-table'>"
            "<thead><tr>"
            "<th style='color:#ffd944'>#</th>"
            "<th style='color:#ffd944'>City</th>"
            "<th style='color:#ff6b6b'>Risk Score</th>"
            "<th style='color:#ffd944'>Exposure</th>"
            "<th style='color:#ffd944'>Prod. Share</th>"
            "</tr></thead>"
            f"<tbody>{_rows_html}</tbody>"
            "</table>"
        )
        st.markdown(_tbl_html, unsafe_allow_html=True)

with col2:
    st.subheader("Province lookup")
    def _on_city_change():
        st.session_state["selected_city_key"] = st.session_state["_city_select"]

    selected_city = st.selectbox(
        "Select province",
        cities_sorted,
        key="_city_select",
        index=cities_sorted.index(st.session_state["selected_city_key"])
            if st.session_state["selected_city_key"] in cities_sorted else 0,
        on_change=_on_city_change,
    )
    _display_city = st.session_state["selected_city_key"] if st.session_state["selected_city_key"] in cities_sorted else selected_city
    row = risk_df[risk_df["City"] == _display_city].iloc[0]
    if selected_product == "All products (max risk)":
        st.metric("Max Risk Score", f"{row['display_score']:.1f}")
        _top_crop_display = PRODUCT_DISPLAY_NAMES.get(row["top_crop"], row["top_crop"]) if row["top_crop"] else "No significant risk detected"
        st.caption(f"Highest-risk crop: **{_top_crop_display}**")
    else:
        st.metric("Risk Score", f"{row['display_score']:.1f}")
        st.caption(f"Selected crop: **{PRODUCT_DISPLAY_NAMES.get(selected_product, selected_product)}**")
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

st.markdown("---")
st.subheader("Price & Temperature History")

def _on_product_change_bottom():
    _dv = st.session_state["_product_bottom"]
    st.session_state["selected_product_key"] = _REVERSE_DISPLAY_MAP.get(_dv, _dv)

_cur_bottom_display = PRODUCT_DISPLAY_NAMES.get(
    st.session_state["selected_product_key"],
    st.session_state["selected_product_key"],
)
st.selectbox(
    "Product (select here or at the top of the page)",
    _DISPLAY_OPTIONS,
    key="_product_bottom",
    index=_DISPLAY_OPTIONS.index(_cur_bottom_display),
    on_change=_on_product_change_bottom,
)
_active_city = st.session_state.get("selected_city_key") or selected_city
st.caption(f"Province: **{_active_city}** — change via the Province lookup panel above ↑")

if st.session_state["selected_product_key"] == "All products (max risk)":
    st.info(
        f"Select a specific product from the dropdown above to view the "
        f"price and temperature history for **{_active_city}**.",
        icon="📈"
    )
else:
    _REVERSE_MAP = {v: k for k, v in PRODUCT_DISPLAY_NAMES.items()}
    _active_product_key = _REVERSE_MAP.get(st.session_state["selected_product_key"], st.session_state["selected_product_key"])
    with st.spinner("Loading time series…"):
        fig_ts = build_time_series_plot(main_df, _active_city, _active_product_key)
    city_row = risk_df[risk_df["City"] == _active_city]
    if not city_row.empty and city_row.iloc[0]["E_norm"] == 0:
        st.info(
            f"**{selected_city}** has no recorded frost exposure for the selected period. "
            "The time series shows price history only — no frost events expected.",
            icon="ℹ️"
        )
    st.plotly_chart(fig_ts, use_container_width=True)
    st.caption(
        "Full 2014–2024 monthly record. Red triangles mark frost events "
        "(min_temp < –2°C). Price data availability varies by province and product."
    )
