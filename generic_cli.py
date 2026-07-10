"""Generic-company forecast entry point (non-memory issuers).

    python generic_cli.py --profile profiles/nvda.generic.yaml
    python generic_cli.py --profile profiles/nvda.generic.yaml --json

Kept separate from cli.py (the memory/SK-Hynix pipeline) so the DRAM/NAND
backtest coupling and its 9Q invariant are never touched. Offline by design:
consumes only the profile YAML (no Yahoo/DART), so it runs in the Cowork sandbox.

Output: Korean console summary + Markdown report (+ optional JSON) under reports/.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent
REPORTS_DIR = REPO_ROOT / "reports"

sys.path.insert(0, str(REPO_ROOT))

from schemas.generic import GenericProfile  # noqa: E402
from engine.generic_forecast import run_generic_forecast  # noqa: E402
from engine.generic_signal import (  # noqa: E402
    build_signal_block,
    fetch_consensus_fy1_eps,
)


def load_generic_profile(path: Path) -> GenericProfile:
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    return GenericProfile.model_validate(raw)


def _mape(pairs: list[tuple[float, float]]) -> float | None:
    errs = [abs(m - a) / abs(a) for m, a in pairs if a]
    return 100.0 * sum(errs) / len(errs) if errs else None


def _bias(pairs: list[tuple[float, float]]) -> float | None:
    errs = [(m - a) / a for m, a in pairs if a]
    return 100.0 * sum(errs) / len(errs) if errs else None


def backtest_generic(profile: GenericProfile) -> dict:
    """One-step-ahead, seasonally-aware offline backtest over the actuals block.

    Predict each quarter's revenue as prior-actual x (1 + base growth[slot]);
    EPS via base op_margin/tax/net_interest at the same slot and the fixed
    diluted share count. ``slot`` is the target quarter's calendar position
    (Q1->0 ... Q4->3) so a seasonal driver vector is matched to the right step
    rather than always using growth[0]. Compared against a naive random walk.
    """
    actuals = sorted(profile.actuals, key=lambda a: (int(a.quarter_label[:4]), int(a.quarter_label[-1])))
    if len(actuals) < 2:
        return {"n": len(actuals), "note": "actuals < 2 — backtest skipped"}

    n = profile.window.n_quarters
    g = profile.base.growth(n)
    m = profile.base.margin(n)
    t = profile.base.tax(n)
    ni = profile.base.net_interest(n)
    scale = profile.unit_scale
    shares = profile.weighted_avg_diluted

    def _slot(label: str) -> int:
        return min(int(label[-1]) - 1, n - 1)

    rev_pairs: list[tuple[float, float]] = []
    eps_pairs: list[tuple[float, float]] = []
    rw_rev_pairs: list[tuple[float, float]] = []
    rw_eps_pairs: list[tuple[float, float]] = []
    rows = []
    for prev, cur in zip(actuals, actuals[1:]):
        s = _slot(cur.quarter_label)
        model_rev = prev.revenue_total * (1.0 + g[s])
        op = model_rev * m[s]
        pretax = op + ni[s] * model_rev
        net = pretax * (1.0 - t[s])
        model_eps = net * scale / shares
        rev_pairs.append((model_rev, cur.revenue_total))
        rw_rev_pairs.append((prev.revenue_total, cur.revenue_total))
        # rw_rev/rw_eps = random-walk (persistence) baseline = prior-quarter actual.
        # Carried per-row so the signal block can recompute skill over a trailing
        # window (Item 1 dual-window reporting) without re-deriving the baseline.
        row = {
            "quarter": cur.quarter_label,
            "actual_rev": cur.revenue_total,
            "model_rev": model_rev,
            "rw_rev": prev.revenue_total,
        }
        if cur.eps_diluted is not None and prev.eps_diluted is not None:
            eps_pairs.append((model_eps, cur.eps_diluted))
            rw_eps_pairs.append((prev.eps_diluted, cur.eps_diluted))
            row["actual_eps"] = cur.eps_diluted
            row["model_eps"] = model_eps
            row["rw_eps"] = prev.eps_diluted
        rows.append(row)

    return {
        "n": len(rev_pairs),
        "revenue_mape": _mape(rev_pairs),
        "revenue_bias": _bias(rev_pairs),
        "eps_mape": _mape(eps_pairs),
        "eps_bias": _bias(eps_pairs),
        "naive_rw_revenue_mape": _mape(rw_rev_pairs),
        "naive_rw_eps_mape": _mape(rw_eps_pairs),
        "rows": rows,
    }


def render_markdown(profile: GenericProfile, fc, bt: dict) -> str:
    p = profile
    lines = [
        f"# {p.name_kr} ({p.name}) — 실적 전망 (Generic)",
        "",
        f"- 티커: `{p.ticker}` · 통화: {p.currency} ({p.reporting_unit}) · 희석주식수: {p.weighted_avg_diluted:,.0f}",
        f"- 시드 분기: {p.seed.quarter_label} (매출 {p.seed.revenue_total:,.0f})",
        f"- 전망 구간: {p.window.start_quarter}부터 {p.window.n_quarters}개 분기",
        "",
        "## 확률가중 분기 전망",
        "",
        "| 분기 | 매출 | 영업이익 | 순이익 | EPS(희석) |",
        "|---|---:|---:|---:|---:|",
    ]
    for q in fc.weighted_quarterly:
        lines.append(
            f"| {q.quarter_label} | {q.revenue_total:,.0f} | {q.operating_profit:,.0f} "
            f"| {q.net_profit:,.0f} | {q.eps_diluted:,.2f} |"
        )
    lines += ["", "## 연간 EPS (시나리오별)", "", "| FY | Bear | Base | Bull | 가중 |", "|---|---:|---:|---:|---:|"]
    years = [a.fiscal_year for a in fc.weighted_annual]
    for i, fy in enumerate(years):
        b = fc.scenarios_annual["bear"][i].eps_basic or 0.0
        ba = fc.scenarios_annual["base"][i].eps_basic or 0.0
        bu = fc.scenarios_annual["bull"][i].eps_basic or 0.0
        w = fc.weighted_annual[i].eps_basic or 0.0
        lines.append(f"| {fy} | {b:,.2f} | {ba:,.2f} | {bu:,.2f} | {w:,.2f} |")

    lines += ["", "## 오프라인 백테스트 (1-step, seasonally-aware)", ""]
    if bt.get("revenue_mape") is None:
        lines.append(f"- {bt.get('note', 'N/A')}")
    else:
        lines.append(
            f"- N={bt['n']} · 매출 MAPE {bt['revenue_mape']:.1f}% (naive RW {bt['naive_rw_revenue_mape']:.1f}%) · 매출 bias {bt['revenue_bias']:+.1f}%"
        )
        if bt.get("eps_mape") is not None:
            lines.append(
                f"- EPS MAPE {bt['eps_mape']:.1f}% (naive RW {bt['naive_rw_eps_mape']:.1f}%) · EPS bias {bt['eps_bias']:+.1f}%"
            )
    if p.notes:
        lines += ["", "## 데이터 출처 / 주의", ""]
        lines += [f"- {n}" for n in p.notes]
    lines += [
        "",
        f"_시나리오 확률: bear {p.bear.probability:.0%} / base {p.base.probability:.0%} / bull {p.bull.probability:.0%}_",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generic-company earnings forecast")
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--json", action="store_true", help="also write JSON")
    args = parser.parse_args(argv)

    profile = load_generic_profile(args.profile)
    fc = run_generic_forecast(profile)
    bt = backtest_generic(profile)

    REPORTS_DIR.mkdir(exist_ok=True)
    md = render_markdown(profile, fc, bt)
    stem = args.profile.stem.replace(".generic", "")
    md_path = REPORTS_DIR / f"{stem}_generic_forecast.md"
    md_path.write_text(md, encoding="utf-8")

    w_fy = fc.weighted_annual
    print(f"[{profile.name}] 확률가중 FY EPS:", ", ".join(f"{a.fiscal_year}={a.eps_basic:,.2f}" for a in w_fy))
    if bt.get("revenue_mape") is not None:
        eps_txt = f" · EPS MAPE {bt['eps_mape']:.1f}%" if bt.get("eps_mape") is not None else ""
        print(f"  백테스트 N={bt['n']} · 매출 MAPE {bt['revenue_mape']:.1f}% (RW {bt['naive_rw_revenue_mape']:.1f}%){eps_txt}")
    else:
        print(f"  백테스트: {bt.get('note')}")
    print(f"  리포트: {md_path}")

    if args.json:
        json_path = REPORTS_DIR / f"{stem}_generic_forecast.json"
        weighted_annual = [a.model_dump() for a in fc.weighted_annual]
        weighted_quarterly = [q.model_dump() for q in fc.weighted_quarterly]
        # Consensus is best-effort (Yahoo); returns None offline so the block
        # still builds with consensus.direction = "n_a".
        consensus_fy1 = fetch_consensus_fy1_eps(profile.ticker, w_fy[0].fiscal_year if w_fy else None)
        payload = {
            "company": profile.name,
            "weighted_annual": weighted_annual,
            "weighted_quarterly": weighted_quarterly,
            "backtest": bt,
            "signal": build_signal_block(
                weighted_annual, weighted_quarterly, bt, consensus_fy1
            ),
        }
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(f"  JSON: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
