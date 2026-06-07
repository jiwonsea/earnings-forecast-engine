# Earnings Forecast Engine

분기·연간 EPS forward 모델 + 컨센서스 갭 분석 + 직전 4Q backtest. 현재 커버: SK하이닉스 (`000660.KS`).

## Why

정적 valuation 도구([business-valuation-tool](https://github.com/jiwonsea/Business-Valuation-Tool))는 SOTP·DCF·rNPV 등 7개 엔진을 갖추고 있으나, growth는 CAGR-fade 가정 수준에 머물러 있습니다. 본 프로젝트는 **라인별 P&L 예측 → 컨센서스 비교 → 직전 분기 backtest → BVT DCF로의 sensitivity bridge** 까지의 사이클을 채워 forward earnings 분석을 산출물 단위로 만듭니다.

## Quickstart

```bash
git clone https://github.com/jiwonsea/earnings-forecast-engine
cd earnings-forecast-engine
pip install -r requirements.txt
cp .env.example .env   # DART_API_KEY 입력
python cli.py --company sk_hynix
```

`reports/sk_hynix_YYYYMMDD.html` (인터랙티브 primary) + `.md` (요약·인용용) + `.xlsx` (raw) 가 생성됩니다.

## Methodology

자세한 드라이버 분해 로직은 [docs/methodology.md](docs/methodology.md) 참조. 요약:

- 매출 = Σ (세그먼트 bit volume × blended ASP). SK하이닉스는 DRAM(HBM + DDR)·NAND 분해.
- 마진 = **cost-per-bit operating-leverage** 모델: `GP_margin_s = 1 − cost_per_bit_s / ASP_s`. ASP가 bit당 원가보다 빠르게 오르면 마진 확장(피크), 반대면 음수(트로프) — 메모리 가격 사이클을 구조적으로 포착. HBM mix는 세그먼트 매출 가중으로 반영.
- 시나리오 = Bear(25%) / Base(50%) / Bull(25%), 확률 가중 EPS 산출.
- Backtest = 직전 8분기 retrospective. **비순환**: 마진·매출 모두 `historical_drivers`의 **실현 시장 ASP**(TrendForce 등 독립 관측)를 입력으로 쓰고, bit growth는 가정(시험 대상). 회사 실현 매출은 비교에만 사용.
- Consensus 갭 = Yahoo Finance `earnings_estimate` / `revenue_estimate` 대비 차이 + 방향성 해석. (⚠️ `.KS` 컨센은 신뢰도 제한 — 한국 broker 컨센 통합은 P1.)

## Sample Output

[**▶ 인터랙티브 HTML 데모**](reports/sk_hynix_latest.html) (브라우저로 열어주세요 — Plotly hover·scenario 토글·sortable table)

- 정적 fan chart 미리보기: `reports/sk_hynix_latest_fan.png`
- 8Q backtest 표: `reports/sk_hynix_latest_backtest.md`

## Backtest Performance

8Q rolling backtest (2024Q1–2025Q4), sourced-draft 가정 기준:

| Metric | Target | 현재 | 
|--------|--------|------|
| 매출 MAPE | < 10% | **9.5%** ✅ |
| EPS MAPE | < 25% | **12.6%** ✅ |
| Hit ratio (방향) | > 60% | **87.5%** ✅ |
| EPS bias (부호) | \|값\| < 5% | **−0.2%** ✅ |

수치는 `profiles/sk_hynix.yaml`의 가정에 따라 변하며, 가정은 출처 기반 초안(사용자 확정 대상)입니다. 상세 표는 매 실행마다 `reports/sk_hynix_YYYYMMDD.md` 에 갱신.

## Roadmap

- **P1**: 삼성전자 (`005930.KS`), 도쿄일렉트론 (`8035.T`) 확장
- **P1**: 한국 broker 컨센서스 통합 (네이버 금융·FnGuide)
- **P2**: BVT와 양방향 어댑터 — forecast → DCF fair value auto-update
- **P2**: Streamlit dashboard

## AI Collaboration

본 프로젝트는 사람(분석가)과 두 AI 도구(Claude Code · Codex CLI)의 협업으로 구축됩니다.

- **사람 (본인)**: 전략·방법론 의사결정, **가정 수치 검토·확정·소유**, 결과 해석, thesis, 면접 방어.
- **Claude Code**: 시장 데이터 기반 가정 **초안**(출처 명시), **검증·QA**(silent failure 적발), 방법론 설계·핸드오프, 백테스트 비순환 규율.
- **Codex CLI**: 함수 본문 구현·테스트·리팩토링.

가정은 AI가 출처 기반으로 **초안**하되 분석가가 검토·확정·소유합니다. 상세·정직성 기준: [docs/ai_collaboration.md](docs/ai_collaboration.md).

## Scope (정직성)

매출/마진 **모델은 메모리 반도체에 특화**(DRAM/HBM/NAND · bit×ASP · cost-per-bit). 파이프라인·시나리오·백테스트·방법론 규율은 **재사용 가능** — 메모리 동종(삼성·Micron)은 새 profile로 거의 그대로, 비메모리는 매출/마진 엔진 재설계 필요. "범용 실적 엔진"이 아니라 **메모리 forward 모델 + 재사용 가능한 방법론·배관**입니다.

## License

MIT
