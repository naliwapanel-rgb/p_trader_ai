from datetime import (
    datetime,
)
from typing import (
    Any,
    Literal,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
from app.schemas.market_scanner import (
    MarketCategory,
    MarketTickerSnapshot,
)
TradingBotStrategyAction = Literal[
    "BUY",
    "SELL",
    "HOLD",
]
class RuleBasedStrategyConfig(
    BaseModel
):
    buy_change_percent_24h: float = 1.0
    sell_change_percent_24h: float = -1.0
    maximum_spread_percent: float = Field(
        default=0.5,
        ge=0,
    )
    minimum_turnover_24h: float = Field(
        default=0.0,
        ge=0,
    )
    confidence_scale_percent: float = Field(
        default=5.0,
        gt=0,
        le=100,
    )
    model_config = ConfigDict(
        extra="forbid",
    )
    @model_validator(mode="after")
    def validate_thresholds(self):
        if (
            self.sell_change_percent_24h
            >= self.buy_change_percent_24h
        ):
            raise ValueError(
                "sell_change_percent_24h "
                "must be below "
                "buy_change_percent_24h"
            )
        return self
class TradingBotStrategyContext(
    BaseModel
):
    bot_id: int = Field(
        ge=1,
    )
    user_id: int = Field(
        ge=1,
    )
    strategy_type: str = Field(
        min_length=2,
        max_length=50,
    )
    symbol: str = Field(
        min_length=2,
        max_length=30,
    )
    category: MarketCategory
    timeframe: str = Field(
        min_length=2,
        max_length=20,
    )
    config: dict[
        str,
        Any,
    ] = Field(
        default_factory=dict
    )
    ticker: MarketTickerSnapshot
    evaluated_at: datetime
    @field_validator(
        "strategy_type",
        "symbol",
    )
    @classmethod
    def normalize_identifier(
        cls,
        value: str,
    ) -> str:
        normalized = (
            value.strip().upper()
        )
        if not normalized:
            raise ValueError(
                "Strategy identifiers "
                "cannot be blank"
            )
        return normalized
    @model_validator(mode="after")
    def validate_market_context(self):
        if self.ticker.symbol != self.symbol:
            raise ValueError(
                "Ticker symbol does not match "
                "the trading bot symbol"
            )
        if self.ticker.category != self.category:
            raise ValueError(
                "Ticker category does not match "
                "the trading bot category"
            )
        return self
class TradingBotStrategyDecision(
    BaseModel
):
    action: TradingBotStrategyAction
    confidence: float = Field(
        ge=0,
        le=1,
    )
    reason: str = Field(
        min_length=2,
        max_length=1000,
    )
    reference_price: float = Field(
        ge=0,
    )
    evaluated_at: datetime
    metadata: dict[
        str,
        Any,
    ] = Field(
        default_factory=dict
    )
