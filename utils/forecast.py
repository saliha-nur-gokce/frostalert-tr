import requests
import pandas as pd
import streamlit as st
from config import FROST_THRESHOLD, FORECAST_DAYS


def _fetch_one(lat: float, lon: float) -> list[float | None]:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":      lat,
        "longitude":     lon,
        "daily":         "temperature_2m_min",
        "forecast_days": FORECAST_DAYS,
        "timezone":      "Europe/Istanbul",
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()["daily"]["temperature_2m_min"]
    except Exception:
        return [None] * FORECAST_DAYS


@st.cache_data(ttl=21600, show_spinner=False)   # cache 6 hours
def fetch_all_forecasts(coords_df: pd.DataFrame) -> pd.DataFrame:
    """
    Fetch 16-day min temperature forecast for all 81 provinces.

    Parameters
    ----------
    coords_df : DataFrame with columns City, Latitude, Longitude

    Returns
    -------
    DataFrame with columns: City, days_below_threshold, E_raw, E_norm
        E_raw  = days < FROST_THRESHOLD / FORECAST_DAYS  (0–1)
        E_norm = min-max normalized E_raw across all provinces
    """
    rows = []
    for _, row in coords_df.iterrows():
        temps = _fetch_one(row["Latitude"], row["Longitude"])
        valid = [t for t in temps if t is not None]
        days_below = sum(1 for t in valid for _ in [t] if t < FROST_THRESHOLD)
        e_raw = days_below / FORECAST_DAYS
        rows.append({"City": row["City"], "days_below_threshold": days_below, "E_raw": e_raw})

    df = pd.DataFrame(rows)
    e_min, e_max = df["E_raw"].min(), df["E_raw"].max()
    if e_max > e_min:
        df["E_norm"] = (df["E_raw"] - e_min) / (e_max - e_min)
    else:
        df["E_norm"] = 0.0
    return df


def compute_simulated_exposure(
    coords_df: pd.DataFrame,
    frost_days: int,
) -> pd.DataFrame:
    """
    Uniform frost shock: every province gets E_norm = frost_days / FORECAST_DAYS.
    Returns DataFrame with columns: City, E_norm
    """
    e_norm = frost_days / FORECAST_DAYS
    return pd.DataFrame({"City": coords_df["City"], "E_norm": float(e_norm)})
