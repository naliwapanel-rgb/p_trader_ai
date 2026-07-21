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

TradingBotStrategyPositionSide = Literal[
    "LONG",
    "SHORT",
]
class DcaStrategyConfig(
    BaseModel
):
    direction: (
        TradingBotStrategyPositionSide
    ) = "LONG"
    entry_spacing_percent: float = Field(
        default=2.0,
        gt=0,
        le=100,
    )
    maximum_entries: int = Field(
        default=5,
        ge=1,
        le=50,
    )
    take_profit_percent: float = Field(
        default=3.0,
        gt=0,
        le=100,
    )
    initial_entry_change_percent_24h: (
        float | None
    ) = None
    maximum_spread_percent: float = Field(
        default=0.5,
        ge=0,
        le=100,
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
class GridStrategyConfig(
    BaseModel
):
    direction: (
        TradingBotStrategyPositionSide
    ) = "LONG"
    lower_price: float = Field(
        gt=0,
    )
    upper_price: float = Field(
        gt=0,
    )
    grid_levels: int = Field(
        default=10,
        ge=2,
        le=100,
    )
    maximum_entries: int = Field(
        default=5,
        ge=1,
        le=100,
    )
    take_profit_percent: float = Field(
        default=2.0,
        gt=0,
        le=100,
    )
    maximum_spread_percent: float = Field(
        default=0.5,
        ge=0,
        le=100,
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
    def validate_grid_range(self):
        if self.lower_price >= self.upper_price:
            raise ValueError(
                "lower_price must be below "
                "upper_price"
            )
        if (
            self.maximum_entries
            > self.grid_levels
        ):
            raise ValueError(
                "maximum_entries cannot exceed "
                "grid_levels"
            )
        return self
class TradingBotStrategyPositionState(
    BaseModel
):
    side: TradingBotStrategyPositionSide
    quantity: float = Field(
        gt=0,
    )
    average_entry_price: float = Field(
        gt=0,
    )
    current_price: float = Field(
        gt=0,
    )
    position_value_usd: float = Field(
        ge=0,
    )
    unrealized_pnl_usd: float = 0.0
    entry_count: int = Field(
        ge=1,
        le=100,
    )
    last_entry_price: float = Field(
        gt=0,
    )
    opened_at: datetime
    last_entry_at: datetime
    model_config = ConfigDict(
        extra="forbid",
    )
class TradingBotStrategyState(
    BaseModel
):
    order_count: int = Field(
        default=0,
        ge=0,
    )
    completed_trade_count: int = Field(
        default=0,
        ge=0,
    )
    last_order_action: (
        TradingBotStrategyAction | None
    ) = None
    last_order_reference_price: (
        float | None
    ) = Field(
        default=None,
        gt=0,
    )
    last_order_at: datetime | None = None
    position: (
        TradingBotStrategyPositionState
        | None
    ) = None
    model_config = ConfigDict(
        extra="forbid",
    )
    @model_validator(mode="after")
    def validate_state_consistency(self):
        last_order_values = (
            self.last_order_action,
            self.last_order_reference_price,
            self.last_order_at,
        )
        supplied_count = sum(
            value is not None
            for value in last_order_values
        )
        if supplied_count not in {
            0,
            3,
        }:
            raise ValueError(
                "Last-order state fields must "
                "be provided together"
            )
        if (
            self.position is not None
            and self.order_count
            < self.position.entry_count
        ):
            raise ValueError(
                "order_count cannot be below "
                "the position entry_count"
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
    state: TradingBotStrategyState = Field(
        default_factory=(
            TradingBotStrategyState
        )
    )
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
