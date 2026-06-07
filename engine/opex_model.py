"""SG&A / R&D / D&A projection helpers.

For MVP these are simple % of revenue. R&D scales with capex via 5Y straight-line lag.
D&A is implicit in GP margin already, so this module currently focuses on operating cost
checks and sanity caps.
"""

from __future__ import annotations

from schemas.models import MarginAssumptions, QuarterlyForecast


def sanity_check_opex(
    forecast: list[QuarterlyForecast],
    assumptions: MarginAssumptions,
    tolerance: float = 0.02,
) -> list[str]:
    """Return warning strings if implied SG&A / R&D drifts from assumption by > tolerance.

    Used for cross-checking that margin_model output is internally consistent.

    Args:
        forecast: Margin-populated forecast.
        assumptions: Expected ratios.
        tolerance: Acceptable deviation (default 2pp).

    Returns:
        List of human-readable warnings. Empty list = clean.

    Raises:
        NotImplementedError: Codex implementation.
    """
    warnings: list[str] = []
    expected_spread = assumptions.sga_pct_of_revenue + assumptions.rnd_pct_of_revenue
    for quarter in forecast:
        implied_spread = quarter.gp_margin - quarter.op_margin
        if abs(implied_spread - expected_spread) > tolerance:
            warnings.append(
                f"{quarter.quarter_label}: implied opex spread {implied_spread:.4f} "
                f"differs from assumption {expected_spread:.4f}"
            )
    return warnings
