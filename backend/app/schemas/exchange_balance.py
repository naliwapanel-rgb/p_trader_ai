from pydantic import BaseModel, Field


class ExchangeCoinBalance(BaseModel):
    coin: str

    equity: float = 0.0
    wallet_balance: float = 0.0
    available_balance: float = 0.0
    locked_balance: float = 0.0

    usd_value: float = 0.0
    unrealized_pnl: float = 0.0


class ExchangeBalance(BaseModel):
    exchange: str
    account_type: str

    total_equity_usd: float = 0.0
    total_wallet_balance_usd: float = 0.0
    total_available_balance_usd: float = 0.0
    total_unrealized_pnl_usd: float = 0.0

    coins: list[ExchangeCoinBalance] = Field(default_factory=list)