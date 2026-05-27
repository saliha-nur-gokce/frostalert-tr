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
    Dual-axis event study plot: Real_Price (left) and min_temp (right)
    centered on a frost shock event.
    """
    filt = PRODUCT_FILTER_MAP.get(product, product)
    sub = df[
        (df["City"] == city)
        & (df["Product_Name"].str.contains(filt, na=False, regex=False))
    ].copy()

    if sub.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient price data for this city–product combination.",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=14),
        )
        return fig

    # aggregate across product varieties
    sub = (
        sub.groupby(["Year", "Month"])
        .agg(Real_Price=("Real_Price", "mean"), min_temp=("min_temp", "min"))
        .reset_index()
    )
    sub["date"] = pd.to_datetime(sub[["Year", "Month"]].assign(day=1))
    sub = sub.sort_values("date").reset_index(drop=True)

    event_date = pd.Timestamp(year=event_year, month=event_month, day=1)

    mask = (
        (sub["date"] >= event_date - pd.DateOffset(months=window))
        & (sub["date"] <= event_date + pd.DateOffset(months=window))
    )
    window_df = sub[mask].copy().reset_index(drop=True)

    if window_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient price data for this city–product combination.",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=14),
        )
        return fig

    dates = window_df["date"].tolist()
    prices = window_df["Real_Price"].tolist()
    temps = window_df["min_temp"].tolist()

    # frost fill: min_temp below 0
    frost_y_upper = [min(t, 0) for t in temps]  # cap at 0 for fill region
    frost_y_lower = [t if t < 0 else 0 for t in temps]

    fig = go.Figure()

    # frost zone fill (right axis scale, drawn first so it sits behind)
    fig.add_trace(go.Scatter(
        x=dates + dates[::-1],
        y=frost_y_upper + frost_y_lower[::-1],
        fill="toself",
        fillcolor="rgba(126, 200, 227, 0.12)",
        line=dict(width=0),
        hoverinfo="skip",
        showlegend=False,
        yaxis="y2",
    ))

    # min_temp line (right axis)
    fig.add_trace(go.Scatter(
        x=dates,
        y=temps,
        mode="lines+markers",
        name="Min Temp (°C)",
        line=dict(color="#7ec8e3", width=1.5, dash="dash"),
        marker=dict(size=5, color="#7ec8e3"),
        yaxis="y2",
    ))

    # Real_Price line (left axis)
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        mode="lines+markers",
        name="Real Price (TL/kg)",
        line=dict(color="#ffd944", width=2.5),
        marker=dict(size=7, color="#ffd944"),
        yaxis="y1",
    ))

    # horizontal 0°C line on right axis
    fig.add_hline(
        y=0,
        line=dict(color="rgba(255,255,255,0.2)", width=0.5),
        yref="y2",
    )

    # FROST_THRESHOLD line on right axis
    fig.add_hline(
        y=FROST_THRESHOLD,
        line=dict(color="#a78bfa", width=0.8, dash="dash"),
        annotation_text=f"–2°C threshold",
        annotation_position="bottom right",
        annotation_font=dict(size=10, color="#a78bfa"),
        yref="y2",
    )

    # vertical shock line
    event_ts = event_date.timestamp() * 1000
    fig.add_vline(
        x=event_ts,
        line=dict(color="#ff6b6b", width=2),
    )

    # annotation box: place right if event is in first half of window, left otherwise
    event_idx = window_df[window_df["date"] == event_date].index
    if len(event_idx) > 0:
        min_temp_val = window_df.loc[event_idx[0], "min_temp"]
    else:
        min_temp_val = float("nan")

    event_position_frac = (event_date - window_df["date"].min()) / (
        window_df["date"].max() - window_df["date"].min()
    ) if len(window_df) > 1 else 0.5

    xanchor = "left" if event_position_frac <= 0.5 else "right"
    ax_offset = 40 if event_position_frac <= 0.5 else -40

    temp_str = f"{min_temp_val:.1f}°C" if not np.isnan(min_temp_val) else "N/A"

    fig.add_annotation(
        x=event_date.strftime("%Y-%m-%d"),
        y=min_temp_val,
        xref="x",
        yref="y2",
        text=f"SHOCK EVENT<br>{event_year}-{event_month:02d}<br>{temp_str}",
        showarrow=True,
        arrowhead=2,
        ax=ax_offset,
        ay=-40,
        bgcolor="#0f1c2e",
        bordercolor="#ff6b6b",
        borderwidth=1,
        font=dict(size=11, color="#e8f4f8", family="monospace"),
        xanchor=xanchor,
    )

    # earlier frost markers (min_temp < FROST_THRESHOLD, excluding event_date)
    earlier_frost = window_df[
        (window_df["min_temp"] < FROST_THRESHOLD) & (window_df["date"] != event_date)
    ]
    if not earlier_frost.empty:
        fig.add_trace(go.Scatter(
            x=earlier_frost["date"].tolist(),
            y=earlier_frost["min_temp"].tolist(),
            mode="markers",
            name="Earlier frost month",
            marker=dict(symbol="triangle-down", color="#ff6b6b", size=10, opacity=0.85),
            yaxis="y2",
        ))

    # x-axis tick formatting
    tickvals = [d.timestamp() * 1000 for d in dates]
    ticktext = [d.strftime("%Y-%b") for d in dates]

    fig.update_layout(
        title=f"Event Study: Frost Shock Impact on {product} Prices — {city}",
        title_font=dict(color="#8ab4cc"),
        font=dict(color="#e8f4f8"),
        template="plotly_dark",
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#111111",
        height=480,
        margin=dict(l=50, r=60, t=55, b=50),
        legend=dict(orientation="h", y=-0.15, x=0, font=dict(color="#e8f4f8")),
        dragmode=False,
        xaxis=dict(
            tickvals=tickvals,
            ticktext=ticktext,
            tickangle=-30,
            fixedrange=True,
            gridcolor="rgba(255,255,255,0.06)",
            title_font=dict(color="#8ab4cc"),
            tickfont=dict(color="#8ab4cc"),
        ),
        yaxis=dict(
            title="Real Price (TL/kg, deflated)",
            title_font=dict(color="#8ab4cc"),
            tickfont=dict(color="#8ab4cc"),
            fixedrange=True,
            gridcolor="rgba(255,255,255,0.06)",
        ),
        yaxis2=dict(
            title="Min Temperature (°C)",
            title_font=dict(color="#8ab4cc"),
            tickfont=dict(color="#8ab4cc"),
            overlaying="y",
            side="right",
            fixedrange=True,
            gridcolor="rgba(255,255,255,0.06)",
        ),
    )

    return fig
