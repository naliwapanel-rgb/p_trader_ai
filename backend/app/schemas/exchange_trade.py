from typing import Literal

from pydantic import BaseModel, Field, model_validator


TradingSide = Literal["BUY", "SELL"]
TradingCategory = Literal["spot", "linear", "inverse"]
OrderCategory = Literal["spot", "linear", "inverse", "option"]
TimeInForce = Literal["GTC", "IOC", "FOK", "PostOnly"]
NormalizedOrderStatus = Literal[
    "PENDING",
    "NEW",
    "PARTIALLY_FILLED",
    "FILLED",
    "CANCELLED",
    "REJECTED",
    "EXPIRED",
    "UNKNOWN",
]
TradingSide = Literal["BUY", "SELL"]

PositionSide = Literal[
    "LONG",
    "SHORT",
]

class MarketOrderRequest(BaseModel):
    symbol: str = Field(min_length=3, max_length=30)
    side: TradingSide
    quantity: float = Field(gt=0)

    category: TradingCategory = "linear"
    time_in_force: TimeInForce = "IOC"

    reduce_only: bool = False
    close_on_trigger: bool = False

    client_order_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=36,
    )

    @model_validator(mode="after")
    def normalize_values(self):
        self.symbol = self.symbol.upper()
        return self


class LimitOrderRequest(BaseModel):
    symbol: str = Field(min_length=3, max_length=30)
    side: TradingSide

    quantity: float = Field(gt=0)
    price: float = Field(gt=0)

    category: TradingCategory = "linear"
    time_in_force: TimeInForce = "GTC"

    reduce_only: bool = False
    close_on_trigger: bool = False

    client_order_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=36,
    )

    @model_validator(mode="after")
    def normalize_values(self):
        self.symbol = self.symbol.upper()
        return self


class ExchangeOrderPlacement(BaseModel):
    exchange: str
    category: str

    order_id: str = ""
    client_order_id: str = ""

    symbol: str
    side: str
    order_type: str

    quantity: float
    price: float = 0.0

    dry_run: bool
    accepted: bool

    message: str


class CancelOrderRequest(BaseModel):
    symbol: str = Field(min_length=3, max_length=30)
    category: OrderCategory = "linear"

    order_id: str | None = Field(
        default=None,
        min_length=1,
    )

    client_order_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=36,
    )

    @model_validator(mode="after")
    def validate_request(self):
        self.symbol = self.symbol.upper()

        if not self.order_id and not self.client_order_id:
            raise ValueError(
                "Either order_id or client_order_id is required"
            )

        return self


class AmendOrderRequest(BaseModel):
    symbol: str = Field(min_length=3, max_length=30)
    category: OrderCategory = "linear"

    order_id: str | None = Field(
        default=None,
        min_length=1,
    )

    client_order_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=36,
    )

    quantity: float | None = Field(
        default=None,
        gt=0,
    )

    price: float | None = Field(
        default=None,
        gt=0,
    )

    trigger_price: float | None = Field(
        default=None,
        ge=0,
    )

    take_profit: float | None = Field(
        default=None,
        ge=0,
    )

    stop_loss: float | None = Field(
        default=None,
        ge=0,
    )

    @model_validator(mode="after")
    def validate_request(self):
        self.symbol = self.symbol.upper()

        if not self.order_id and not self.client_order_id:
            raise ValueError(
                "Either order_id or client_order_id is required"
            )

        amendment_values = (
            self.quantity,
            self.price,
            self.trigger_price,
            self.take_profit,
            self.stop_loss,
        )

        if all(value is None for value in amendment_values):
            raise ValueError(
                "At least one amendment value is required"
            )

        return self


class ExchangeOrderActionResult(BaseModel):
    exchange: str
    category: str
    symbol: str

    action: Literal["CANCEL", "AMEND"]

    order_id: str = ""
    client_order_id: str = ""

    dry_run: bool
    accepted: bool

    message: str

class ExchangeOrderExecution(BaseModel):
    exchange: str
    category: str

    order_id: str
    client_order_id: str = ""

    symbol: str
    side: str
    order_type: str
    status: NormalizedOrderStatus

    quantity: float = 0.0
    filled_quantity: float = 0.0
    remaining_quantity: float = 0.0

    price: float = 0.0
    average_price: float = 0.0

    cumulative_execution_value: float = 0.0
    cumulative_execution_fee: float = 0.0

    reduce_only: bool = False
    close_on_trigger: bool = False

    dry_run: bool = False
    accepted: bool = False
    verified: bool = False

    created_at_ms: int = 0
    updated_at_ms: int = 0

    message: str
    
    
class ClosePositionRequest(BaseModel):
    symbol: str = Field(
        min_length=3,
        max_length=30,
    )

    position_side: PositionSide

    quantity: float = Field(gt=0)

    category: TradingCategory = "linear"

    position_index: int = Field(
        default=0,
        ge=0,
        le=2,
    )

    time_in_force: TimeInForce = "IOC"

    client_order_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=36,
    )

    @model_validator(mode="after")
    def validate_close_position(self):
        self.symbol = self.symbol.upper()

        if (
            self.position_side == "LONG"
            and self.position_index == 2
        ):
            raise ValueError(
                "A LONG position cannot use position_index 2"
            )

        if (
            self.position_side == "SHORT"
            and self.position_index == 1
        ):
            raise ValueError(
                "A SHORT position cannot use position_index 1"
            )

        return self
    
class ClosePositionResult(BaseModel):
    exchange: str
    category: str

    order_id: str = ""
    client_order_id: str = ""

    symbol: str
    position_side: PositionSide
    closing_side: TradingSide
    position_index: int

    requested_quantity: float

    status: NormalizedOrderStatus = "PENDING"

    reduce_only: bool = True
    dry_run: bool
    accepted: bool
    verified: bool = False

    message: str