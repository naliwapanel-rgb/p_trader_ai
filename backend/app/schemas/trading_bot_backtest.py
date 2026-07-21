from datetime import (
    UTC,
    datetime,
)
from typing import (
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
    MarketTickerSnapshot,
)
from app.schemas.trading_bot_strategy import (
    TradingBotStrategyDecision,
)
BacktestPositionSide = Literal[
    "LONG",
    "SHORT",
]
class HistoricalMarketCandle(
    BaseModel
):
    opened_at: datetime
    closed_at: datetime
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
    volume: float = Field(
        default=0.0,
        ge=0,
    )
    turnover_usd: float = Field(
        default=0.0,
        ge=0,
    )
    model_config = ConfigDict(
        extra="forbid",
    )
    @field_validator(
        "opened_at",
        "closed_at",
    )
    @classmethod
    def normalize_timestamp(
        cls,
        value: datetime,
    ) -> datetime:
        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise ValueError(
                "Candle timestamps must "
                "include a timezone"
            )
        return value.astimezone(UTC)
    @model_validator(mode="after")
    def validate_candle(self):
        if self.closed_at <= self.opened_at:
            raise ValueError(
                "closed_at must be after "
                "opened_at"
            )
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
        return self
class TradingBotBacktestRequest(
    BaseModel
):
    initial_balance_usd: float = Field(
        default=10000.0,
        gt=0,
    )
    fee_rate: float = Field(
        default=0.0006,
        ge=0,
        le=0.1,
    )
    slippage_rate: float = Field(
        default=0.0001,
        ge=0,
        le=0.1,
    )
    minimum_order_notional_usd: float = (
        Field(
            default=1.0,
            gt=0,
        )
    )
    quantity_decimal_places: int = Field(
        default=12,
        ge=0,
        le=18,
    )
    force_close_at_end: bool = True
    candles: list[
        HistoricalMarketCandle
    ] = Field(
        min_length=2,
        max_length=10000,
    )
    model_config = ConfigDict(
        extra="forbid",
    )
    @model_validator(mode="after")
    def validate_candle_sequence(self):
        previous = None
        for candle in self.candles:
            if previous is not None:
                if (
                    candle.opened_at
                    <= previous.opened_at
                ):
                    raise ValueError(
                        "Candles must be ordered "
                        "chronologically"
                    )
                if (
                    candle.opened_at
                    < previous.closed_at
                ):
                    raise ValueError(
                        "Historical candles "
                        "cannot overlap"
                    )
            previous = candle
        return self
class BacktestMarketFrame(
    BaseModel
):
    sequence: int = Field(
        ge=1,
    )
    candle: HistoricalMarketCandle
    ticker: MarketTickerSnapshot
    warmup_complete: bool
    model_config = ConfigDict(
        extra="forbid",
    )
BacktestExecutionOutcome = Literal[
    "WARMUP",
    "NO_ACTION",
    "OPENED",
    "INCREASED",
    "CLOSED",
    "REJECTED",
    "FORCED_CLOSED",
]
class BacktestPositionSnapshot(
    BaseModel
):
    side: BacktestPositionSide
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
    reserved_margin_usd: float = Field(
        ge=0,
    )
    unrealized_pnl_usd: float
    entry_fees_usd: float = Field(
        ge=0,
    )
    opened_at: datetime
class BacktestPortfolioSnapshot(
    BaseModel
):
    initial_balance_usd: float = Field(
        gt=0,
    )
    cash_balance_usd: float = Field(
        ge=0,
    )
    reserved_balance_usd: float = Field(
        ge=0,
    )
    equity_usd: float
    realized_pnl_usd: float
    unrealized_pnl_usd: float
    total_fees_usd: float = Field(
        ge=0,
    )
    open_position: (
        BacktestPositionSnapshot
        | None
    ) = None
class BacktestOrderFill(
    BaseModel
):
    sequence: int = Field(
        ge=1,
    )
    filled_at: datetime
    side: Literal[
        "BUY",
        "SELL",
    ]
    position_side: BacktestPositionSide
    position_effect: Literal[
        "OPEN",
        "INCREASE",
        "CLOSE",
    ]
    quantity: float = Field(
        gt=0,
    )
    reference_price: float = Field(
        gt=0,
    )
    fill_price: float = Field(
        gt=0,
    )
    gross_value_usd: float = Field(
        gt=0,
    )
    fee_usd: float = Field(
        ge=0,
    )
    slippage_usd: float = Field(
        ge=0,
    )
    realized_pnl_usd: float = 0.0
    forced: bool = False
    reason: str = Field(
        min_length=2,
        max_length=1000,
    )
class BacktestCompletedTrade(
    BaseModel
):
    side: BacktestPositionSide
    opened_at: datetime
    closed_at: datetime
    quantity: float = Field(
        gt=0,
    )
    average_entry_price: float = Field(
        gt=0,
    )
    exit_price: float = Field(
        gt=0,
    )
    gross_realized_pnl_usd: float
    total_fees_usd: float = Field(
        ge=0,
    )
    net_realized_pnl_usd: float
    forced_exit: bool = False
class BacktestExecutionStep(
    BaseModel
):
    sequence: int = Field(
        ge=1,
    )
    candle_closed_at: datetime
    warmup_complete: bool
    decision: (
        TradingBotStrategyDecision
        | None
    ) = None
    outcomes: list[
        BacktestExecutionOutcome
    ] = Field(
        min_length=1,
    )
    orders: list[
        BacktestOrderFill
    ] = Field(
        default_factory=list
    )
    portfolio: BacktestPortfolioSnapshot
class TradingBotBacktestExecutionResult(
    BaseModel
):
    bot_id: int = Field(
        ge=1,
    )
    symbol: str
    category: str
    timeframe: str
    started_at: datetime
    ended_at: datetime
    frames_processed: int = Field(
        ge=2,
    )
    warmup_frame_count: int = Field(
        ge=0,
    )
    evaluated_frame_count: int = Field(
        ge=0,
    )
    order_count: int = Field(
        ge=0,
    )
    completed_trade_count: int = Field(
        ge=0,
    )
    orders: list[
        BacktestOrderFill
    ] = Field(
        default_factory=list
    )
    completed_trades: list[
        BacktestCompletedTrade
    ] = Field(
        default_factory=list
    )
    steps: list[
        BacktestExecutionStep
    ] = Field(
        default_factory=list
    )
    final_portfolio: (
        BacktestPortfolioSnapshot
    )
class BacktestEquityPoint(
    BaseModel
):
    sequence: int = Field(
        ge=0,
    )
    recorded_at: datetime
    equity_usd: float
    peak_equity_usd: float
    drawdown_usd: float = Field(
        ge=0,
    )
    drawdown_percent: float = Field(
        ge=0,
    )
class BacktestPerformanceSummary(
    BaseModel
):
    initial_balance_usd: float = Field(
        gt=0,
    )
    final_equity_usd: float
    total_net_pnl_usd: float
    return_percent: float
    maximum_drawdown_usd: float = Field(
        ge=0,
    )
    maximum_drawdown_percent: float = Field(
        ge=0,
    )
    order_count: int = Field(
        ge=0,
    )
    completed_trade_count: int = Field(
        ge=0,
    )
    winning_trade_count: int = Field(
        ge=0,
    )
    losing_trade_count: int = Field(
        ge=0,
    )
    breakeven_trade_count: int = Field(
        ge=0,
    )
    forced_exit_count: int = Field(
        ge=0,
    )
    gross_profit_usd: float = Field(
        ge=0,
    )
    gross_loss_usd: float = Field(
        ge=0,
    )
    net_realized_pnl_usd: float
    unrealized_pnl_usd: float
    total_fees_usd: float = Field(
        ge=0,
    )
    win_rate_percent: float = Field(
        ge=0,
        le=100,
    )
    average_win_usd: float = Field(
        ge=0,
    )
    average_loss_usd: float = Field(
        le=0,
    )
    profit_factor: float | None = Field(
        default=None,
        ge=0,
    )
class TradingBotBacktestResult(
    BaseModel
):
    execution: (
        TradingBotBacktestExecutionResult
    )
    equity_curve: list[
        BacktestEquityPoint
    ] = Field(
        min_length=1,
    )
    performance: (
        BacktestPerformanceSummary
    )
