import pandas as pd
import plotly.graph_objects as go
from config import FROST_THRESHOLD, PRODUCT_FILTER_MAP


def build_time_series_plot(df: pd.DataFrame, city: str, product: str) -> go.Figure:
    """
    Full 2014–2024 dual-axis time series for a city-product combination.
    Left axis: Real Price (TL/kg, deflated) — red solid line
    Right axis: min_temp (°C) — blue dashed line
    Frost zone: fill_between where min_temp < 0, blue, alpha=0.12
    Frost events: scatter markers (triangle-down, red) where min_temp < FROST_THRESHOLD
    Horizontal line at y=0 on temp axis (black, linewidth=0.5)
    Horizontal line at y=FROST_THRESHOLD on temp axis (red dashed, linewidth=0.8,
      label="–2°C threshold")
    """
    filt = PRODUCT_FILTER_MAP.get(product, product)
    sub = df[
        (df["City"] == city)
        & (df["Product_Name"].str.contains(filt, na=False, regex=False))
    ].copy()

    if sub.empty:
        fig = go.Figure()
        fig.add_annotation(
            text=f"No data available for {city} / {product}",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=14, color="#8ab4cc"),
        )
        fig.update_layout(
            paper_bgcolor="#0a0a0a",
            plot_bgcolor="#111111",
            font=dict(color="#8ab4cc"),
        )
        return fig

    sub = (
        sub.groupby(["Year", "Month"])
        .agg(Real_Price=("Real_Price", "mean"), min_temp=("min_temp", "min"))
        .reset_index()
    )
    sub["date"] = pd.to_datetime(sub[["Year", "Month"]].assign(day=1))
    sub = sub.sort_values("date").reset_index(drop=True)
    sub = sub.dropna(subset=["Real_Price", "min_temp"], how="all")

    if sub.empty:
        fig = go.Figure()
        fig.add_annotation(
            text=f"No data available for {city} / {product}",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=14, color="#8ab4cc"),
        )
        fig.update_layout(
            paper_bgcolor="#0a0a0a",
            plot_bgcolor="#111111",
            font=dict(color="#8ab4cc"),
        )
        return fig

    temp_min = sub["min_temp"].min()
    y2_min = min(temp_min, FROST_THRESHOLD) - 2
    y2_max = sub["min_temp"].max() + 2

    dates = sub["date"].tolist()
    prices = sub["Real_Price"].tolist()
    temps = sub["min_temp"].tolist()

    frost_mask = sub["min_temp"] < FROST_THRESHOLD
    frost_dates = sub.loc[frost_mask, "date"].tolist()
    frost_temps = sub.loc[frost_mask, "min_temp"].tolist()

    fig = go.Figure()

    # 1. Frost zone fill
    fig.add_trace(go.Scatter(
        x=dates,
        y=[t if t < 0 else 0 for t in temps],
        fill="tozeroy",
        fillcolor="rgba(126,200,227,0.10)",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip",
        yaxis="y2",
    ))

    # 2. Min temp line
    fig.add_trace(go.Scatter(
        x=dates,
        y=temps,
        mode="lines+markers",
        name="Min Temp (°C)",
        line=dict(color="#7ec8e3", dash="dash", width=1.5),
        marker=dict(size=4),
        yaxis="y2",
        opacity=0.85,
    ))

    # 3. Frost event markers
    fig.add_trace(go.Scatter(
        x=frost_dates,
        y=frost_temps,
        mode="markers",
        name="Frost event (< –2°C)",
        marker=dict(symbol="triangle-down", color="#ff6b6b", size=9, opacity=0.9),
        yaxis="y2",
    ))

    # 4. Price line
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        mode="lines+markers",
        name="Real Price (TL/kg)",
        line=dict(color="#ffd944", width=2.5),
        marker=dict(size=5),
    ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#111111",
        height=380,
        title=f"Price & Temperature History — {city} / {product} (2014–2024)",
        title_font=dict(color="#8ab4cc"),
        font=dict(color="#e8f4f8"),
        dragmode=False,
        margin=dict(l=50, r=70, t=50, b=50),
        legend=dict(orientation="h", y=-0.15, x=0, font=dict(color="#e8f4f8")),
        shapes=[
            dict(
                type="line",
                xref="paper", x0=0, x1=1,
                yref="y2", y0=FROST_THRESHOLD, y1=FROST_THRESHOLD,
                line=dict(color="#a78bfa", dash="dash", width=0.8),
            )
        ],
        annotations=[
            dict(
                x=1.01, xref="paper",
                y=FROST_THRESHOLD, yref="y2",
                text="–2°C",
                showarrow=False,
                font=dict(size=10, color="#a78bfa"),
                xanchor="left",
            )
        ],
        xaxis=dict(
            title=None,
            tickformat="%Y-%b",
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
            title="Min Temp (°C)",
            overlaying="y",
            side="right",
            title_font=dict(color="#8ab4cc"),
            tickfont=dict(color="#8ab4cc"),
            range=[y2_min, y2_max],
            zeroline=True,
            zerolinecolor="rgba(255,255,255,0.2)",
            zerolinewidth=0.5,
            fixedrange=True,
            gridcolor="rgba(255,255,255,0.06)",
        ),
    )

    return fig
