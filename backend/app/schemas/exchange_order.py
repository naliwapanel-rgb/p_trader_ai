from pydantic import BaseModel, Field


class ExchangeOrder(BaseModel):
    exchange: str
    category: str

    order_id: str
    client_order_id: str = ""

    symbol: str
    side: str
    order_type: str
    status: str

    price: float = 0.0
    average_price: float = 0.0

    quantity: float = 0.0
    filled_quantity: float = 0.0
    remaining_quantity: float = 0.0

    order_value: float = 0.0
    cumulative_execution_value: float = 0.0
    cumulative_execution_fee: float = 0.0

    time_in_force: str = ""
    position_index: int = 0

    reduce_only: bool = False
    close_on_trigger: bool = False

    trigger_price: float = 0.0
    trigger_direction: int = 0
    trigger_by: str = ""

    take_profit: float = 0.0
    stop_loss: float = 0.0

    order_filter: str = ""
    reject_reason: str = ""
    cancel_type: str = ""

    created_at_ms: int = 0
    updated_at_ms: int = 0


class ExchangeOrderList(BaseModel):
    exchange: str
    category: str
    settle_coin: str

    count: int = 0
    next_cursor: str = ""

    orders: list[ExchangeOrder] = Field(default_factory=list)