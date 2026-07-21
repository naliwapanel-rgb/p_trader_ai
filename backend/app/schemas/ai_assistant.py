from typing import (
    Any,
    Literal,
)
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)
from app.schemas.market_scanner import (
    MarketCategory,
)
from app.schemas.portfolio_sync import (
    PortfolioSyncSnapshotResponse,
)
from app.schemas.risk_management import (
    PreTradeRiskResult,
)
AIAnalysisType = Literal[
    "GENERAL",
    "MARKET",
    "PORTFOLIO",
    "RISK",
    "TRADE_PLAN",
    "ARBITRAGE",
]
AIAnalysisStatus = Literal[
    "SUCCESS",
    "PARTIAL",
    "UNAVAILABLE",
]
AIWarningSeverity = Literal[
    "INFO",
    "WARNING",
    "CRITICAL",
]
AITradeSide = Literal[
    "BUY",
    "SELL",
]
AIArbitrageOpportunityType = Literal[
    "CROSS_EXCHANGE",
    "TRIANGULAR",
]
AIDataSource = Literal[
    "CONVERSATION_HISTORY",
    "USER_QUERY",
    "MARKET_SCANNER",
    "PORTFOLIO",
    "RISK_ENGINE",
    "ARBITRAGE_ENGINE",
    "AUTOMATION_RUNTIME",
    "WATCHLIST",
    "ALERTS",
]
class AIQuestionRequest(BaseModel):
    question: str = Field(
        min_length=2,
        max_length=4000,
    )
    @field_validator("question")
    @classmethod
    def normalize_question(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError(
                "question cannot be blank"
            )
        return normalized
class AIAssistantRequest(
    AIQuestionRequest
):
    include_conversation_history: bool = True
    conversation_history_limit: int = Field(
        default=12,
        ge=1,
        le=50,
    )

    conversation_id: int | None = Field(
        default=None,
        gt=0,
    )
    persist_conversation: bool = False

    analysis_type: AIAnalysisType = (
        "GENERAL"
    )
    symbols: list[str] = Field(
        default_factory=list,
        max_length=25,
    )
    portfolio_id: int | None = Field(
        default=None,
        gt=0,
    )
    exchange_account_id: (
        int | None
    ) = Field(
        default=None,
        gt=0,
    )
    include_user_context: bool = True
    @field_validator("symbols")
    @classmethod
    def normalize_symbols(
        cls,
        values: list[str],
    ) -> list[str]:
        normalized: list[str] = []
        for value in values:
            symbol = value.strip().upper()
            if not symbol:
                raise ValueError(
                    "symbols cannot contain "
                    "blank values"
                )
            if symbol not in normalized:
                normalized.append(symbol)
        return normalized
class AIMarketAnalysisRequest(
    AIQuestionRequest
):
    exchange: Literal["BYBIT"] = "BYBIT"
    category: MarketCategory = "spot"
    symbols: list[str] = Field(
        min_length=1,
        max_length=25,
    )
    scan_limit: int = Field(
        default=10,
        ge=1,
        le=50,
    )
    include_order_book_metrics: bool = (
        False
    )
    @field_validator("symbols")
    @classmethod
    def normalize_market_symbols(
        cls,
        values: list[str],
    ) -> list[str]:
        normalized: list[str] = []
        for value in values:
            symbol = value.strip().upper()
            if not symbol:
                raise ValueError(
                    "symbols cannot contain "
                    "blank values"
                )
            if symbol not in normalized:
                normalized.append(symbol)
        return normalized
class AIPortfolioAnalysisRequest(
    AIQuestionRequest
):
    portfolio_id: int | None = Field(
        default=None,
        gt=0,
    )
    exchange_account_id: (
        int | None
    ) = Field(
        default=None,
        gt=0,
    )
    include_positions: bool = True
    include_open_orders: bool = True
    include_allocation_analysis: bool = (
        True
    )
class AIRiskExplanationRequest(
    AIQuestionRequest
):
    risk_result: PreTradeRiskResult
class AITradePlanRequest(
    AIQuestionRequest
):
    symbol: str = Field(
        min_length=2,
        max_length=30,
    )
    side: AITradeSide
    exchange: Literal["BYBIT"] = "BYBIT"
    category: MarketCategory = "linear"
    reference_entry_price: (
        float | None
    ) = Field(
        default=None,
        gt=0,
    )
    reference_stop_loss_price: (
        float | None
    ) = Field(
        default=None,
        gt=0,
    )
    reference_take_profit_price: (
        float | None
    ) = Field(
        default=None,
        gt=0,
    )
    maximum_risk_percent: (
        float | None
    ) = Field(
        default=None,
        gt=0,
        le=100,
    )
    @field_validator("symbol")
    @classmethod
    def normalize_trade_symbol(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError(
                "symbol cannot be blank"
            )
        return normalized
    @model_validator(mode="after")
    def validate_reference_levels(self):
        entry_price = (
            self.reference_entry_price
        )
        stop_loss = (
            self.reference_stop_loss_price
        )
        take_profit = (
            self.reference_take_profit_price
        )
        if (
            entry_price is None
            and (
                stop_loss is not None
                or take_profit is not None
            )
        ):
            raise ValueError(
                "reference_entry_price is "
                "required when stop-loss or "
                "take-profit levels are provided"
            )
        if entry_price is None:
            return self
        if self.side == "BUY":
            if (
                stop_loss is not None
                and stop_loss >= entry_price
            ):
                raise ValueError(
                    "BUY reference stop-loss "
                    "must be below entry price"
                )
            if (
                take_profit is not None
                and take_profit <= entry_price
            ):
                raise ValueError(
                    "BUY reference take-profit "
                    "must be above entry price"
                )
        if self.side == "SELL":
            if (
                stop_loss is not None
                and stop_loss <= entry_price
            ):
                raise ValueError(
                    "SELL reference stop-loss "
                    "must be above entry price"
                )
            if (
                take_profit is not None
                and take_profit >= entry_price
            ):
                raise ValueError(
                    "SELL reference take-profit "
                    "must be below entry price"
                )
        return self
class AIArbitrageExplanationRequest(
    AIQuestionRequest
):
    opportunity_type: (
        AIArbitrageOpportunityType
    )
    opportunity: dict[str, Any]
    @model_validator(mode="after")
    def require_opportunity_data(self):
        if not self.opportunity:
            raise ValueError(
                "opportunity cannot be empty"
            )
        return self
class AIAnalysisWarning(BaseModel):
    code: str = Field(
        min_length=2,
        max_length=100,
    )
    severity: AIWarningSeverity = (
        "WARNING"
    )
    message: str = Field(
        min_length=2,
        max_length=1000,
    )
    @field_validator("code")
    @classmethod
    def normalize_warning_code(
        cls,
        value: str,
    ) -> str:
        normalized = (
            value.strip()
            .upper()
            .replace(" ", "_")
            .replace("-", "_")
        )
        if not normalized:
            raise ValueError(
                "warning code cannot be blank"
            )
        return normalized
    @field_validator("message")
    @classmethod
    def normalize_warning_message(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError(
                "warning message cannot "
                "be blank"
            )
        return normalized
class AIAnalysisSection(BaseModel):
    title: str = Field(
        min_length=2,
        max_length=150,
    )
    summary: str = Field(
        min_length=2,
        max_length=4000,
    )
    bullet_points: list[str] = Field(
        default_factory=list,
        max_length=50,
    )
    metrics: dict[str, Any] = Field(
        default_factory=dict
    )
    @field_validator("title", "summary")
    @classmethod
    def normalize_section_text(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError(
                "section text cannot be blank"
            )
        return normalized
    @field_validator("bullet_points")
    @classmethod
    def normalize_bullet_points(
        cls,
        values: list[str],
    ) -> list[str]:
        normalized: list[str] = []
        for value in values:
            bullet = value.strip()
            if not bullet:
                raise ValueError(
                    "bullet points cannot "
                    "contain blank values"
                )
            if bullet not in normalized:
                normalized.append(bullet)
        return normalized
class AIAnalysisMetadata(BaseModel):
    analysis_type: AIAnalysisType
    generated_at_ms: int = Field(
        default=0,
        ge=0,
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0,
        le=1,
    )
    data_sources: list[AIDataSource] = (
        Field(
            default_factory=lambda: [
                "USER_QUERY",
            ],
            max_length=20,
        )
    )
    provider: str = Field(
        default="DETERMINISTIC",
        min_length=2,
        max_length=100,
    )
    model_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )
    advisory_only: Literal[True] = True
    execution_enabled: Literal[False] = (
        False
    )
    @field_validator("data_sources")
    @classmethod
    def normalize_data_sources(
        cls,
        values: list[AIDataSource],
    ) -> list[AIDataSource]:
        normalized: list[AIDataSource] = []
        for value in values:
            if value not in normalized:
                normalized.append(value)
        return normalized
    @field_validator("provider")
    @classmethod
    def normalize_provider(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError(
                "provider cannot be blank"
            )
        return normalized
    @field_validator("model_name")
    @classmethod
    def normalize_model_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError(
                "model_name cannot be blank"
            )
        return normalized
class AITradePlan(BaseModel):
    symbol: str = Field(
        min_length=2,
        max_length=30,
    )
    side: AITradeSide
    category: MarketCategory = "linear"
    thesis: str = Field(
        min_length=2,
        max_length=4000,
    )
    entry_conditions: list[str] = Field(
        default_factory=list,
        max_length=30,
    )
    stop_loss_reasoning: str = Field(
        min_length=2,
        max_length=2000,
    )
    take_profit_reasoning: str = Field(
        min_length=2,
        max_length=2000,
    )
    invalidation_conditions: list[str] = (
        Field(
            default_factory=list,
            max_length=30,
        )
    )
    risk_warnings: list[str] = Field(
        default_factory=list,
        max_length=30,
    )
    reference_entry_price: (
        float | None
    ) = Field(
        default=None,
        gt=0,
    )
    reference_stop_loss_price: (
        float | None
    ) = Field(
        default=None,
        gt=0,
    )
    reference_take_profit_price: (
        float | None
    ) = Field(
        default=None,
        gt=0,
    )
    estimated_risk_reward_ratio: (
        float | None
    ) = Field(
        default=None,
        gt=0,
    )
    advisory_only: Literal[True] = True
    execution_enabled: Literal[False] = (
        False
    )
    @field_validator("symbol")
    @classmethod
    def normalize_plan_symbol(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError(
                "symbol cannot be blank"
            )
        return normalized
    @field_validator(
        "thesis",
        "stop_loss_reasoning",
        "take_profit_reasoning",
    )
    @classmethod
    def normalize_plan_text(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError(
                "trade-plan text cannot "
                "be blank"
            )
        return normalized
    @field_validator(
        "entry_conditions",
        "invalidation_conditions",
        "risk_warnings",
    )
    @classmethod
    def normalize_plan_lists(
        cls,
        values: list[str],
    ) -> list[str]:
        normalized: list[str] = []
        for value in values:
            item = value.strip()
            if not item:
                raise ValueError(
                    "trade-plan lists cannot "
                    "contain blank values"
                )
            if item not in normalized:
                normalized.append(item)
        return normalized
class AIAnalysisResponse(BaseModel):
    status: AIAnalysisStatus
    answer: str = Field(
        min_length=2,
        max_length=12000,
    )
    sections: list[AIAnalysisSection] = (
        Field(
            default_factory=list,
            max_length=30,
        )
    )
    warnings: list[AIAnalysisWarning] = (
        Field(
            default_factory=list,
            max_length=50,
        )
    )
    metadata: AIAnalysisMetadata
    trade_plan: AITradePlan | None = None
    execution_allowed: Literal[False] = (
        False
    )
    @field_validator("answer")
    @classmethod
    def normalize_answer(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError(
                "answer cannot be blank"
            )
        return normalized
    @model_validator(mode="after")
    def validate_trade_plan_response(self):
        if (
            self.trade_plan is not None
            and self.metadata.analysis_type
            != "TRADE_PLAN"
        ):
            raise ValueError(
                "trade_plan requires metadata "
                "analysis_type TRADE_PLAN"
            )
        return self
class AIMarketAnalysisAPIRequest(BaseModel):
    request: AIMarketAnalysisRequest
    tickers: list[dict[str, Any]] = Field(
        default_factory=list,
        max_length=100,
    )
class AIPortfolioAnalysisAPIRequest(BaseModel):
    request: AIPortfolioAnalysisRequest
    snapshot: PortfolioSyncSnapshotResponse
