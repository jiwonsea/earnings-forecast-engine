"""Bridge from forecast EPS to BVT DCF fair value sensitivity.

Loose coupling: this module imports nothing from the BVT repo. It expects a
caller-supplied function or pre-computed elasticity factor:
  fair_value_delta_pct = elasticity × eps_delta_pct

For MVP, the elasticity is a YAML-provided constant (set by the user after
running BVT once with sensitivity analysis). P2 work will wire BVT directly.
"""

from __future__ import annotations

from schemas.models import ScenarioTree


def sensitivity_to_dcf(
    model_tree: ScenarioTree,
    consensus_eps_fy: float | None,
    fair_value_elasticity: float = 1.2,
) -> dict[str, float | None]:
    """Compute implied fair-value delta vs consensus.

    Args:
        model_tree: Full tree — weighted_annual FY1 EPS is used.
        consensus_eps_fy: Consensus EPS for the same fiscal year.
        fair_value_elasticity: EPS-delta -> fair-value-delta multiplier (default 1.2).
            User-provided via profile YAML if customized. 1.2 is a placeholder
            assuming roughly linear DCF response with small terminal-value amplification.

    Returns:
        dict with eps_delta_pct, fair_value_delta_pct, note.

    Raises:
        NotImplementedError: Codex implementation.
    """
    raise NotImplementedError("Codex: implement valuation bridge per docs/methodology.md §8")
