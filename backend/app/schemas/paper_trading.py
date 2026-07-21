from datetime import (
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
)
PaperTradingAccountStatus = Literal[
    "ACTIVE",
    "FROZEN",
    "CLOSED",
]
PaperTradingPositionSide = Literal[
    "LONG",
    "SHORT",
]
PaperTradingPositionStatus = Literal[
    "OPEN",
    "CLOSED",
]
PaperTradingOrderSide = Literal[
    "BUY",
    "SELL",
]
PaperTradingPositionEffect = Literal[
    "OPEN",
    "INCREASE",
    "CLOSE",
]
PaperTradingOrderStatus = Literal[
    "FILLED",
]
class PaperTradingAccountCreate(
    BaseModel
):
    user_id: int = Field(
        ge=1,
    )
    trading_bot_id: int = Field(
        ge=1,
    )
    currency: str = Field(
        default="USDT",
        min_length=2,
        max_length=20,
    )
    initial_balance_usd: float = Field(
        default=10000.0,
        gt=0,
    )
    @field_validator("currency")
    @classmethod
    def normalize_currency(
        cls,
        value: str,
    ) -> str:
        normalized = (
            value.strip().upper()
        )
        if not normalized:
            raise ValueError(
                "currency cannot be blank"
            )
        return normalized
class PaperTradingAccountResponse(
    BaseModel
):
    id: int
    user_id: int
    trading_bot_id: int
    currency: str
    initial_balance_usd: float
    cash_balance_usd: float
    reserved_balance_usd: float
    equity_usd: float
    realized_pnl_usd: float
    unrealized_pnl_usd: float
    total_fees_usd: float
    status: PaperTradingAccountStatus
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(
        from_attributes=True
    )
class PaperTradingPositionCreate(
    BaseModel
):
    user_id: int = Field(
        ge=1,
    )
    trading_bot_id: int = Field(
        ge=1,
    )
    paper_account_id: int = Field(
        ge=1,
    )
    symbol: str = Field(
        min_length=2,
        max_length=30,
    )
    category: Literal[
        "spot",
        "linear",
        "inverse",
    ]
    side: PaperTradingPositionSide
    quantity: float = Field(
        gt=0,
    )
    average_entry_price: float = Field(
        gt=0,
    )
    current_price: float = Field(
        ge=0,
    )
    position_value_usd: float = Field(
        ge=0,
    )
    reserved_margin_usd: float = Field(
        ge=0,
    )
    unrealized_pnl_usd: float = 0.0
    realized_pnl_usd: float = 0.0
    total_fees_usd: float = Field(
        default=0.0,
        ge=0,
    )
    opened_at: datetime
    @field_validator("symbol")
    @classmethod
    def normalize_symbol(
        cls,
        value: str,
    ) -> str:
        normalized = (
            value.strip().upper()
        )
        if not normalized:
            raise ValueError(
                "symbol cannot be blank"
            )
        return normalized
class PaperTradingPositionResponse(
    PaperTradingPositionCreate
):
    id: int
    status: PaperTradingPositionStatus
    closed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(
        from_attributes=True
    )
class PaperTradingOrderCreate(
    BaseModel
):
    user_id: int = Field(
        ge=1,
    )
    trading_bot_id: int = Field(
        ge=1,
    )
    paper_account_id: int = Field(
        ge=1,
    )
    paper_position_id: int | None = Field(
        default=None,
        ge=1,
    )
    symbol: str = Field(
        min_length=2,
        max_length=30,
    )
    category: Literal[
        "spot",
        "linear",
        "inverse",
    ]
    side: PaperTradingOrderSide
    position_effect: (
        PaperTradingPositionEffect
    )
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
    fee_rate: float = Field(
        ge=0,
        le=1,
    )
    fee_usd: float = Field(
        ge=0,
    )
    slippage_rate: float = Field(
        ge=0,
        le=1,
    )
    slippage_usd: float = Field(
        ge=0,
    )
    realized_pnl_usd: float = 0.0
    decision_reason: str | None = Field(
        default=None,
        max_length=1000,
    )
    filled_at: datetime
    @field_validator("symbol")
    @classmethod
    def normalize_order_symbol(
        cls,
        value: str,
    ) -> str:
        normalized = (
            value.strip().upper()
        )
        if not normalized:
            raise ValueError(
                "symbol cannot be blank"
            )
        return normalized
class PaperTradingOrderResponse(
    PaperTradingOrderCreate
):
    id: int
    status: PaperTradingOrderStatus
    created_at: datetime
    model_config = ConfigDict(
        from_attributes=True
    )
class PaperTradingEngineSettings(
    BaseModel
):
    initial_balance_usd: float = Field(
        default=10000.0,
        gt=0,
    )
    currency: str = Field(
        default="USDT",
        min_length=2,
        max_length=20,
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
    model_config = ConfigDict(
        extra="forbid",
    )
    @field_validator("currency")
    @classmethod
    def normalize_settings_currency(
        cls,
        value: str,
    ) -> str:
        normalized = (
            value.strip().upper()
        )
        if not normalized:
            raise ValueError(
                "currency cannot be blank"
            )
        return normalized
PaperTradingExecutionOutcome = Literal[
    "NO_ACTION",
    "OPENED",
    "INCREASED",
    "CLOSED",
    "REJECTED",
]
class PaperTradingExecutionResult(
    BaseModel
):
    outcome: PaperTradingExecutionOutcome
    decision_action: Literal[
        "BUY",
        "SELL",
        "HOLD",
    ]
    message: str = Field(
        min_length=2,
        max_length=1000,
    )
    account_created: bool = False
    account: PaperTradingAccountResponse
    position: (
        PaperTradingPositionResponse
        | None
    ) = None
    order: (
        PaperTradingOrderResponse
        | None
    ) = None
