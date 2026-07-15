from pydantic import BaseModel, Field


class ExchangePosition(BaseModel):
    exchange: str
    category: str

    symbol: str
    side: str

    size: float = 0.0
    position_value: float = 0.0

    entry_price: float = 0.0
    break_even_price: float = 0.0
    mark_price: float = 0.0
    liquidation_price: float = 0.0

    leverage: float = 0.0

    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    cumulative_realized_pnl: float = 0.0

    take_profit: float = 0.0
    stop_loss: float = 0.0
    trailing_stop: float = 0.0

    initial_margin: float = 0.0
    maintenance_margin: float = 0.0

    position_status: str = ""
    position_index: int = 0
    auto_add_margin: bool = False
    reduce_only: bool = False

    created_at_ms: int = 0
    updated_at_ms: int = 0


class ExchangePositionList(BaseModel):
    exchange: str
    category: str
    settle_coin: str

    count: int = 0
    positions: list[ExchangePosition] = Field(default_factory=list)