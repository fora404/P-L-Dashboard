"""
Plotly charts for the monthly-trend view. Two departures from a literal
reading of the prototype screenshot, made per the loaded dataviz skill's
non-negotiables (not a stylistic choice):

- The "combo chart" is two stacked panels sharing one x-axis (bars: Net
  Revenue; line: Contribution Margin %), NOT a single dual-y-axis plot --
  a dual-axis chart invents a correlation the alignment of two arbitrary
  scales doesn't actually show (the skill's #1 flagged anti-pattern).
- The "donut" is a single-ratio meter -- a ring with a filled arc (the
  metric) against a track (the remainder), same as a linear progress
  meter bent into a circle -- NOT a 2-slice pie comparing two independent
  categories. A single ratio against an implicit 100% limit is exactly
  the case the skill calls out a plain comparison-pie as the wrong form
  for; rendering it as a filled/track ring keeps the meter semantics while
  matching the reference mockup's ring visual.

Colors follow the brand navy/orange pairing used in ui/styles.py, applied
consistently: navy for magnitude/track, orange for the highlighted ratio.
"""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from i18n import month_label, t

_NAVY = "#21396a"
_ORANGE = "#e8a33d"
_GRID = "#eef0f5"
_AXIS = "#c9cfdb"
_MUTED = "#8b95ab"
_INK = "#1b2233"
_SURFACE = "#ffffff"


def combo_chart(periods: list[str], net_revenue: list[float], margin_pct: list, lang: str) -> go.Figure:
    labels = [month_label(p, lang) for p in periods]

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                         row_heights=[0.62, 0.38])

    fig.add_trace(
        go.Bar(x=labels, y=net_revenue, name=t("kpi_net_revenue", lang),
               marker_color=_NAVY, marker_line_width=0,
               hovertemplate="%{x}: %{y:,.0f} €<extra></extra>"),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=labels, y=margin_pct, name=t("chart_donut_title", lang),
                   mode="lines+markers", line=dict(color=_ORANGE, width=2),
                   marker=dict(size=8, color=_ORANGE),
                   hovertemplate="%{x}: %{y:.1f}%<extra></extra>"),
        row=2, col=1,
    )

    fig.update_layout(
        showlegend=False,
        hovermode="x unified",
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor=_SURFACE,
        paper_bgcolor=_SURFACE,
        font=dict(color=_INK, family="system-ui, -apple-system, Segoe UI, sans-serif"),
        height=380,
    )
    fig.update_xaxes(showgrid=False, linecolor=_AXIS, tickfont=dict(color=_MUTED))
    fig.update_yaxes(showgrid=True, gridcolor=_GRID, zerolinecolor=_AXIS, tickfont=dict(color=_MUTED))
    fig.update_yaxes(ticksuffix="%", row=2, col=1)
    return fig


def margin_meter(margin_pct: float | None, lang: str) -> go.Figure:
    """A single-ratio progress ring: the orange arc is the metric (clamped
    to [0, 100] for the arc's proportions -- the exact signed value still
    shows in the center label), the navy arc is the remainder/track."""
    value = margin_pct if margin_pct is not None else 0.0
    filled = max(0.0, min(100.0, value))
    remainder = 100.0 - filled

    fig = go.Figure(go.Pie(
        values=[filled, remainder],
        labels=[t("chart_donut_title", lang), ""],
        hole=0.72,
        marker=dict(colors=[_ORANGE, _NAVY], line=dict(color=_SURFACE, width=2)),
        textinfo="none",
        sort=False,
        direction="clockwise",
        hovertemplate="%{label}: %{value:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=30),
        height=220,
        paper_bgcolor=_SURFACE,
        font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif"),
        annotations=[
            dict(text=f"{value:.0f}%", x=0.5, y=0.56, xanchor="center", yanchor="middle",
                 font=dict(size=30, color=_INK), showarrow=False),
            dict(text=t("chart_donut_title", lang), x=0.5, y=0.3, xanchor="center", yanchor="middle",
                 font=dict(size=12, color=_MUTED), showarrow=False),
        ],
    )
    return fig
