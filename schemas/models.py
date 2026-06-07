"""Pydantic v2 schemas for the earnings forecast engine.

All engine/pipeline functions accept and return these models.
DataFrames are intentionally avoided to keep types explicit and serializable.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Company meta
# ---------------------------------------------------------------------------

class CompanyMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    name_kr: str
    ticker_yahoo: str
    corp_code_dart: str
    currency: str = "KRW"
    fiscal_year_end_month: int = Field(..., ge=1, le=12)
    reporting_unit: Literal["KRW", "KRW_million", "KRW_billion", "USD", "USD_million"]


class SharesOutstanding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    weighted_avg_basic: int
    weighted_avg_diluted: int
    treasury_shares: int = 0
    source: str = ""


# ---------------------------------------------------------------------------
# Assumptions (input to engine)
# ---------------------------------------------------------------------------

class SegmentAssumptions(BaseModel):
    """Single-scenario segment-level driver assumptions for N quarters."""

    model_config = ConfigDict(extra="forbid")

    # DRAM
    dram_bit_growth_qoq: list[float]
    dram_hbm_share_qoq: list[float]
    dram_hbm_asp_yoy: float
    dram_ddr_asp_qoq: list[float]

    # NAND
    nand_bit_growth_qoq: list[float]
    nand_asp_qoq: list[float]

    # Other
    other_revenue_growth_qoq: list[float]

    @field_validator(
        "dram_bit_growth_qoq",
        "dram_hbm_share_qoq",
        "dram_ddr_asp_qoq",
        "nand_bit_growth_qoq",
        "nand_asp_qoq",
        "other_revenue_growth_qoq",
    )
    @classmethod
    def _must_be_non_empty(cls, v: list[float]) -> list[float]:
        if not v:
            raise ValueError("driver list must contain at least one quarter")
        return v


class MarginAssumptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sga_pct_of_revenue: float
    rnd_pct_of_revenue: float


class AnchorMargins(BaseModel):
    """Scenario-independent historical margin anchor for the cost-per-bit chain."""

    model_config = ConfigDict(extra="forbid")

    gm_hbm: float = Field(..., ge=-1.0, le=1.0)
    gm_ddr: float = Field(..., ge=-1.0, le=1.0)
    gm_nand: float = Field(..., ge=-1.0, le=1.0)
    gm_other: float = Field(..., ge=-1.0, le=1.0)
    cost_decline_qoq_hbm: float = Field(default=0.0, ge=0.0, lt=1.0)
    cost_decline_qoq_ddr: float = Field(default=0.0, ge=0.0, lt=1.0)
    cost_decline_qoq_nand: float = Field(default=0.0, ge=0.0, lt=1.0)


class MarginCarryover(BaseModel):
    """ASP factors carried from the historical anchor into the forward window."""

    model_config = ConfigDict(extra="forbid")

    asp_hbm: float = Field(default=1.0, gt=0.0)
    asp_ddr: float = Field(default=1.0, gt=0.0)
    asp_nand: float = Field(default=1.0, gt=0.0)
    periods_since_anchor: int = Field(default=0, ge=0)


class HistoricalDriver(BaseModel):
    """Historical quarter-specific drivers used by backtest."""

    model_config = ConfigDict(extra="forbid")

    quarter_label: str
    hbm_share: float = Field(..., ge=0.0, le=1.0)
    hbm_asp_qoq: float = 0.0
    ddr_asp_qoq: float = 0.0
    nand_asp_qoq: float = 0.0
    gm_overrides: dict[str, float] | None = None


class FinanceAssumptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    effective_tax_rate: float = Field(..., ge=0.0, le=1.0)
    net_interest_pct_of_revenue: float


class MarginBaseline(BaseModel):
    """Prior 4Q averages used as baseline for cyclical margin function."""

    model_config = ConfigDict(extra="forbid")

    gp_margin: float | None = None
    op_margin: float | None = None
    np_margin: float | None = None
    dram_blended_asp: float | None = None
    nand_blended_asp: float | None = None
    capex_krw_bn: float | None = None


# ---------------------------------------------------------------------------
# Quarterly data (actual + forecast share the same shape)
# ---------------------------------------------------------------------------

class SegmentForecast(BaseModel):
    model_config = ConfigDict(extra="forbid")

    segment_id: str
    revenue: float


class QuarterlyActual(BaseModel):
    """Historical quarterly result from DART. Used for backtest and baseline."""

    model_config = ConfigDict(extra="forbid")

    quarter_label: str  # e.g., "2025Q4"
    period_end: date

    revenue_total: float
    revenue_by_segment: list[SegmentForecast]

    gross_profit: float
    operating_profit: float
    net_profit: float

    eps_basic: float | None = None
    eps_diluted: float | None = None


class QuarterlyForecast(BaseModel):
    """Forward projection. Same shape as QuarterlyActual but with scenario tag."""

    model_config = ConfigDict(extra="forbid")

    quarter_label: str
    scenario: Literal["bear", "base", "bull", "weighted"] = "base"

    revenue_total: float
    revenue_by_segment: list[SegmentForecast]
    hbm_share: float = Field(default=0.0, ge=0.0, le=1.0)
    asp_hbm: float = Field(default=1.0, gt=0.0)
    asp_ddr: float = Field(default=1.0, gt=0.0)
    asp_nand: float = Field(default=1.0, gt=0.0)
    margin_periods_since_anchor: int = Field(default=1, ge=0)

    gross_profit: float
    operating_profit: float
    net_profit: float

    gp_margin: float
    op_margin: float
    np_margin: float

    eps_basic: float | None = None
    eps_diluted: float | None = None


class AnnualForecast(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fiscal_year: int
    scenario: Literal["bear", "base", "bull", "weighted"] = "base"
    revenue_total: float
    operating_profit: float
    net_profit: float
    eps_basic: float | None = None


# ---------------------------------------------------------------------------
# Scenario tree
# ---------------------------------------------------------------------------

class ScenarioProbabilities(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bear: float = Field(..., ge=0.0, le=1.0)
    base: float = Field(..., ge=0.0, le=1.0)
    bull: float = Field(..., ge=0.0, le=1.0)

    @field_validator("bull")
    @classmethod
    def _must_sum_to_one(cls, v: float, info) -> float:
        bear = info.data.get("bear", 0.0)
        base = info.data.get("base", 0.0)
        total = bear + base + v
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"scenario probabilities must sum to 1.0 (got {total})")
        return v


class ScenarioCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario: Literal["bear", "base", "bull"]
    probability: float
    rationale: str
    quarterly: list[QuarterlyForecast]
    annual: list[AnnualForecast]


class ScenarioTree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company: CompanyMeta
    as_of: date

    bear: ScenarioCase
    base: ScenarioCase
    bull: ScenarioCase

    weighted_quarterly: list[QuarterlyForecast]
    weighted_annual: list[AnnualForecast]


# ---------------------------------------------------------------------------
# Consensus
# ---------------------------------------------------------------------------

class ConsensusRecord(BaseModel):
    """Snapshot of analyst consensus from yfinance."""

    model_config = ConfigDict(extra="forbid")

    ticker: str
    as_of: date

    # quarter_label -> consensus value
    revenue_estimate_quarterly: dict[str, float | None]
    eps_estimate_quarterly: dict[str, float | None]
    revenue_estimate_annual: dict[int, float | None]   # fiscal_year -> value
    eps_estimate_annual: dict[int, float | None]

    # Historical (prior 4Q): {quarter_label: {actual, estimate, surprise_pct}}
    history: dict[str, dict[str, float | None]] = Field(default_factory=dict)

    notes: list[str] = Field(default_factory=list)


class ConsensusGap(BaseModel):
    """Model (base case) vs consensus, per period."""

    model_config = ConfigDict(extra="forbid")

    period_label: str        # "2026Q1" or "FY26"
    metric: Literal["revenue", "eps"]

    model_value: float
    consensus_value: float | None
    gap_abs: float | None
    gap_pct: float | None
    direction: Literal["above", "below", "in_line", "n_a"]

    interpretation: str = ""  # user fills in; engine leaves empty


# ---------------------------------------------------------------------------
# Backtest
# ---------------------------------------------------------------------------

class BacktestQuarter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quarter_label: str
    actual_revenue: float
    model_revenue: float
    revenue_error_pct: float

    actual_eps: float | None
    model_eps: float | None
    eps_error_pct: float | None

    direction_match: bool   # model predicted same sign of QoQ change as actual


class BacktestResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lookback_quarters: int
    quarters: list[BacktestQuarter]

    revenue_mape: float
    eps_mape: float | None
    hit_ratio_direction: float
    bias_revenue: float   # avg signed error %
    bias_eps: float | None


# ---------------------------------------------------------------------------
# Consensus signal layer (Phase B)
# ---------------------------------------------------------------------------

DisclosureSource = Literal["dart_mdna", "ir_deck", "fair_disclosure"]
SignalTone = Literal["up", "flat", "down"]


class DisclosureDocument(BaseModel):
    """Raw narrative text of one disclosure/IR document (input to extraction).

    Carries no interpretation — only the source text and provenance needed to
    align it to an earnings event (T0) without look-ahead.
    """

    model_config = ConfigDict(extra="forbid")

    source: DisclosureSource
    doc_date: date           # publication date (used for look-ahead checks)
    period_label: str        # reporting period the text describes, e.g. "2025Q4"
    raw_text: str
    char_count_kr: int = 0   # Korean-character count (sanity check, not OCR scan)
    url_or_path: str = ""    # DART rcpNo URL or local deck PDF path


class TopicEmphasis(BaseModel):
    """One topic the disclosure text emphasizes, with salience and polarity."""

    model_config = ConfigDict(extra="forbid")

    topic: str
    salience: float = Field(..., ge=0.0, le=1.0)
    polarity: Literal["positive", "neutral", "negative"]
    evidence_quote: str = ""


class ExtractedSignal(BaseModel):
    """Deterministic, validated structured signal from one DisclosureDocument.

    Produced by engine.signal_extractor from the raw LLM extraction. Holds no
    interpretation field — narrative reading is the user's, not the engine's.
    """

    model_config = ConfigDict(extra="forbid")

    period_label: str
    source: DisclosureSource
    topics: list[TopicEmphasis]
    guidance_tone: SignalTone
    surprise_candidates: list[str] = Field(default_factory=list)
    extracted_at: date
    model_id: str


class CallBrief(BaseModel):
    """Forward earnings-call pre-briefing: what to watch and ask next quarter."""

    model_config = ConfigDict(extra="forbid")

    as_of: date
    target_event_label: str           # the upcoming event, e.g. "2026Q2"
    top_topics: list[TopicEmphasis]
    expected_qna: list[str] = Field(default_factory=list)
    dispersion_flags: list[str] = Field(default_factory=list)
    predicted_revision_direction: Literal["up", "flat", "down", "n_a"] = "n_a"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    interpretation: str = ""          # user fills in; engine leaves empty


class SignalEventResult(BaseModel):
    """One backtest event: text signal at T0 vs realized market-adjusted CAR."""

    model_config = ConfigDict(extra="forbid")

    event_label: str
    t0: date

    car_t1: float | None = None       # CAR[T0 -> T+1d], market-adjusted
    car_t5: float | None = None       # CAR[T0 -> T+5d], secondary

    signal_tone: SignalTone
    signal_score: float               # salience-weighted tone, continuous (for IC)
    predicted_sign: int               # +1 / 0 / -1 from signal_tone

    realized_sign_t1: int | None = None   # sign(car_t1)
    direction_match_t1: bool | None = None


class SignalBacktestResult(BaseModel):
    """Event-study summary over SK Hynix earnings events (small-sample by design)."""

    model_config = ConfigDict(extra="forbid")

    events: list[SignalEventResult]
    sample_n: int
    directional_hit_ratio: float
    information_coefficient: float | None = None   # Spearman rank corr (signal vs CAR)
    calibration: dict[str, float] = Field(default_factory=dict)
    window_primary: str = "T+1d"
