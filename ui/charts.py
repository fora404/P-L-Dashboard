"""
Plotly charts for the monthly-trend view.

- The "combo chart" is a single panel, two grouped bar series (Net Revenue,
  Contribution Margin %) sharing one x-axis but each on its own y-axis
  (secondary_y). This is a dual-axis chart, which the dataviz skill flags
  as the #1 anti-pattern in general -- here it's a deliberate, explicit
  user request (to match a reference mockup) made after being told the two
  series have incompatible scales, so the margin bars carry no cross-series
  height comparison to Net Revenue. Each series' own axis is still labeled
  in its own color so it never reads as a shared scale.
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

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(x=labels, y=net_revenue, name=t("kpi_net_revenue", lang),
               marker_color=_NAVY, marker_line_width=0, offsetgroup="revenue",
               hovertemplate="%{x}: %{y:,.0f} €<extra></extra>"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Bar(x=labels, y=margin_pct, name=t("chart_donut_title", lang),
               marker_color=_ORANGE, marker_line_width=0, offsetgroup="margin",
               hovertemplate="%{x}: %{y:.1f}%<extra></extra>"),
        secondary_y=True,
    )

    fig.update_layout(
        barmode="group",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="left", x=0,
                    font=dict(color=_MUTED)),
        hovermode="x unified",
        margin=dict(l=10, r=10, t=10, b=40),
        plot_bgcolor=_SURFACE,
        paper_bgcolor=_SURFACE,
        font=dict(color=_INK, family="system-ui, -apple-system, Segoe UI, sans-serif"),
        height=380,
    )
    fig.update_xaxes(showgrid=False, linecolor=_AXIS, tickfont=dict(color=_MUTED))
    fig.update_yaxes(showgrid=True, gridcolor=_GRID, zerolinecolor=_AXIS,
                      tickfont=dict(color=_NAVY), secondary_y=False)
    fig.update_yaxes(showgrid=False, zeroline=False, ticksuffix="%",
                      tickfont=dict(color=_ORANGE), secondary_y=True)
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
