"""Load profiles/{company}.yaml into Pydantic models.

Validates that probabilities sum to 1.0 and driver list lengths match
forecast_window.n_quarters.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from schemas.models import (
    AnchorMargins,
    CompanyMeta,
    FinanceAssumptions,
    HistoricalDriver,
    MarginAssumptions,
    ScenarioProbabilities,
    SegmentAssumptions,
    SharesOutstanding,
)


def load_profile(profile_path: Path) -> dict:
    """Load a YAML profile and return validated Pydantic models keyed by section.

    Args:
        profile_path: Path to profiles/sk_hynix.yaml or similar.

    Returns:
        dict with keys:
            - "company": CompanyMeta
            - "shares": SharesOutstanding
            - "forecast_window": dict (start_quarter, n_quarters, annual_horizon_years)
            - "backtest_window": dict
            - "probabilities": ScenarioProbabilities
            - "scenarios": {"bear": (SegmentAssumptions, MarginAssumptions, FinanceAssumptions),
                            "base": ..., "bull": ...}
            - "raw": original YAML dict (for archival in reports)

    Raises:
        FileNotFoundError: Profile YAML missing.
        pydantic.ValidationError: Schema mismatch.
        NotImplementedError: Codex implementation.
    """
    with open(profile_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    company = CompanyMeta.model_validate(raw["company"])
    shares = SharesOutstanding.model_validate(raw["share_count"])
    anchor_margins = AnchorMargins.model_validate(raw["anchor_margins"])
    historical_drivers = {
        str(quarter_label): HistoricalDriver.model_validate(
            {"quarter_label": str(quarter_label), **driver}
        )
        for quarter_label, driver in raw.get("historical_drivers", {}).items()
    }
    forecast_window = raw["forecast_window"]
    n_quarters = int(forecast_window["n_quarters"])
    segment_revenue_split = {
        str(segment_id): float(share)
        for segment_id, share in raw.get("segment_revenue_split", {}).items()
    }
    if not segment_revenue_split:
        raise ValueError("segment_revenue_split must be specified in the profile YAML")
    split_total = sum(segment_revenue_split.values())
    if abs(split_total - 1.0) > 1e-6:
        raise ValueError(f"segment_revenue_split must sum to 1.0 (got {split_total})")

    scenarios: dict[str, tuple[SegmentAssumptions, MarginAssumptions, FinanceAssumptions]] = {}
    probabilities: dict[str, float] = {}
    rationales: dict[str, str] = {}
    for name in ("bear", "base", "bull"):
        data = raw["assumptions"][name]
        probabilities[name] = float(data["probability"])
        rationales[name] = str(data.get("rationale", ""))
        segment = SegmentAssumptions(
            dram_bit_growth_qoq=data["dram"]["bit_growth_qoq"],
            dram_hbm_share_qoq=data["dram"]["hbm_share_qoq"],
            dram_hbm_asp_yoy=data["dram"]["hbm_asp_yoy"],
            dram_ddr_asp_qoq=data["dram"]["ddr_asp_qoq"],
            nand_bit_growth_qoq=data["nand"]["bit_growth_qoq"],
            nand_asp_qoq=data["nand"]["asp_qoq"],
            other_revenue_growth_qoq=data["other"]["revenue_growth_qoq"],
        )
        for field, values in segment.model_dump().items():
            if isinstance(values, list) and len(values) != n_quarters:
                raise ValueError(f"{name}.{field} length must equal n_quarters")
        scenarios[name] = (
            segment,
            MarginAssumptions.model_validate(data["margins"]),
            FinanceAssumptions.model_validate(data["finance"]),
        )

    return {
        "company": company,
        "shares": shares,
        "forecast_window": forecast_window,
        "backtest_window": raw["backtest_window"],
        "segment_revenue_split": segment_revenue_split,
        "historical_drivers": historical_drivers,
        "anchor_margins": anchor_margins,
        "probabilities": ScenarioProbabilities(**probabilities),
        "rationales": rationales,
        "scenarios": scenarios,
        "raw": raw,
    }
