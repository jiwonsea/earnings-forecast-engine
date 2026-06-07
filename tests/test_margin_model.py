"""Tests for engine.margin_model.project_margins."""

from __future__ import annotations

import pytest

from schemas.models import AnchorMargins, MarginAssumptions, MarginBaseline, QuarterlyForecast, SegmentForecast
from engine.margin_model import project_margins


def _forecast(hbm_share: float = 0.5) -> QuarterlyForecast:
    return QuarterlyForecast(
        quarter_label="2026Q1",
        revenue_total=100.0,
        revenue_by_segment=[
            SegmentForecast(segment_id="dram", revenue=60.0),
            SegmentForecast(segment_id="nand", revenue=30.0),
            SegmentForecast(segment_id="other", revenue=10.0),
        ],
        hbm_share=hbm_share,
        asp_hbm=1.0,
        asp_ddr=1.0,
        asp_nand=1.0,
        margin_periods_since_anchor=0,
        gross_profit=0.0,
        operating_profit=0.0,
        net_profit=0.0,
        gp_margin=0.0,
        op_margin=0.0,
        np_margin=0.0,
    )


def _margin_assumptions() -> MarginAssumptions:
    return MarginAssumptions(
        sga_pct_of_revenue=0.05,
        rnd_pct_of_revenue=0.10,
    )


def _anchor_margins() -> AnchorMargins:
    return AnchorMargins(
        gm_hbm=0.8,
        gm_ddr=0.4,
        gm_nand=0.2,
        gm_other=0.1,
    )


def test_project_margins_uses_hbm_mix_bridge():
    result = project_margins([_forecast()], MarginBaseline(), _margin_assumptions(), _anchor_margins())

    assert result[0].gross_profit == pytest.approx(60.0 * 0.6 + 30.0 * 0.2 + 10.0 * 0.1)
    assert result[0].gp_margin == pytest.approx(0.43)
    assert result[0].op_margin == pytest.approx(0.28)


def test_margin_responds_to_hbm_share_lift():
    result = project_margins([_forecast(1.0)], MarginBaseline(), _margin_assumptions(), _anchor_margins())

    assert result[0].gp_margin == pytest.approx(0.55)


def test_margin_responds_to_asp_and_cost_leverage():
    forecast = _forecast(0.0).model_copy(
        update={"asp_ddr": 1.2, "asp_nand": 0.8, "margin_periods_since_anchor": 1}
    )
    anchor_margins = AnchorMargins(
        gm_hbm=0.8,
        gm_ddr=0.4,
        gm_nand=0.2,
        gm_other=0.1,
        cost_decline_qoq_hbm=0.0,
        cost_decline_qoq_ddr=0.04,
        cost_decline_qoq_nand=0.04,
    )

    result = project_margins([forecast], MarginBaseline(), _margin_assumptions(), anchor_margins)

    ddr_margin = 1.0 - (1.0 - 0.4) * 0.96 / 1.2
    nand_margin = 1.0 - (1.0 - 0.2) * 0.96 / 0.8
    assert result[0].gp_margin == pytest.approx((60.0 * ddr_margin + 30.0 * nand_margin + 10.0 * 0.1) / 100.0)


def test_gp_margin_can_go_negative_without_floor():
    forecast = _forecast(0.0).model_copy(
        update={"asp_ddr": 0.2, "asp_nand": 0.2, "margin_periods_since_anchor": 1}
    )

    result = project_margins([forecast], MarginBaseline(), _margin_assumptions(), _anchor_margins())

    assert result[0].gp_margin < 0.0
