"""
Plotly charts for the monthly-trend view. Two departures from a literal
reading of the prototype screenshot, made per the loaded dataviz skill's
non-negotiables (not a stylistic choice):

- The "combo chart" is two stacked panels sharing one x-axis (bars: Net
  Revenue; line: Contribution Margin %), NOT a single dual-y-axis plot --
  a dual-axis chart invents a correlation the alignment of two arbitrary
  scales doesn't actually show (the skill's #1 flagged anti-pattern).
- The "donut" is a gauge/meter (arc 0-100%, one hue, same-ramp track), NOT
  a 2-slice pie -- a single ratio against an implicit limit is exactly the
  case the skill calls out a pie/donut as the wrong form for.

Colors are the validated default categorical palette (see the dataviz
skill's references/palette.md): slot 1 blue for magnitude, slot 2 orange
for the second measure, applied in fixed order.
"""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from i18n import month_label, t

_BLUE = "#2a78d6"
_ORANGE = "#eb6834"
_GRID = "#e1e0d9"
_AXIS = "#c3c2b7"
_MUTED = "#898781"
_INK = "#0b0b0b"


def combo_chart(periods: list[str], net_revenue: list[float], margin_pct: list, lang: str) -> go.Figure:
    labels = [month_label(p, lang) for p in periods]

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                         row_heights=[0.6, 0.4],
                         subplot_titles=(t("kpi_net_revenue", lang), t("chart_donut_title", lang)))

    fig.add_trace(
        go.Bar(x=labels, y=net_revenue, name=t("kpi_net_revenue", lang),
               marker_color=_BLUE, marker_line_width=0,
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
        margin=dict(l=10, r=10, t=36, b=10),
        plot_bgcolor="#fcfcfb",
        paper_bgcolor="#fcfcfb",
        font=dict(color=_INK, family="system-ui, -apple-system, Segoe UI, sans-serif"),
        height=380,
    )
    fig.update_xaxes(showgrid=False, linecolor=_AXIS, tickfont=dict(color=_MUTED))
    fig.update_yaxes(showgrid=True, gridcolor=_GRID, zerolinecolor=_AXIS, tickfont=dict(color=_MUTED))
    fig.update_yaxes(ticksuffix="%", row=2, col=1)
    return fig


def margin_meter(margin_pct: float | None, lang: str) -> go.Figure:
    """A single-ratio meter (arc gauge), not a 2-slice donut -- see module
    docstring. `margin_pct` can be negative or >100; the gauge clamps its
    track to [-50, 100] so an unprofitable period still renders sensibly."""
    value = margin_pct if margin_pct is not None else 0.0
    lo, hi = -50, 100
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": "%", "font": {"color": _INK, "size": 36}},
        gauge={
            "axis": {"range": [lo, hi], "tickcolor": _MUTED, "tickfont": {"color": _MUTED}},
            "bar": {"color": _BLUE, "thickness": 0.28},
            "bgcolor": "#fcfcfb",
            "borderwidth": 0,
            "threshold": {"line": {"color": _AXIS, "width": 2}, "thickness": 0.9, "value": 0},
        },
        title={"text": t("chart_donut_title", lang), "font": {"color": _MUTED, "size": 13}},
    ))
    fig.update_layout(
        height=220,
        margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor="#fcfcfb",
        font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif"),
    )
    return fig
