# PLAN — Applying EFE beyond memory: NVIDIA as the test case

Date: 2026-07-10
Scope: `earnings-forecast-engine` generic path (`schemas/generic.py`,
`engine/generic_forecast.py`, `generic_cli.py`, `profiles/nvda.generic.yaml`)
Basis: `HANDOFF_generic_engine.md` (2026-07-06 session), current
`reports/nvda_generic_forecast.md`

## 1. The question

Can the SK Hynix pipeline generalize to non-memory companies — and what does
NVIDIA specifically need? Short answer: the **memory driver chain must not be
ported** (it would be a fake model for NVDA), the **generic path is already the
honest model shape**, and the real work is (a) fixing two data-integrity defects
in the NVDA history, (b) lifting the diagnostic layers (skill metrics,
attribution, risk band, consensus gap) onto the generic path, (c) reporting
parity. The engine code was never the barrier; **driver observability** is.

## 2. Why the memory chain does not port

The SK Hynix chain works because each stage is externally observable:

| Stage (memory path)                  | Observability for SK Hynix              | NVIDIA equivalent                        |
|--------------------------------------|-----------------------------------------|------------------------------------------|
| bit growth × ASP per segment         | TrendForce/industry feeds, quarterly IR  | No unit×ASP disclosure (only segment revenue) |
| HBM share / premium mix              | IR + industry research                   | DC vs Gaming revenue only, coarse        |
| Cost-decline margin chain            | Commodity cost curves, mean-reverting    | No physical cost curve; margin = mix+pricing power |
| DART quarterly detail                | Official, cached, rate-limited API       | EDGAR companyfacts (10-Q GAAP)           |
| KR consensus vintage                 | Yahoo .KS (gated) / FnGuide (P1)         | Yahoo NVDA — rich analyst coverage       |

A bottom-up NVDA model (GPU units × ASP) would require assumption-heavy inputs
with no independent feed to validate against — exactly the "looks more precise
than it is" failure PLAN_skill_adoption.md §5 warns about. Revenue-growth-vector
× op-margin (the generic path) states its ignorance honestly.

**Decision rule for future companies:** give a company a physical driver chain
only if an independent industry feed exists for the physical driver (bits, ASP,
wafer starts, subscriber counts…). Otherwise it goes on the generic path.

## 3. Current NVDA output — evaluation (reports/nvda_generic_forecast.md)

Forward window rolls from 2026Q1 seed (rev $81.6bn); weighted 2026 quarters
$89–108bn, EPS $1.94→$2.36. Backtest N=19: rev MAPE 14.2% vs naive RW 18.5%
(beats RW), EPS MAPE 46.9% vs RW 67.4%, **EPS bias −45.8%**.

Two data-integrity defects dominate that EPS number:

1. **Split-unadjusted EPS history (NEW finding, this session).** The `actuals`
   EPS series is as-reported: 2019Q3 EPS 1.45 on NI $899M. With the profile's
   fixed 24.49B diluted shares the model can only produce 899×scale/24.49B ≈
   0.037 — exactly the reported figure ÷ 40 (= 4:1 split Jul 2021 × 10:1 split
   Jun 2024). Every pre-split quarter contributes a ~−97% "error" that is pure
   share-base mismatch, not model error. EDGAR companyfacts EPS is *not*
   retroactively split-adjusted; any history ingested from it must be adjusted
   by the cumulative split factor. This alone explains most of the −45.8% bias.
2. **Partial circularity (known, HANDOFF §데이터 provenance).** Quarterly
   `actuals` were derived from reported FY totals → backtest revenue MAPE is
   optimistic. Replace with independently reported 10-Q quarters.

Model-shape limits (acceptable, but disclose): constant base margins across a
2019–2026 window that contains a regime break (FY2023→ AI supercycle, op margin
~25%→62%); labels are calendar-quarter approximations of a Jan-ending fiscal
year (~1 month offset — matters when aligning Yahoo consensus quarters).

## 4. Component portability matrix

| Layer                                   | Status on generic path | Work to port |
|-----------------------------------------|------------------------|--------------|
| EPS bridge / scenario weighting / annual agg | Already shared (`QuarterlyForecast`) | none |
| Skill metrics (MASE / Theil / vs-consensus) | Not wired (generic_cli has own 1-step MAPE) | small — reuse `engine/skill_metrics.py` |
| **EPS-error attribution (EFE-1 waterfall)** | Blocked: generic sets `gross_profit=0` → 5-lever bridge undefined | small — either 4-lever variant (rev / OP conv / tax-fin / shares) or ingest COGS from EDGAR and keep 5 levers |
| Below-OP risk band                      | Portable as-is (band over EPS points)  | small |
| Consensus gap                           | Not wired; Yahoo NVDA coverage is rich and reliable (vs sparse .KS) | medium — quarter alignment (fiscal offset) is the only trap |
| Valuation bridge                        | Portable; elasticity remains DRAFT     | none until BVT sensitivity lands |
| HTML/Plotly report                      | Memory-path only; generic emits MD     | medium — generic branch in `output/*` |
| Backtest honesty (no-lookahead, rolling seed) | generic backtest is 1-step slot-matched, weaker than memory 9Q protocol | medium |
| Segment bit×ASP chain, margin cost chain, DART fetcher | memory/Korea-specific | **do not port** |

## 5. Workstreams

### NVDA-1: Data integrity (host — network required)
- Split-adjust the EPS/shares history (cumulative factor per quarter:
  ×40 before 2021-07, ×10 before 2024-06, ×1 after) or re-derive EPS as
  NI / split-adjusted shares. Add `split_history:` to the generic profile schema
  so the adjustment is declared, not silently baked in.
- Replace derived quarterly `actuals` with independently reported 10-Q values
  (EDGAR companyfacts, tag-level: Revenues, NetIncomeLoss, EPS diluted,
  CostOfRevenue for the GP lever). New `pipeline/edgar_fetcher.py` with the
  same cache pattern as `dart_fetcher` (offline-reproducible).
- Fix Tesla NI/EPS (known HANDOFF item) in the same pass.
- Verification: re-run `generic_cli.py --profile profiles/nvda.generic.yaml`;
  EPS bias should collapse from −45.8% to single digits; document before/after.

### NVDA-2: Metrics parity (sandbox-able once NVDA-1 data is cached)
- Swap `backtest_generic`'s ad-hoc MAPE for `engine/skill_metrics.py`
  (MASE/Theil vs RW) — one metrics vocabulary across both paths.
- Add consensus gap: `fetch_consensus("NVDA")` → quarter alignment via fiscal
  calendar mapping (profile field `fiscal_quarter_offset` or explicit
  label↔fiscal-quarter map). Vintage discipline identical to memory path.
- Optional: attribution on generic backtest quarters — 4-lever variant if GP
  absent, 5-lever once EDGAR COGS lands. Reuses `attribute_eps_error` /
  EFE-1 waterfall unchanged apart from the lever count.

### NVDA-3: Reporting parity (sandbox)
- Generic branch in `output/html_builder.py` + `plotly_charts.py`: fan,
  scenario compare, risk band, attribution waterfall, consensus gap table.
  Keep MD as the fallback. Same "사후 귀인 — 예측 신호 아님" labeling contract.

Priority: NVDA-1 ≫ NVDA-2 > NVDA-3. NVDA-1 is prerequisite — every metric
computed before it is polluted by the split artifact and circularity.

## 6. Risks
- **Regime non-stationarity:** a backtest window straddling FY2023 punishes any
  constant-margin model; report split-window metrics (pre/post 2023Q1) rather
  than blending, or start the scored window at 2023Q2.
- **Fiscal offset:** silently joining calendar-labeled model quarters to Yahoo
  fiscal quarters would corrupt the consensus gap — make the mapping explicit
  and tested.
- **Attribution mis-read:** on the generic path the "opex" lever does not exist
  (no GP decomposition); label levers accordingly so the waterfall never implies
  a decomposition the model didn't make.
- Keep generic ↔ memory paths fully separated (HANDOFF design contract);
  the 9Q SK Hynix invariant must stay bit-identical through all three
  workstreams (baseline sha256 recorded 2026-07-10).

## 7. Verification
- `pytest tests/test_generic_forecast.py -q` + new fetcher/alignment tests.
- `python generic_cli.py --profile profiles/nvda.generic.yaml` before/after
  NVDA-1 — record bias collapse in the HANDOFF.
- Memory path regression: `pytest -q` full suite + 9Q backtest sha256 match.
