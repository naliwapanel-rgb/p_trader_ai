from typing import Any, Literal
from pydantic import BaseModel, Field
from app.schemas.exchange_trade import (
    LimitOrderRequest,
    MarketOrderRequest,
)
AutomatedTradeType = Literal[
    "MARKET_ORDER",
    "LIMIT_ORDER",
]
class AutomatedMarketOrderJob(BaseModel):
    user_id: int = Field(
        ge=1,
    )
    account_id: int = Field(
        ge=1,
    )
    order: MarketOrderRequest
class AutomatedLimitOrderJob(BaseModel):
    user_id: int = Field(
        ge=1,
    )
    account_id: int = Field(
        ge=1,
    )
    order: LimitOrderRequest
class AutomatedTradeExecutionResult(BaseModel):
    execution_type: AutomatedTradeType
    user_id: int = Field(
        ge=1,
    )
    account_id: int = Field(
        ge=1,
    )
    symbol: str
    side: str
    exchange_result: dict[str, Any]
