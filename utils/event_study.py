import numpy as np
import pandas as pd
import plotly.graph_objects as go
from config import FROST_THRESHOLD, PRODUCT_FILTER_MAP


def find_worst_frost_event(df: pd.DataFrame, city: str, product: str) -> tuple[int, int] | None:
    """
    Identify the month with the lowest min_temp below FROST_THRESHOLD for a
    given city-product combination.

    Returns (year, month) of the worst event, or None if no frost event found.
    """
    filt = PRODUCT_FILTER_MAP.get(product, product)
    sub = df[
        (df["City"] == city)
        & (df["Product_Name"].str.contains(filt, na=False, regex=False))
        & (df["min_temp"] < FROST_THRESHOLD)
        & (df["Real_Price"].notna())
    ].copy()

    if sub.empty:
        return None

    # aggregate across product varieties if multiple match
    monthly = sub.groupby(["Year", "Month"])["min_temp"].min().reset_index()
    idx = monthly["min_temp"].idxmin()
    row = monthly.loc[idx]
    return int(row["Year"]), int(row["Month"])


def build_event_study_plot(
    df: pd.DataFrame,
    city: str,
    product: str,
    event_year: int,
    event_month: int,
    window: int = 3,
) -> go.Figure:
    """
    Plot real price ±window months around the frost event for the given city-product.
    """
    filt = PRODUCT_FILTER_MAP.get(product, product)
    sub = df[
        (df["City"] == city)
        & (df["Product_Name"].str.contains(filt, na=False, regex=False))
    ].copy()

    if sub.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available for this selection.", showarrow=False)
        return fig

    import streamlit as st
    st.write(f"DEBUG — rows before groupby: {len(sub)}, city={city}, product={product}")
    # aggregate across product varieties
    sub = sub.groupby(["Year", "Month"])["Real_Price"].mean().reset_index()
    sub["date"] = pd.to_datetime(sub[["Year", "Month"]].assign(day=1))
    sub = sub.sort_values("date")

    event_date = pd.Timestamp(year=event_year, month=event_month, day=1)
    if sub["date"].dt.tz is not None:
        event_date = event_date.tz_localize(sub["date"].dt.tz)
    st.write(f"DEBUG2 — date dtype: {sub['date'].dtype}, sample: {sub['date'].iloc[0]}, event_date type: {type(event_date)}, event_date: {event_date}")
    st.write(f"DEBUG2 — comparison test: {sub['date'].iloc[0] >= event_date - pd.DateOffset(months=window)}")
    st.write(f"DEBUG3 — dates in window range: {sub[(sub['date'] >= '2022-11-01') & (sub['date'] <= '2023-05-01')][['Year','Month','date']]}")
    mask = (sub["date"] >= event_date - pd.DateOffset(months=window)) & \
           (sub["date"] <= event_date + pd.DateOffset(months=window))
    window_df = sub[mask].copy()

    st.write(f"DEBUG — event_date={event_date}, window_df rows={len(window_df)}, date range: {sub['date'].min()} to {sub['date'].max()}")
    if window_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Not enough data around the event date.", showarrow=False)
        return fig

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=window_df["date"],
        y=window_df["Real_Price"],
        mode="lines+markers",
        name="Real Price (TL/kg)",
        line=dict(color="#E07B39", width=2),
        marker=dict(size=7),
    ))

    fig.add_vline(
        x=event_date.timestamp() * 1000,
        line_dash="dash",
        line_color="#C0392B",
        annotation_text=f"Frost event\n{event_month}/{event_year}",
        annotation_position="top right",
    )

    fig.update_layout(
        title=f"Price around frost event — {city} / {product}",
        xaxis_title="Date",
        yaxis_title="Real Price (TL/kg, Jan 2024 base)",
        template="plotly_white",
        height=400,
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig
