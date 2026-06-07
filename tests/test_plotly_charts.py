from __future__ import annotations

from datetime import date

from engine.scenario import aggregate_quarterly_to_annual, build_scenario_tree
from output.plotly_charts import build_fan_chart
from schemas.models import (
    CompanyMeta,
    QuarterlyForecast,
    ScenarioCase,
    ScenarioProbabilities,
    SegmentForecast,
)


def _q(label: str, scenario: str, revenue: float) -> QuarterlyForecast:
    return QuarterlyForecast(
        quarter_label=label,
        scenario=scenario,
        revenue_total=revenue,
        revenue_by_segment=[SegmentForecast(segment_id="dram", revenue=revenue)],
        gross_profit=revenue * 0.4,
        operating_profit=revenue * 0.3,
        net_profit=revenue * 0.2,
        gp_margin=0.4,
        op_margin=0.3,
        np_margin=0.2,
        eps_basic=revenue,
    )


def _case(name: str, revenue: float) -> ScenarioCase:
    quarterly = [_q("2026Q2", name, revenue), _q("2026Q3", name, revenue * 1.1)]
    return ScenarioCase(
        scenario=name,
        probability={"bear": 0.25, "base": 0.50, "bull": 0.25}[name],
        rationale="test",
        quarterly=quarterly,
        annual=aggregate_quarterly_to_annual(quarterly, name),
    )


def _tree():
    company = CompanyMeta(
        name="SK Hynix",
        name_kr="SK",
        ticker_yahoo="000660.KS",
        corp_code_dart="00164779",
        fiscal_year_end_month=12,
        reporting_unit="KRW_billion",
    )
    return build_scenario_tree(
        company,
        date(2026, 6, 2),
        _case("bear", 80),
        _case("base", 100),
        _case("bull", 130),
        ScenarioProbabilities(bear=0.25, base=0.50, bull=0.25),
    )


def test_fan_chart_keeps_scenario_legends_separate_and_fixes_yaxis_range() -> None:
    chart = build_fan_chart(_tree())
    band_lower, band_upper, bear, weighted, bull = chart["data"]

    assert band_lower["showlegend"] is False
    assert band_upper["showlegend"] is False
    assert band_upper["fill"] == "tonexty"
    assert [trace["name"] for trace in chart["data"] if trace.get("showlegend", True)] == [
        "Bear",
        "Weighted",
        "Bull",
    ]
    assert "legendgroup" not in bear
    assert "legendgroup" not in bull
    assert weighted["name"] == "Weighted"
    assert chart["layout"]["yaxis"]["range"][0] > 0
