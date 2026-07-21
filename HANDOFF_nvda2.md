# HANDOFF — NVDA-2 stage 2a: skill metrics + regime windows

Date: 2026-07-21
Scope: `PLAN_nvda2.md` rev-1 §2a only
Baseline: `2ac4d58`; docs housekeeping commit `3710248`

## 1. Delivered contracts

- Generic backtest rows map 1:1 to shared `SkillRow`; `compute_skill` remains
  unchanged. Legacy MAPE fields remain percent while `skill` MAPE fields remain
  0–1 ratios. The report owns the single ratio-to-percent formatting site.
- `GenericProfile.regime_break_quarter` is optional and `extra="forbid"`
  remains active. NVDA/TSLA set `2023Q2`, with the AI-supercycle sourcing
  comment required by `REVIEW_nvda2_codex.md` §1.2.
- Profiles with a regime break emit `windows.full/pre_break/post_break`; each
  contains rows, `n`, `n_eps`, percent MAPE/bias, and ratio-based skill.
  Profiles without the field emit no `windows` key.
- The generic signal uses post-break as its primary skill window and takes its
  trailing 8Q from inside post-break. Full-vs-primary disagreement is explicit.
  Profiles without regime windows retain full/trailing behavior.
- Historical model EPS uses prior-quarter as-filed diluted shares adjusted to
  the current split basis. Legacy rows without shares explicitly fall back to
  the fixed forward count. The forward forecast still uses its fixed share
  assumption.
- Consensus-dependent skill fields are `None`/N=0 in stage 2a.

## 2. Verification

### Tests

| Check | Before | After |
|---|---:|---:|
| Full pytest | 164 passed | 173 passed |
| Added tests | — | 9 |
| Targeted 2a + adjacent suites | — | 27 passed |

`python -m pytest -q`: **173 passed in 25.77s**.

New tests cover NVDA/TSLA legacy-to-skill unit equivalence, exact row/count/APE
partition identity, 2023Q2 boundary placement, signal primary/fallback behavior,
split-adjusted prior shares, fixed-share fallback, and report percent rendering.
The existing schema test continues to verify that `diluted_shares` without
`period_end` fails validation.

### Memory-path invariant

No memory-path file differs from `2ac4d58`:

```text
git diff 2ac4d58 -- engine/backtest.py schemas/models.py profiles/sk_hynix.yaml pipeline/ir_loader.py pipeline/dart_fetcher.py pipeline/consensus_loader.py
# no output
```

The 9Q core values reproduce the NVDA-1 handoff exactly: revenue MAPE 8.99%,
EPS MAPE 10.39%, EPS bias -3.58%. The documented SHA
`077ecb10986a5f2a7e81b31dc595ae47077b8ed7d6fb3ababfb1d5073891933c`
did **not** reproduce from the currently available caches: every stored Yahoo
vintage produced `b979d79f...f6e7`; `consensus_history=None` produced
`eb6688a1...2674`. Because all memory-path inputs/code tracked by git are
unchanged, this is an undocumented hash-fixture/vintage reproduction gap, not
a generic-path code diff. Cowork must independently run its canonical SHA
recipe before PASS.

## 3. Before/after measurements

All error MAPE/bias columns are percent. MASE and Theil U2 are ratios. These are
stage measurements only; PLAN's full-companyfacts host gate still prohibits
external metric quotation.

### NVDA

| Window | N | Rev MAPE | Rev bias | EPS MAPE | EPS bias | MASE rev | MASE EPS | Theil rev | Theil EPS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Full before | 26 | 9.92 | -4.11 | 94.97 | +81.54 | 0.609 | 1.081 | 0.628 | 1.043 |
| Full after | 26 | 9.92 | -4.11 | 91.59 | +77.37 | 0.609 | 1.081 | 0.628 | 1.038 |
| Pre before | 14 | 8.56 | +1.97 | 162.19 | +162.19 | 0.754 | 3.729 | 0.990 | 3.328 |
| Pre after | 14 | 8.56 | +1.97 | 155.25 | +155.25 | 0.754 | 3.537 | 0.990 | 3.175 |
| Post before | 12 | 11.50 | -11.20 | 16.55 | -12.55 | 0.592 | 0.817 | 0.621 | 0.998 |
| Post after | 12 | 11.50 | -11.20 | 17.31 | -13.49 | 0.592 | 0.836 | 0.621 | 0.998 |

Share convention: fixed forward 24.49B before → prior-quarter split-adjusted
as-filed shares after. All 26 after rows report
`prior_quarter_split_adjusted`; no fallback was needed.

Signal after: primary=`post_break`, N=12, skill pass=true; full EPS MAPE does
not beat RW while post-break does, so `full_vs_primary_disagreement=true`.

### TSLA

| Window | N | Rev MAPE | Rev bias | EPS MAPE | EPS bias | MASE rev | MASE EPS | Theil rev | Theil EPS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Full before | 26 | 10.76 | +0.04 | 161.62 | +114.23 | 0.846 | 0.989 | 0.874 | 0.834 |
| Full after | 26 | 10.76 | +0.04 | 196.43 | +150.48 | 0.846 | 0.991 | 0.874 | 0.829 |
| Pre before | 14 | 9.98 | -4.61 | 238.32 | +176.09 | 0.708 | 1.807 | 0.737 | 1.849 |
| Pre after | 14 | 9.98 | -4.61 | 303.14 | +242.63 | 0.708 | 1.830 | 0.737 | 1.827 |
| Post before | 12 | 11.67 | +5.46 | 72.12 | +42.05 | 0.949 | 0.671 | 0.935 | 0.715 |
| Post after | 12 | 11.67 | +5.46 | 71.94 | +42.98 | 0.949 | 0.665 | 0.935 | 0.712 |

Share convention: fixed forward 3.538B before → prior-quarter split-adjusted
as-filed shares after. All 26 after rows report
`prior_quarter_split_adjusted`; no fallback was needed. The much worse early
window EPS percentage errors are measured consequences of removing the fixed
forward-share wedge, not presumed targets.

Signal after: primary=`post_break`, N=12, skill pass=true; full EPS MAPE does
not beat RW while post-break does, so `full_vs_primary_disagreement=true`.

## 4. CLI/report behavior

```text
NVDA: backtest post-break N=12, revenue MAPE 11.5%, EPS MAPE 17.3%
TSLA: backtest post-break N=12, revenue MAPE 11.7%, EPS MAPE 71.9%
```

Both JSON files preserve top-level legacy metrics plus `skill`, `rows`, and all
three windows. Markdown reports show post-break first, retain full/pre windows,
display `n`/`n_eps`, MASE/Theil, ratio-derived RW MAPE percentages, and
consensus N=0.

## 5. Scope boundary

No 2b fiscal consensus normalization or 2c attribution work was started.
