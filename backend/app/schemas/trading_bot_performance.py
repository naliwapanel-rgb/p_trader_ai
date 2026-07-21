from typing import (
    Literal,
)
from pydantic import (
    BaseModel,
    Field,
)
from app.schemas.paper_trading import (
    PaperTradingAccountResponse,
    PaperTradingOrderResponse,
    PaperTradingPositionResponse,
)
PaperTradingHistoryPositionStatus = Literal[
    "OPEN",
    "CLOSED",
]
class PaperTradingAccountSummaryResult(
    BaseModel
):
    bot_id: int = Field(
        ge=1,
    )
    account: PaperTradingAccountResponse
class PaperTradingOrderHistoryResult(
    BaseModel
):
    bot_id: int = Field(
        ge=1,
    )
    paper_account_id: int = Field(
        ge=1,
    )
    total_count: int = Field(
        ge=0,
    )
    limit: int = Field(
        ge=1,
        le=200,
    )
    offset: int = Field(
        ge=0,
    )
    items: list[
        PaperTradingOrderResponse
    ] = Field(
        default_factory=list
    )
class PaperTradingPositionHistoryResult(
    BaseModel
):
    bot_id: int = Field(
        ge=1,
    )
    paper_account_id: int = Field(
        ge=1,
    )
    position_status: (
        PaperTradingHistoryPositionStatus
        | None
    ) = None
    total_count: int = Field(
        ge=0,
    )
    limit: int = Field(
        ge=1,
        le=200,
    )
    offset: int = Field(
        ge=0,
    )
    items: list[
        PaperTradingPositionResponse
    ] = Field(
        default_factory=list
    )
class PaperTradingPerformanceResult(
    BaseModel
):
    bot_id: int = Field(
        ge=1,
    )
    paper_account_id: int = Field(
        ge=1,
    )
    currency: str
    initial_balance_usd: float
    cash_balance_usd: float
    reserved_balance_usd: float
    equity_usd: float
    order_count: int = Field(
        ge=0,
    )
    trade_count: int = Field(
        ge=0,
    )
    completed_trade_count: int = Field(
        ge=0,
    )
    open_trade_count: int = Field(
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
    gross_realized_pnl_usd: float
    realized_fees_usd: float
    net_realized_pnl_usd: float
    unrealized_pnl_usd: float
    total_fees_usd: float
    total_net_pnl_usd: float
    gross_profit_usd: float = Field(
        ge=0,
    )
    gross_loss_usd: float = Field(
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
    return_percent: float
