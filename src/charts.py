"""Plotly charts aligned with Tactical Obsidian palette."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# DESIGN.md tokens
ON_SURFACE = "#e5e2e1"
SURFACE_HIGH = "#2a2a2a"
PRIMARY = "#2962ff"
SECONDARY = "#40e56c"
MUTED = "rgba(229, 226, 225, 0.45)"


def price_oi_figure(df: pd.DataFrame, title: str) -> go.Figure:
    """Close price with optional open-interest subplot when OI has signal."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#131313",
            plot_bgcolor="#1c1b1b",
            font=dict(color=ON_SURFACE, family="Inter, sans-serif", size=12),
            title=dict(text=title, font=dict(size=16)),
            margin=dict(l=48, r=24, t=48, b=48),
        )
        fig.add_annotation(
            text="No candle data returned for this contract and range.",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(color=MUTED),
        )
        return fig

    has_oi = df["oi"].notna() & (df["oi"].astype(float).abs() > 0)

    if has_oi.any():
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.06,
            row_heights=[0.62, 0.38],
        )
        fig.add_trace(
            go.Scatter(
                x=df["time"],
                y=df["close"],
                mode="lines",
                name="Close",
                line=dict(color=PRIMARY, width=2),
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Bar(
                x=df["time"],
                y=df["oi"],
                name="Open interest",
                marker_color=SECONDARY,
                opacity=0.35,
            ),
            row=2,
            col=1,
        )
        fig.update_yaxes(title_text="Close", row=1, col=1, gridcolor=SURFACE_HIGH, zeroline=False)
        fig.update_yaxes(title_text="OI", row=2, col=1, gridcolor=SURFACE_HIGH, zeroline=False)
    else:
        fig = go.Figure(
            go.Scatter(
                x=df["time"],
                y=df["close"],
                mode="lines",
                name="Close",
                line=dict(color=PRIMARY, width=2),
            )
        )
        fig.update_yaxes(title_text="Close", gridcolor=SURFACE_HIGH, zeroline=False)

    fig.update_xaxes(gridcolor=SURFACE_HIGH, zeroline=False, showline=False)
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#131313",
        plot_bgcolor="#1c1b1b",
        font=dict(color=ON_SURFACE, family="Inter, sans-serif", size=12),
        title=dict(text=title, font=dict(size=16, color=ON_SURFACE)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=48, r=24, t=56, b=40),
        hovermode="x unified",
    )
    return fig
