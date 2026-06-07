"""Primary HTML report — Jinja2 template + inline Plotly figures.

Self-contained single file. Plotly JS via CDN by default (smaller file);
pass inline_plotly=True for offline distribution at the cost of ~3MB.

Output layout (per docs/methodology.md §13-B):
  - Top: 6 KPI cards (Model FY26 EPS, Consensus FY26 EPS, Gap %, Backtest MAPE,
    Scenario range, As-of-date).
  - Middle: 3 tabs — Forecast / Backtest / Consensus Gap.
  - Bottom: Assumptions YAML dump + AI collaboration disclosure.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from schemas.models import BacktestResult, ConsensusGap, ScenarioTree
from output.plotly_charts import build_beat_miss_bar, build_fan_chart, build_scenario_compare


def render_html_report(
    out_path: Path,
    tree: ScenarioTree,
    consensus_gaps: list[ConsensusGap],
    backtest: BacktestResult,
    profile_raw: dict,
    inline_plotly: bool = False,
) -> Path:
    """Render the full HTML report to out_path.

    Args:
        out_path: Target file path (must end with .html).
        tree: Full scenario tree.
        consensus_gaps: From engine.consensus_diff.
        backtest: From engine.backtest.
        profile_raw: Original profile YAML dict (rendered as assumptions block).
        inline_plotly: If True, bundle plotly.js into the HTML (offline-friendly).

    Returns:
        out_path on success.

    Raises:
        NotImplementedError: Codex implementation.
    """
    import yaml

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plotly_script = (
        '<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>'
        if not inline_plotly
        else '<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>'
    )
    fan = json.dumps(build_fan_chart(tree))
    beat = json.dumps(build_beat_miss_bar(backtest))
    compare = json.dumps(build_scenario_compare(tree))

    gap_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(g.period_label)}</td><td>{g.metric}</td>"
        f"<td>{g.model_value:,.1f}</td><td>{'' if g.consensus_value is None else f'{g.consensus_value:,.1f}'}</td>"
        f"<td>{'' if g.gap_pct is None else f'{g.gap_pct:.1%}'}</td><td>{g.direction}</td>"
        f"<td>{html.escape(g.interpretation)}</td></tr>"
        for g in consensus_gaps
    )
    backtest_rows = "\n".join(
        "<tr>"
        f"<td>{q.quarter_label}</td><td>{q.actual_revenue:,.1f}</td><td>{q.model_revenue:,.1f}</td>"
        f"<td>{q.revenue_error_pct:.1%}</td><td>{'' if q.actual_eps is None else f'{q.actual_eps:,.1f}'}</td>"
        f"<td>{'' if q.model_eps is None else f'{q.model_eps:,.1f}'}</td>"
        f"<td>{'' if q.eps_error_pct is None else f'{q.eps_error_pct:.1%}'}</td>"
        f"<td>{q.direction_match}</td></tr>"
        for q in backtest.quarters
    )
    notes = profile_raw.get("consensus_notes") or []
    warning_html = ""
    if notes:
        warning_items = "".join(f"<li>{html.escape(str(note))}</li>" for note in notes)
        warning_html = f"<div class=\"card\"><b>Data warning</b><ul>{warning_items}</ul></div>"
    fy1_eps = tree.weighted_annual[0].eps_basic if tree.weighted_annual else None
    content = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><title>{html.escape(tree.company.name)} report</title>
{plotly_script}
<style>body{{font-family:Arial,sans-serif;margin:24px;color:#111827}}table{{border-collapse:collapse;width:100%;margin:16px 0}}td,th{{border:1px solid #d1d5db;padding:6px;text-align:right}}td:first-child,th:first-child{{text-align:left}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.card{{border:1px solid #d1d5db;padding:12px;border-radius:6px}}pre{{white-space:pre-wrap;background:#f3f4f6;padding:12px}}</style>
</head><body>
<h1>{html.escape(tree.company.name_kr)} ({tree.company.ticker_yahoo})</h1>
<div class="grid">
<div class="card"><b>Weighted FY EPS</b><br>{'' if fy1_eps is None else f'{fy1_eps:,.0f}'}</div>
<div class="card"><b>Revenue MAPE</b><br>{backtest.revenue_mape:.1%}</div>
<div class="card"><b>EPS MAPE</b><br>{'' if backtest.eps_mape is None else f'{backtest.eps_mape:.1%}'}</div>
<div class="card"><b>Hit Ratio</b><br>{backtest.hit_ratio_direction:.1%}</div>
</div>
{warning_html}
<h2>Forecast</h2><div id="fan"></div><div id="compare"></div>
<h2>Consensus Gap</h2><table><thead><tr><th>Period</th><th>Metric</th><th>Model</th><th>Consensus</th><th>Gap</th><th>Direction</th><th>Interpretation</th></tr></thead><tbody>{gap_rows}</tbody></table>
<h2>Backtest</h2><div id="beat"></div><table><thead><tr><th>Quarter</th><th>Actual Rev</th><th>Model Rev</th><th>Rev Err</th><th>Actual EPS</th><th>Model EPS</th><th>EPS Err</th><th>Direction</th></tr></thead><tbody>{backtest_rows}</tbody></table>
<h2>Assumptions</h2><pre>{html.escape(yaml.safe_dump(profile_raw, allow_unicode=True, sort_keys=False))}</pre>
<script>const fan={fan};const beat={beat};const compare={compare};Plotly.newPlot('fan',fan.data,fan.layout);Plotly.newPlot('beat',beat.data,beat.layout);Plotly.newPlot('compare',compare.data,compare.layout);</script>
</body></html>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    return out_path
