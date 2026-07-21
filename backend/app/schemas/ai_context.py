from datetime import datetime
from typing import (
    Any,
    Literal,
)
from pydantic import (
    BaseModel,
    Field,
)
from app.schemas.alert import (
    AlertResponse,
)
from app.schemas.exchange_account import (
    ExchangeAccountResponse,
)
from app.schemas.notification_preference import (
    NotificationPreferenceResponse,
)
from app.schemas.portfolio import (
    PortfolioResponse,
)
from app.schemas.risk_management import (
    RiskConfiguration,
)
from app.schemas.watchlist import (
    WatchlistResponse,
)
AIContextDataSource = Literal[
    "PORTFOLIO",
    "WATCHLIST",
    "ALERTS",
    "EXCHANGE_ACCOUNTS",
    "NOTIFICATION_PREFERENCES",
    "RISK_ENGINE",
    "AUTOMATION_RUNTIME",
]
class AIContextRequest(BaseModel):
    portfolio_id: int | None = Field(
        default=None,
        gt=0,
    )
    exchange_account_id: int | None = Field(
        default=None,
        gt=0,
    )
    include_automation: bool = True
class AIPortfolioSnapshotContext(BaseModel):
    id: int = Field(gt=0)
    user_id: int = Field(gt=0)
    portfolio_id: int = Field(gt=0)
    exchange_account_id: int = Field(gt=0)
    exchange_name: str
    account_type: str
    category: str
    settle_coin: str
    status: Literal[
        "SUCCESS",
        "PARTIAL",
        "FAILED",
    ]
    total_equity_usd: float
    total_wallet_balance_usd: float
    total_available_balance_usd: float
    total_unrealized_pnl_usd: float
    total_realized_pnl_usd: float
    total_position_value_usd: float
    coin_count: int = Field(ge=0)
    open_position_count: int = Field(ge=0)
    open_order_count: int = Field(ge=0)
    balance_payload: dict[str, Any] = Field(
        default_factory=dict
    )
    positions_payload: list[
        dict[str, Any]
    ] = Field(
        default_factory=list
    )
    orders_payload: list[
        dict[str, Any]
    ] = Field(
        default_factory=list
    )
    error_message: str | None = None
    synced_at: datetime
    created_at: datetime
class AIAutomationContext(BaseModel):
    available: bool
    healthy: bool
    started: bool
    handlers_registered: bool
    worker_running: bool
    accepting_jobs: bool
class AIUserContextResponse(BaseModel):
    context_version: int = Field(
        default=1,
        ge=1,
    )
    user_id: int = Field(gt=0)
    generated_at_ms: int = Field(ge=0)
    portfolios: list[
        PortfolioResponse
    ] = Field(
        default_factory=list
    )
    selected_portfolio: (
        PortfolioResponse | None
    ) = None
    latest_portfolio_snapshot: (
        AIPortfolioSnapshotContext | None
    ) = None
    watchlist: list[
        WatchlistResponse
    ] = Field(
        default_factory=list
    )
    alerts: list[
        AlertResponse
    ] = Field(
        default_factory=list
    )
    exchange_accounts: list[
        ExchangeAccountResponse
    ] = Field(
        default_factory=list
    )
    selected_exchange_account: (
        ExchangeAccountResponse | None
    ) = None
    notification_preferences: (
        NotificationPreferenceResponse | None
    ) = None
    risk_configuration: RiskConfiguration
    automation: (
        AIAutomationContext | None
    ) = None
    data_sources: list[
        AIContextDataSource
    ] = Field(
        default_factory=list
    )
    portfolio_count: int = Field(ge=0)
    watchlist_count: int = Field(ge=0)
    alert_count: int = Field(ge=0)
    exchange_account_count: int = Field(ge=0)
    advisory_only: Literal[True] = True
    execution_enabled: Literal[False] = False
