# Earnings Forecast Engine — Project Memory

## Purpose
분기·연간 EPS forward 모델 + 컨센서스 갭 + backtest. **마이다스에셋자산운용 리서치 면접 (2026-05-18) 후속**으로 시작 — 입사 후 6개월 목표("컨센과 본질가치 괴리 탐색")를 산출물로 뒷받침. 단, 다른 운용사·증권사 직무에도 재활용 가능한 일반 자산.

## Sibling Repos
- `F:\dev\Portfolio\business-valuation-tool` (BVT) — 정적 valuation 7엔진, growth는 CAGR-fade 수준
- `F:\dev\Portfolio\fx-reserves-analyzer` — 거시 VAR/FEVD
- 본 repo는 BVT growth/DCF의 forward earnings 보완

## Structure
```
earnings-forecast-engine/
├── cli.py                    # 진입점
├── profiles/sk_hynix.yaml    # 회사별 가정 (BVT profiles/ 패턴)
├── engine/                   # 순수 함수 (IO 없음)
├── pipeline/                 # IO 전용 (Yahoo·DART)
├── schemas/models.py         # Pydantic v2 (BVT 단일 파일 패턴)
├── output/                   # HTML(primary) + MD + xlsx + 차트
├── tests/                    # pytest
└── docs/                     # methodology, thesis, AI collaboration
```

## Conventions
- 코드·docstring·주석: 영어
- 사용자 대면 출력 (리포트·터미널): 한국어
- Pydantic v2, no DataFrames in engine returns (Pydantic 모델만)
- 가정 수치는 모두 `profiles/*.yaml` — 코드 하드코딩 금지
- 파일 IO 시 `encoding='utf-8'` 명시 (Windows cp949 회피)

## Data Sources
- **Yahoo Finance** (yfinance) — 컨센서스·실적·주가. `000660.KS` 등 KS 티커.
- **DART OpenAPI** — 분기 재무제표. corp_code 캐시: SK하이닉스 = `00164779`.
- **수동 IR 가정** — `profiles/{company}.yaml` 의 `assumptions:` 섹션.

## AI Collaboration Split (BVT와 동일)
- **사람**: 방법론 선정·가정 수치·결과 해석·thesis 작성·면접 답변
- **Codex CLI**: 코드 구현·리팩토링·테스트·Pydantic 스키마·템플릿 보일러플레이트
- README·`docs/ai_collaboration.md`에 명시. CLAUDE.md·AGENTS.md·`.codex/` 메타 디렉토리 삭제 금지 (2026-04-27 사용자 방침).

## Workflow
1. Claude Code: scaffold 단계 (현재 완료) — 디렉토리·핸드오프 docs·시그니처
2. Codex CLI: 함수 본문·테스트 구현 — `AGENTS.md` 참고
3. 사용자: 가정 수치 입력·시나리오 확률 조정·thesis 작성·결과 해석
4. 동기화: `career/profile.md`·`portfolio-summary.md`·`facts-verified.md` 에 본 repo 항목 추가

## Gotchas
- ASCII path 필수 — Codex는 한글 경로(`C:\Users\김지원`)에서 silent fail
- 임시 작업은 `C:/temp/earnings_forecast/` 격리 (다른 자소서 세션과 충돌 회피)
- Yahoo `.KS` 티커는 일부 필드 sparse — `null` 처리 + "consensus unavailable" 경고
- Plotly 단일 HTML 파일 < 5MB 유지 — Malgun.ttf 임베드 금지, 시스템 폰트만 사용
- DART API rate limit: 분당 1000회 — `httpx` retry/backoff 필요

## Verification
- `pytest -q` — 엔진별 유닛 테스트
- `python cli.py --company sk_hynix --dry-run` — fixture로 외부 API 없이 리포트 생성
- `python cli.py --company sk_hynix` — 실 데이터 호출, HTML 산출물 브라우저 점검
- 8Q backtest MAPE: 매출 < 10%, EPS < 25% 미달 시 가정 재검토
- 모델-컨센 gap이 모든 분기 < 5%면 "내 view 없음" 신호 → thesis 재작성

## Plan Reference
원안: `C:\Users\김지원\.claude\plans\glittery-juggling-candle.md`
