from datetime import (
    UTC,
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
from app.schemas.arbitrage import (
    ArbitrageMarketQuote,
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

class TrendStrategyConfig(
    BaseModel
):
    direction: Literal[
        "LONG",
        "SHORT",
        "BOTH",
    ] = "BOTH"
    fast_ema_period: int = Field(
        default=9,
        ge=2,
        le=200,
    )
    slow_ema_period: int = Field(
        default=21,
        ge=3,
        le=500,
    )
    momentum_lookback: int = Field(
        default=5,
        ge=1,
        le=200,
    )
    minimum_momentum_percent: float = Field(
        default=0.25,
        ge=0,
        le=100,
    )
    minimum_ema_separation_percent: float = (
        Field(
            default=0.05,
            ge=0,
            le=100,
        )
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
        default=2.0,
        gt=0,
        le=100,
    )
    model_config = ConfigDict(
        extra="forbid",
    )
    @model_validator(mode="after")
    def validate_periods(self):
        if (
            self.fast_ema_period
            >= self.slow_ema_period
        ):
            raise ValueError(
                "fast_ema_period must be "
                "below slow_ema_period"
            )
        return self
class MeanReversionStrategyConfig(
    BaseModel
):
    direction: Literal[
        "LONG",
        "SHORT",
        "BOTH",
    ] = "BOTH"
    lookback_period: int = Field(
        default=20,
        ge=3,
        le=500,
    )
    rsi_period: int = Field(
        default=14,
        ge=2,
        le=200,
    )
    entry_z_score: float = Field(
        default=2.0,
        gt=0,
        le=10,
    )
    exit_z_score: float = Field(
        default=0.5,
        ge=0,
        le=10,
    )
    oversold_rsi: float = Field(
        default=30.0,
        ge=0,
        lt=50,
    )
    overbought_rsi: float = Field(
        default=70.0,
        gt=50,
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
    confidence_scale: float = Field(
        default=2.0,
        gt=0,
        le=10,
    )
    model_config = ConfigDict(
        extra="forbid",
    )
    @model_validator(mode="after")
    def validate_mean_reversion_thresholds(
        self,
    ):
        if (
            self.exit_z_score
            >= self.entry_z_score
        ):
            raise ValueError(
                "exit_z_score must be below "
                "entry_z_score"
            )
        if (
            self.oversold_rsi
            >= self.overbought_rsi
        ):
            raise ValueError(
                "oversold_rsi must be below "
                "overbought_rsi"
            )
        return self
class ScalpingStrategyConfig(
    BaseModel
):
    direction: Literal[
        "LONG",
        "SHORT",
        "BOTH",
    ] = "BOTH"
    fast_ema_period: int = Field(
        default=5,
        ge=2,
        le=100,
    )
    slow_ema_period: int = Field(
        default=13,
        ge=3,
        le=200,
    )
    rsi_period: int = Field(
        default=7,
        ge=2,
        le=100,
    )
    atr_period: int = Field(
        default=7,
        ge=2,
        le=100,
    )
    momentum_lookback: int = Field(
        default=2,
        ge=1,
        le=50,
    )
    minimum_momentum_percent: float = Field(
        default=0.10,
        ge=0,
        le=100,
    )
    exit_momentum_percent: float = Field(
        default=0.05,
        ge=0,
        le=100,
    )
    long_rsi_minimum: float = Field(
        default=52.0,
        ge=0,
        le=100,
    )
    long_rsi_maximum: float = Field(
        default=75.0,
        ge=0,
        le=100,
    )
    short_rsi_minimum: float = Field(
        default=25.0,
        ge=0,
        le=100,
    )
    short_rsi_maximum: float = Field(
        default=48.0,
        ge=0,
        le=100,
    )
    minimum_atr_percent: float = Field(
        default=0.05,
        ge=0,
        le=100,
    )
    maximum_atr_percent: float = Field(
        default=3.0,
        gt=0,
        le=100,
    )
    maximum_spread_percent: float = Field(
        default=0.20,
        ge=0,
        le=100,
    )
    minimum_turnover_24h: float = Field(
        default=0.0,
        ge=0,
    )
    confidence_scale_percent: float = Field(
        default=1.0,
        gt=0,
        le=100,
    )
    model_config = ConfigDict(
        extra="forbid",
    )
    @model_validator(mode="after")
    def validate_scalping_thresholds(
        self,
    ):
        if (
            self.fast_ema_period
            >= self.slow_ema_period
        ):
            raise ValueError(
                "fast_ema_period must be "
                "below slow_ema_period"
            )
        if (
            self.long_rsi_minimum
            >= self.long_rsi_maximum
        ):
            raise ValueError(
                "long_rsi_minimum must be "
                "below long_rsi_maximum"
            )
        if (
            self.short_rsi_minimum
            >= self.short_rsi_maximum
        ):
            raise ValueError(
                "short_rsi_minimum must be "
                "below short_rsi_maximum"
            )
        if (
            self.short_rsi_maximum
            > self.long_rsi_minimum
        ):
            raise ValueError(
                "short_rsi_maximum cannot "
                "exceed long_rsi_minimum"
            )
        if (
            self.minimum_atr_percent
            >= self.maximum_atr_percent
        ):
            raise ValueError(
                "minimum_atr_percent must be "
                "below maximum_atr_percent"
            )
        return self
class ArbitrageRuntimeMarketConfig(
    BaseModel
):
    exchange: str = Field(
        min_length=2,
        max_length=50,
    )
    symbol: str = Field(
        min_length=3,
        max_length=50,
    )
    base_asset: str = Field(
        min_length=1,
        max_length=20,
    )
    quote_asset: str = Field(
        min_length=1,
        max_length=20,
    )
    fee_rate_percent: float = Field(
        default=0.0,
        ge=0,
        lt=100,
    )
    slippage_percent: float = Field(
        default=0.0,
        ge=0,
        lt=100,
    )
    fixed_buy_cost: float = Field(
        default=0.0,
        ge=0,
    )
    fixed_sell_cost: float = Field(
        default=0.0,
        ge=0,
    )
    model_config = ConfigDict(
        extra="forbid",
    )
    @field_validator(
        "exchange",
        "symbol",
        "base_asset",
        "quote_asset",
    )
    @classmethod
    def normalize_market_identifier(
        cls,
        value: str,
    ) -> str:
        normalized = (
            value.strip().upper()
        )
        if not normalized:
            raise ValueError(
                "Arbitrage market identifiers "
                "cannot be blank"
            )
        return normalized
    @model_validator(mode="after")
    def validate_market_assets(self):
        if (
            self.base_asset
            == self.quote_asset
        ):
            raise ValueError(
                "base_asset and quote_asset "
                "must be different"
            )
        return self
class ArbitrageStrategyConfig(
    BaseModel
):
    opportunity_type: Literal[
        "CROSS_EXCHANGE",
        "TRIANGULAR",
    ] = "TRIANGULAR"
    starting_asset: str = Field(
        default="USDT",
        min_length=1,
        max_length=20,
    )
    starting_amount: float = Field(
        default=100.0,
        gt=0,
        le=1_000_000_000,
    )
    minimum_profit_percent: float = Field(
        default=0.1,
        ge=0,
        le=100,
    )
    exchanges: list[str] = Field(
        default_factory=lambda: [
            "BYBIT",
        ],
        min_length=1,
        max_length=10,
    )
    symbols: list[str] = Field(
        default_factory=list,
        max_length=100,
    )
    markets: list[
        ArbitrageRuntimeMarketConfig
    ] = Field(
        default_factory=list,
        max_length=500,
    )
    maximum_quote_age_ms: (
        int | None
    ) = Field(
        default=5000,
        ge=0,
        le=3_600_000,
    )
    maximum_time_skew_ms: (
        int | None
    ) = Field(
        default=1000,
        ge=0,
        le=3_600_000,
    )
    require_full_liquidity: bool = True
    maximum_opportunities: int = Field(
        default=10,
        ge=1,
        le=200,
    )
    evaluation_only: Literal[
        True
    ] = True
    model_config = ConfigDict(
        extra="forbid",
    )
    @field_validator(
        "starting_asset",
    )
    @classmethod
    def normalize_starting_asset(
        cls,
        value: str,
    ) -> str:
        normalized = (
            value.strip().upper()
        )
        if not normalized:
            raise ValueError(
                "starting_asset cannot be blank"
            )
        return normalized
    @field_validator(
        "exchanges",
        "symbols",
    )
    @classmethod
    def normalize_identifier_list(
        cls,
        values: list[str],
    ) -> list[str]:
        normalized = []
        for value in values:
            identifier = (
                value.strip().upper()
            )
            if not identifier:
                raise ValueError(
                    "Arbitrage identifiers "
                    "cannot be blank"
                )
            if identifier not in normalized:
                normalized.append(
                    identifier
                )
        return normalized
    @model_validator(mode="after")
    def validate_arbitrage_mode(self):
        if (
            self.opportunity_type
            == "TRIANGULAR"
            and len(self.exchanges) != 1
        ):
            raise ValueError(
                "TRIANGULAR arbitrage requires "
                "exactly one exchange"
            )
        if (
            self.opportunity_type
            == "CROSS_EXCHANGE"
            and len(self.exchanges) < 2
        ):
            raise ValueError(
                "CROSS_EXCHANGE arbitrage "
                "requires at least two exchanges"
            )
        configured_exchanges = set(
            self.exchanges
        )
        market_keys = set()
        for market in self.markets:
            market_key = (
                market.exchange,
                market.symbol,
            )
            if market_key in market_keys:
                raise ValueError(
                    "Arbitrage runtime markets "
                    "cannot contain duplicate "
                    "exchange and symbol entries"
                )
            market_keys.add(
                market_key
            )
            if (
                market.exchange
                not in configured_exchanges
            ):
                raise ValueError(
                    "Arbitrage runtime market "
                    "exchange must be included "
                    "in exchanges"
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


class TradingBotMarketSample(
    BaseModel
):
    observed_at: datetime
    open_price: float = Field(
        gt=0,
    )
    high_price: float = Field(
        gt=0,
    )
    low_price: float = Field(
        gt=0,
    )
    close_price: float = Field(
        gt=0,
    )
    bid_price: float = Field(
        default=0.0,
        ge=0,
    )
    ask_price: float = Field(
        default=0.0,
        ge=0,
    )
    volume: float = Field(
        default=0.0,
        ge=0,
    )
    turnover_usd: float = Field(
        default=0.0,
        ge=0,
    )
    source: Literal[
        "TICKER",
        "CANDLE",
    ] = "TICKER"
    model_config = ConfigDict(
        extra="forbid",
    )
    @field_validator("observed_at")
    @classmethod
    def normalize_observed_at(
        cls,
        value: datetime,
    ) -> datetime:
        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise ValueError(
                "Market sample timestamps "
                "must include a timezone"
            )
        return value.astimezone(UTC)
    @model_validator(mode="after")
    def validate_market_sample(self):
        if self.high_price < self.low_price:
            raise ValueError(
                "high_price cannot be below "
                "low_price"
            )
        if self.high_price < max(
            self.open_price,
            self.close_price,
        ):
            raise ValueError(
                "high_price must be at least "
                "the open and close prices"
            )
        if self.low_price > min(
            self.open_price,
            self.close_price,
        ):
            raise ValueError(
                "low_price must not exceed "
                "the open or close prices"
            )
        if (
            self.bid_price > 0
            and self.ask_price > 0
            and self.ask_price
            < self.bid_price
        ):
            raise ValueError(
                "ask_price cannot be below "
                "bid_price"
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
    arbitrage_quotes: list[
        ArbitrageMarketQuote
    ] = Field(
        default_factory=list,
        max_length=500,
    )
    market_history: list[
        TradingBotMarketSample
    ] = Field(
        default_factory=list,
        max_length=500,
    )
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
        if self.arbitrage_quotes:
            if (
                self.evaluated_at.tzinfo
                is None
                or self.evaluated_at
                .utcoffset()
                is None
            ):
                raise ValueError(
                    "evaluated_at must include "
                    "a timezone when arbitrage "
                    "quotes are provided"
                )
            evaluated_at_ms = int(
                self.evaluated_at
                .astimezone(UTC)
                .timestamp()
                * 1000
            )
            quote_keys = set()
            for quote in self.arbitrage_quotes:
                quote_key = (
                    quote.exchange,
                    quote.symbol,
                )
                if quote_key in quote_keys:
                    raise ValueError(
                        "Arbitrage quotes cannot "
                        "contain duplicate exchange "
                        "and symbol markets"
                    )
                quote_keys.add(
                    quote_key
                )
                if (
                    quote.observed_at_ms > 0
                    and quote.observed_at_ms
                    > evaluated_at_ms
                ):
                    raise ValueError(
                        "Arbitrage quotes cannot "
                        "contain future observations"
                    )
        previous_timestamp = None
        if self.market_history:
            if (
                self.evaluated_at.tzinfo
                is None
                or self.evaluated_at
                .utcoffset()
                is None
            ):
                raise ValueError(
                    "evaluated_at must include "
                    "a timezone when market "
                    "history is provided"
                )
            evaluated_at = (
                self.evaluated_at
                .astimezone(UTC)
            )
            for sample in self.market_history:
                if (
                    previous_timestamp
                    is not None
                    and sample.observed_at
                    <= previous_timestamp
                ):
                    raise ValueError(
                        "Market history must be "
                        "strictly chronological"
                    )
                if (
                    sample.observed_at
                    > evaluated_at
                ):
                    raise ValueError(
                        "Market history cannot "
                        "contain future samples"
                    )
                previous_timestamp = (
                    sample.observed_at
                )
            latest_price = (
                self.market_history[
                    -1
                ].close_price
            )
            tolerance = max(
                abs(
                    self.ticker.last_price
                )
                * 1e-9,
                1e-9,
            )
            if (
                abs(
                    latest_price
                    - self.ticker.last_price
                )
                > tolerance
            ):
                raise ValueError(
                    "Latest market-history price "
                    "does not match the ticker"
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
