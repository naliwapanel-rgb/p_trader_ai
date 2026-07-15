from decimal import Decimal

from pydantic import BaseModel


class ExchangeInstrumentRules(BaseModel):
    exchange: str
    category: str
    symbol: str

    status: str = ""

    base_coin: str = ""
    quote_coin: str = ""
    settle_coin: str = ""

    min_price: Decimal = Decimal("0")
    max_price: Decimal = Decimal("0")
    tick_size: Decimal = Decimal("0")

    min_order_quantity: Decimal = Decimal("0")
    max_limit_order_quantity: Decimal = Decimal("0")
    max_market_order_quantity: Decimal = Decimal("0")
    quantity_step: Decimal = Decimal("0")

    min_notional_value: Decimal = Decimal("0")