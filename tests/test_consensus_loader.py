from __future__ import annotations

from datetime import date

from pipeline.consensus_loader import to_consensus_record


def test_quarterly_consensus_labels_derive_from_as_of_when_history_period_is_null(
    sk_hynix_yahoo_raw: dict,
) -> None:
    raw = {
        **sk_hynix_yahoo_raw,
        "earnings_history": [
            {**row, "period": None}
            for row in sk_hynix_yahoo_raw["earnings_history"]
        ],
    }

    record = to_consensus_record(raw, "000660.KS", as_of=date(2026, 6, 2))

    assert set(record.revenue_estimate_quarterly) == {"2026Q2", "2026Q3"}
    assert set(record.eps_estimate_quarterly) == {"2026Q2", "2026Q3"}
    assert record.revenue_estimate_quarterly["2026Q2"] == 81815.89382
    assert "quarterly revenue consensus unavailable" not in record.notes
    assert "quarterly EPS consensus unavailable" not in record.notes


def test_quarterly_consensus_labels_roll_over_year_boundary(sk_hynix_yahoo_raw: dict) -> None:
    record = to_consensus_record(sk_hynix_yahoo_raw, "000660.KS", as_of=date(2026, 12, 15))

    assert set(record.revenue_estimate_quarterly) == {"2026Q4", "2027Q1"}
