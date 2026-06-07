"""Markdown summary report — GitHub README embed + cover letter quotation source.

Plain text only, no JS. Static PNG charts embedded via relative path.
Designed for grep-friendly reuse.
"""

from __future__ import annotations

from pathlib import Path

from schemas.models import BacktestResult, ConsensusGap, ScenarioTree


def render_md_report(
    out_path: Path,
    tree: ScenarioTree,
    consensus_gaps: list[ConsensusGap],
    backtest: BacktestResult,
    png_fan_path: Path | None = None,
    png_beat_miss_path: Path | None = None,
    consensus_notes: list[str] | None = None,
) -> Path:
    """Render the MD summary.

    Args:
        out_path: Target file path (.md).
        tree, consensus_gaps, backtest: Same inputs as html_builder.
        png_fan_path, png_beat_miss_path: Static chart paths (optional).

    Returns:
        out_path on success.

    Raises:
        NotImplementedError: Codex implementation.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {tree.company.name_kr} ({tree.company.ticker_yahoo}) Earnings Forecast",
        "",
        f"**As of**: {tree.as_of}",
        "",
        "## Headline",
        "",
        f"- Revenue MAPE: {backtest.revenue_mape:.1%}",
        f"- EPS MAPE: {'' if backtest.eps_mape is None else f'{backtest.eps_mape:.1%}'}",
        f"- Direction hit ratio: {backtest.hit_ratio_direction:.1%}",
        "",
    ]
    if consensus_notes:
        lines += ["## Data Warnings", ""]
        lines += [f"- {note}" for note in consensus_notes]
        lines.append("")
    if png_fan_path is not None:
        lines += [f"![Forecast fan chart]({png_fan_path.name})", ""]
    lines += [
        "## Consensus Gap",
        "",
        "| Period | Metric | Model | Consensus | Gap % | Direction |",
        "|---|---|---:|---:|---:|---|",
    ]
    for gap in consensus_gaps:
        lines.append(
            f"| {gap.period_label} | {gap.metric} | {gap.model_value:,.1f} | "
            f"{'' if gap.consensus_value is None else f'{gap.consensus_value:,.1f}'} | "
            f"{'' if gap.gap_pct is None else f'{gap.gap_pct:.1%}'} | {gap.direction} |"
        )
    lines += ["", "## Backtest", ""]
    if png_beat_miss_path is not None:
        lines += [f"![Beat miss chart]({png_beat_miss_path.name})", ""]
    lines += [
        "| Quarter | Actual Rev | Model Rev | Rev Err % | Actual EPS | Model EPS | EPS Err % | Direction |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in backtest.quarters:
        lines.append(
            f"| {row.quarter_label} | {row.actual_revenue:,.1f} | {row.model_revenue:,.1f} | "
            f"{row.revenue_error_pct:.1%} | {'' if row.actual_eps is None else f'{row.actual_eps:,.1f}'} | "
            f"{'' if row.model_eps is None else f'{row.model_eps:,.1f}'} | "
            f"{'' if row.eps_error_pct is None else f'{row.eps_error_pct:.1%}'} | {row.direction_match} |"
        )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return out_path
