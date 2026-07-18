from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
PortfolioSyncStatus = Literal[
    "SUCCESS",
    "PARTIAL",
    "FAILED",
]
class PortfolioSyncSnapshotCreate(BaseModel):
    user_id: int = Field(gt=0)
    portfolio_id: int = Field(gt=0)
    exchange_account_id: int = Field(gt=0)
    exchange_name: str = Field(
        min_length=2,
        max_length=50,
    )
    account_type: str = Field(
        default="UNIFIED",
        min_length=2,
        max_length=30,
    )
    category: str = Field(
        default="linear",
        min_length=2,
        max_length=20,
    )
    settle_coin: str = Field(
        default="USDT",
        min_length=2,
        max_length=20,
    )
    status: PortfolioSyncStatus = "SUCCESS"
    fingerprint: str = Field(
        min_length=64,
        max_length=64,
    )
    sync_version: int = Field(
        default=1,
        ge=1,
    )
    total_equity_usd: float = 0.0
    total_wallet_balance_usd: float = 0.0
    total_available_balance_usd: float = 0.0
    total_unrealized_pnl_usd: float = 0.0
    total_realized_pnl_usd: float = 0.0
    total_position_value_usd: float = 0.0
    coin_count: int = Field(
        default=0,
        ge=0,
    )
    open_position_count: int = Field(
        default=0,
        ge=0,
    )
    open_order_count: int = Field(
        default=0,
        ge=0,
    )
    balance_payload: dict = Field(
        default_factory=dict
    )
    positions_payload: list[dict] = Field(
        default_factory=list
    )
    orders_payload: list[dict] = Field(
        default_factory=list
    )
    error_message: str | None = None
class PortfolioSyncSnapshotResponse(
    PortfolioSyncSnapshotCreate
):
    id: int
    synced_at: datetime
    created_at: datetime
    model_config = {
        "from_attributes": True,
    }
