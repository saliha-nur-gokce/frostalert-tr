import numpy as np
import pandas as pd
import streamlit as st
from pathlib import Path
from config import SENSITIVITY_TABLE, HISTORICAL_YEARS, EXPOSURE_YEARS_FULL, WINTER_MONTHS, FROST_THRESHOLD, PRODUCT_FILTER_MAP


@st.cache_data(show_spinner=False)
def compute_sensitivity_norms() -> dict[str, float]:
    """
    Min-max normalize Sj values across non-flagged products only.
    Flagged products → Sj_norm = 0.0.
    """
    unflagged = {k: v["sj"] for k, v in SENSITIVITY_TABLE.items() if v["flag"] is None}
    if not unflagged:
        return {k: 0.0 for k in SENSITIVITY_TABLE}

    sj_min = min(unflagged.values())
    sj_max = max(unflagged.values())
    span = sj_max - sj_min if sj_max > sj_min else 1.0

    norms: dict[str, float] = {}
    for product, info in SENSITIVITY_TABLE.items():
        if info["flag"] is not None:
            norms[product] = 0.0
        else:
            norms[product] = (info["sj"] - sj_min) / span
    return norms


_SEASON_FILTERS: dict[str, list[tuple[int, int]] | str] = {
    "2014–2024 average":       "full",
    "2014–2015":               [(2014, 11), (2014, 12), (2015, 1), (2015, 2), (2015, 3)],
    "2015–2016":               [(2015, 11), (2015, 12), (2016, 1), (2016, 2), (2016, 3)],
    "2016–2017":               [(2016, 11), (2016, 12), (2017, 1), (2017, 2), (2017, 3)],
    "2017–2018":               [(2017, 11), (2017, 12), (2018, 1), (2018, 2), (2018, 3)],
    "2018–2019":               [(2018, 11), (2018, 12), (2019, 1), (2019, 2), (2019, 3)],
    "2019–2020":               [(2019, 11), (2019, 12), (2020, 1), (2020, 2), (2020, 3)],
    "2020–2021":               [(2020, 11), (2020, 12), (2021, 1), (2021, 2), (2021, 3)],
    "2021–2022":               [(2021, 11), (2021, 12), (2022, 1), (2022, 2), (2022, 3)],
    "2022–2023":               [(2022, 11), (2022, 12), (2023, 1), (2023, 2), (2023, 3)],
    "2023–2024":               [(2023, 11), (2023, 12), (2024, 1), (2024, 2), (2024, 3)],
    "2024–2025 (partial)":     [(2024, 11), (2024, 12)],
}


@st.cache_data(show_spinner=False)
def compute_historical_exposure(_df: pd.DataFrame, season: str = "2022–2024 average") -> pd.DataFrame:
    """
    Historical E_i: fraction of winter months with min_temp < FROST_THRESHOLD.
    season controls the year/month window (see _SEASON_FILTERS).
    Drops product-level duplicates so each city-date is counted once.
    Returns DataFrame with columns: City, E_norm
    """
    ym_pairs = _SEASON_FILTERS.get(season)
    if ym_pairs == "full":
        hist = _df[
            _df["Year"].isin(EXPOSURE_YEARS_FULL) & _df["Month"].isin(WINTER_MONTHS)
        ].copy()
    else:
        mask = pd.Series(False, index=_df.index)
        for y, m in ym_pairs:
            mask |= (_df["Year"] == y) & (_df["Month"] == m)
        hist = _df[mask].copy()

    hist = hist.drop_duplicates(subset=["City", "date"])
    hist["frost_shock"] = (hist["min_temp"] < FROST_THRESHOLD).astype(int)

    city_stats = (
        hist.groupby("City")
        .agg(total_months=("frost_shock", "count"), frost_months=("frost_shock", "sum"))
        .reset_index()
    )
    city_stats["E_raw"] = city_stats["frost_months"] / city_stats["total_months"].clip(lower=1)

    e_min = city_stats["E_raw"].min()
    e_max = city_stats["E_raw"].max()
    span = e_max - e_min if e_max > e_min else 1.0
    city_stats["E_norm"] = (city_stats["E_raw"] - e_min) / span

    return city_stats[["City", "E_norm"]]


@st.cache_data(show_spinner=False)
def compute_production_norms(_df: pd.DataFrame) -> pd.DataFrame:
    """
    Hybrid two-stage normalization for P_ij (province × product production share).

    Stage 1: national_share = product's total production / all basket products' total
    Stage 2: city_share_within = city's production of product / product's national total
    Combined: P_combined = national_share × city_share_within
    Final: global min-max normalize P_combined → P_norm

    Returns DataFrame with columns: City, product, P_norm
    """
    hist = _df[_df["Year"].isin(HISTORICAL_YEARS)].copy()

    rows = []
    for product, filt in PRODUCT_FILTER_MAP.items():
        prod_df = hist[hist["Product_Name"].str.contains(filt, na=False, regex=False)]
        if prod_df.empty:
            continue
        by_city = (
            prod_df.groupby("City")["Production_Quantity"]
            .mean()
            .reset_index()
            .rename(columns={"Production_Quantity": "city_prod"})
        )
        national_total = by_city["city_prod"].sum()
        if national_total == 0:
            continue
        by_city["national_share"] = national_total / max(1, national_total)  # placeholder; computed below
        by_city["city_share_within"] = by_city["city_prod"] / national_total
        by_city["product"] = product
        rows.append(by_city)

    if not rows:
        return pd.DataFrame(columns=["City", "product", "P_norm"])

    combined = pd.concat(rows, ignore_index=True)

    # national_share: product total vs all basket totals
    product_totals = combined.groupby("product")["city_prod"].sum()
    basket_total = product_totals.sum()
    combined["national_share"] = combined["product"].map(product_totals) / max(1, basket_total)
    combined["P_combined"] = combined["national_share"] * combined["city_share_within"]

    p_min = combined["P_combined"].min()
    p_max = combined["P_combined"].max()
    span = p_max - p_min if p_max > p_min else 1.0
    combined["P_norm"] = (combined["P_combined"] - p_min) / span

    return combined[["City", "product", "P_norm", "city_share_within"]]


def compute_risk_scores(
    exposure_df: pd.DataFrame,
    production_norm_df: pd.DataFrame,
    product: str,
) -> pd.DataFrame:
    """
    Compute risk scores for a single product across all 81 provinces.

    Parameters
    ----------
    exposure_df       : output of fetch_all_forecasts(), has City + E_norm
    production_norm_df: output of compute_production_norms(), has City + product + P_norm
    product           : product short name (key in SENSITIVITY_TABLE)

    Returns
    -------
    DataFrame: City, E_norm, S_norm, P_norm, risk_score, flag
    """
    sj_norms = compute_sensitivity_norms()
    s_norm = sj_norms.get(product, 0.0)
    flag = SENSITIVITY_TABLE[product]["flag"]

    prod_p = production_norm_df[production_norm_df["product"] == product][["City", "P_norm", "city_share_within"]]

    result = exposure_df[["City", "E_norm"]].merge(prod_p, on="City", how="left")
    result["P_norm"] = result["P_norm"].fillna(0.0)
    result["city_share_within"] = result["city_share_within"].fillna(0.0)
    result["production_pct"] = (result["city_share_within"] * 100).round(1)

    result["S_norm"] = s_norm
    result["flag"] = flag

    result["risk_raw"] = result["E_norm"] * result["S_norm"] * result["P_norm"]
    result["risk_score"] = (result["risk_raw"] * 100).round(2)

    return result


@st.cache_data(show_spinner=False)
def compute_product_reference_max(_df: pd.DataFrame, product: str) -> float:
    import json
    cache_path = Path(__file__).parent.parent / "data" / f"ref_max_{product}.json"
    if cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)["value"]
    all_seasons = [
        "2014–2024 average",
        "2014–2015", "2015–2016", "2016–2017", "2017–2018",
        "2018–2019", "2019–2020", "2020–2021", "2021–2022",
        "2022–2023", "2023–2024", "2024–2025 (partial)",
    ]
    prod_norm = compute_production_norms(_df)
    all_scores: list[float] = []
    for season in all_seasons:
        exp = compute_historical_exposure(_df, season)
        scores = compute_risk_scores(exp, prod_norm, product)["risk_score"].tolist()
        all_scores.extend(scores)
    result = max(max(all_scores) if all_scores else 0.1, 0.1)
    cache_path.parent.mkdir(exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump({"value": result}, f)
    return result
