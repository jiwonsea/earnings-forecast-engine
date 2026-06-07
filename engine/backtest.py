"""Retrospective backtest of the forecast methodology.

For each historical quarter Q in [start, end]:
  1. Take the prior 4Q (Q-4 .. Q-1) as the seed and baseline.
  2. Apply the SAME methodology used for forward forecasting.
  3. Compare projected Q against the actual Q.
  4. Aggregate errors into MAPE / hit_ratio / bias.

No look-ahead bias allowed — only data available before period_end of Q.
"""

from __future__ import annotations

from schemas.models import (
    AnchorMargins,
    BacktestQuarter,
    BacktestResult,
    FinanceAssumptions,
    HistoricalDriver,
    MarginBaseline,
    MarginAssumptions,
    QuarterlyActual,
    SegmentAssumptions,
    SharesOutstanding,
)
from engine.eps_bridge import project_eps
from engine.margin_model import project_margins
from engine.segment_revenue import project_quarterly_revenue
from engine.tax_finance import apply_taxes_and_finance


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _realized_price_assumptions(
    assumptions: SegmentAssumptions,
    driver: HistoricalDriver,
) -> SegmentAssumptions:
    """Return one-quarter assumptions with realized ASP and HBM share.

    Args:
        assumptions: Base scenario assumptions; bit growth values are retained.
        driver: Observed market price and HBM-share driver for the target quarter.

    Returns:
        SegmentAssumptions for one backtest quarter.

    Raises:
        ValueError: If base assumptions do not contain at least one quarter.
    """
    return SegmentAssumptions(
        dram_bit_growth_qoq=[assumptions.dram_bit_growth_qoq[0]],
        dram_hbm_share_qoq=[driver.hbm_share],
        dram_hbm_asp_yoy=driver.hbm_asp_qoq * 4.0,
        dram_ddr_asp_qoq=[driver.ddr_asp_qoq],
        nand_bit_growth_qoq=[assumptions.nand_bit_growth_qoq[0]],
        nand_asp_qoq=[driver.nand_asp_qoq],
        other_revenue_growth_qoq=[assumptions.other_revenue_growth_qoq[0]],
    )


def run_backtest(
    historical_actuals: list[QuarterlyActual],
    methodology_assumptions: SegmentAssumptions,
    margin_assumptions: MarginAssumptions,
    anchor_margins: AnchorMargins,
    finance_assumptions: FinanceAssumptions,
    shares: SharesOutstanding,
    historical_drivers: dict[str, HistoricalDriver | float] | None = None,
    lookback_quarters: int = 8,
) -> BacktestResult:
    """Run retrospective backtest over the most recent N quarters.

    Args:
        historical_actuals: Must contain at least lookback_quarters + 4 quarters
            (the extra 4 are needed as the initial seed for the earliest test point).
        methodology_assumptions: Same shape as forward assumptions — typically the
            base-case driver set, applied uniformly for fair comparison.
        margin_assumptions: Same base-case margin assumptions used by forward.
        finance_assumptions: Same base-case tax/finance assumptions used by forward.
        shares: Share count used for EPS bridge.
        historical_drivers: quarter_label -> HBM share and market ASP driver used for
            quarter-specific backtest margin model.
        lookback_quarters: How many recent quarters to score (default 8).

    Returns:
        BacktestResult with per-quarter detail + summary stats.

    Raises:
        ValueError: If insufficient history.
        NotImplementedError: Codex implementation.
    """
    required = lookback_quarters + 4
    if len(historical_actuals) < required:
        raise ValueError(f"need at least {required} quarters for backtest")

    actuals = sorted(historical_actuals, key=lambda item: item.period_end)
    start_idx = len(actuals) - lookback_quarters
    rows: list[BacktestQuarter] = []
    asp_hbm = 1.0
    asp_ddr = 1.0
    asp_nand = 1.0
    periods_since_anchor = 0
    for idx in range(start_idx, len(actuals)):
        prior_window = actuals[idx - 4 : idx]
        seed = actuals[idx - 1]
        target = actuals[idx]
        gp_margins = [q.gross_profit / q.revenue_total for q in prior_window if q.revenue_total]
        op_margins = [q.operating_profit / q.revenue_total for q in prior_window if q.revenue_total]
        np_margins = [q.net_profit / q.revenue_total for q in prior_window if q.revenue_total]
        baseline = MarginBaseline(
            gp_margin=_avg(gp_margins),
            op_margin=_avg(op_margins),
            np_margin=_avg(np_margins),
            dram_blended_asp=next(s.revenue for s in seed.revenue_by_segment if s.segment_id == "dram"),
            nand_blended_asp=next(s.revenue for s in seed.revenue_by_segment if s.segment_id == "nand"),
        )
        revenue_assumptions = methodology_assumptions
        if historical_drivers is not None:
            driver = historical_drivers.get(target.quarter_label)
            if driver is None:
                raise ValueError(f"missing historical driver for {target.quarter_label}")
            if isinstance(driver, HistoricalDriver):
                revenue_assumptions = _realized_price_assumptions(methodology_assumptions, driver)
        forecast_chain = project_quarterly_revenue(seed, baseline, revenue_assumptions, 1)
        if historical_drivers is not None:
            driver = historical_drivers.get(target.quarter_label)
            if driver is None:
                raise ValueError(f"missing historical driver for {target.quarter_label}")
            hbm_share = driver if isinstance(driver, float) else driver.hbm_share
            updates = {"hbm_share": hbm_share}
            if isinstance(driver, HistoricalDriver):
                asp_hbm *= 1.0 + driver.hbm_asp_qoq
                asp_ddr *= 1.0 + driver.ddr_asp_qoq
                asp_nand *= 1.0 + driver.nand_asp_qoq
                periods_since_anchor += 1
                updates.update(
                    {
                        "asp_hbm": asp_hbm,
                        "asp_ddr": asp_ddr,
                        "asp_nand": asp_nand,
                        "margin_periods_since_anchor": periods_since_anchor,
                    }
                )
            forecast_chain = [
                forecast.model_copy(update=updates)
                for forecast in forecast_chain
            ]
        forecast_chain = project_margins(forecast_chain, baseline, margin_assumptions, anchor_margins)
        forecast_chain = apply_taxes_and_finance(forecast_chain, finance_assumptions)
        forecast_chain = project_eps(forecast_chain, shares)
        forecast = forecast_chain[0]
        model_revenue = forecast.revenue_total
        revenue_error_pct = (model_revenue - target.revenue_total) / target.revenue_total

        actual_eps = target.eps_basic
        model_eps = forecast.eps_basic
        eps_error_pct = None
        if actual_eps not in (None, 0) and model_eps is not None:
            eps_error_pct = (model_eps - actual_eps) / actual_eps

        model_qoq = model_revenue - seed.revenue_total
        actual_qoq = target.revenue_total - seed.revenue_total
        direction_match = (model_qoq >= 0 and actual_qoq >= 0) or (model_qoq < 0 and actual_qoq < 0)
        rows.append(
            BacktestQuarter(
                quarter_label=target.quarter_label,
                actual_revenue=target.revenue_total,
                model_revenue=model_revenue,
                revenue_error_pct=revenue_error_pct,
                actual_eps=actual_eps,
                model_eps=model_eps,
                eps_error_pct=eps_error_pct,
                direction_match=direction_match,
            )
        )

    revenue_errors = [row.revenue_error_pct for row in rows]
    eps_errors = [row.eps_error_pct for row in rows if row.eps_error_pct is not None]
    return BacktestResult(
        lookback_quarters=lookback_quarters,
        quarters=rows,
        revenue_mape=_avg([abs(value) for value in revenue_errors]),
        eps_mape=_avg([abs(value) for value in eps_errors]) if eps_errors else None,
        hit_ratio_direction=_avg([1.0 if row.direction_match else 0.0 for row in rows]),
        bias_revenue=_avg(revenue_errors),
        bias_eps=_avg(eps_errors) if eps_errors else None,
    )
