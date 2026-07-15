from typing import Literal

from pydantic import BaseModel, Field, model_validator


TradingSide = Literal["BUY", "SELL"]
TradingCategory = Literal["spot", "linear", "inverse"]
TimeInForce = Literal["GTC", "IOC", "FOK", "PostOnly"]


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