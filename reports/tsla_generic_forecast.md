# 테슬라 (Tesla, Inc.) — 실적 전망 (Generic)

- 티커: `TSLA` · 통화: USD (USD_million) · 희석주식수: 3,538,000,000
- 시드 분기: 2026Q1 (매출 22,387)
- 전망 구간: 2026Q2부터 4개 분기

## 확률가중 분기 전망

| 분기 | 매출 | 영업이익 | 순이익 | EPS(희석) |
|---|---:|---:|---:|---:|
| 2026Q2 | 21,268 | 1,349 | 1,424 | 0.40 |
| 2026Q3 | 22,359 | 1,437 | 1,514 | 0.43 |
| 2026Q4 | 24,204 | 1,575 | 1,656 | 0.47 |
| 2027Q1 | 26,713 | 1,759 | 1,847 | 0.52 |

## 연간 EPS (시나리오별)

| FY | Bear | Base | Bull | 가중 |
|---|---:|---:|---:|---:|
| 2026 | 0.64 | 1.22 | 2.12 | 1.30 |
| 2027 | 0.23 | 0.48 | 0.90 | 0.52 |

## 오프라인 백테스트 (1-step, seasonally-aware)

- **Post-break (headline)** · N=12 (EPS 12) · 매출 MAPE 11.7% / bias +5.5% · EPS MAPE 71.9% / bias +43.0%
  - RW MAPE 매출 12.4% / EPS 123.0% · MASE 매출 0.949 / EPS 0.665 · Theil U2 매출 0.935 / EPS 0.712 · consensus N=0
- **Full window** · N=26 (EPS 26) · 매출 MAPE 10.8% / bias +0.0% · EPS MAPE 196.4% / bias +150.5%
  - RW MAPE 매출 13.2% / EPS 101.4% · MASE 매출 0.846 / EPS 0.991 · Theil U2 매출 0.874 / EPS 0.829 · consensus N=0
- **Pre-break** · N=14 (EPS 14) · 매출 MAPE 10.0% / bias -4.6% · EPS MAPE 303.1% / bias +242.6%
  - RW MAPE 매출 13.8% / EPS 82.9% · MASE 매출 0.708 / EPS 1.830 · Theil U2 매출 0.737 / EPS 1.827 · consensus N=0

## 데이터 출처 / 주의

- actuals는 EDGAR companyfacts as-filed 원본 공시 기준 공식 분기 GAAP (10-Q; Q4는 동일 회계연도 10-K 연간 − Q3 10-Q 9M 차감 복원). 구 프로파일의 NI/EPS LOW-CONFIDENCE 추정 해소 (NVDA-1 세션, 2026-07-11).
- 과거 EPS는 로드 시 파생: net_profit ÷ (as-filed 분기별 희석주식수 × split_history 조정, 현재 기준). FY2024 분기는 FY2025 공시에서 소급 재작성됨 — as-filed 원본 유지(point-in-time 백테스트 정합).
- 테슬라는 규제 크레딧·기타수익 변동으로 순이익 예측 오차가 큼 — 결과 해석 주의(마진 가정 신뢰도 낮음).
- FSD/로보택시 옵션가치는 top-down 마진 모델로 포착 불가 — BVT 옵셔널리티 SOTP 참조.

_시나리오 확률: bear 25% / base 50% / bull 25%_
