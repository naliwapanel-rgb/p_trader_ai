from typing import Literal
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)
MarketCategory = Literal[
    "spot",
    "linear",
    "inverse",
]
MarketSortField = Literal[
    "turnover_24h",
    "volume_24h",
    "price_change_percent_24h",
    "absolute_price_change_percent_24h",
    "spread_percent",
    "last_price",
    "symbol",
]
class MarketTickerSnapshot(BaseModel):
    exchange: str
    category: MarketCategory
    symbol: str
    last_price: float = 0.0
    bid_price: float = 0.0
    bid_size: float = 0.0
    ask_price: float = 0.0
    ask_size: float = 0.0
    spread: float = 0.0
    spread_percent: float = 0.0
    previous_price_24h: float = 0.0
    price_change_24h: float = 0.0
    price_change_percent_24h: float = 0.0
    high_24h: float = 0.0
    low_24h: float = 0.0
    volume_24h: float = 0.0
    turnover_24h: float = 0.0
    index_price: float = 0.0
    mark_price: float = 0.0
    usd_index_price: float = 0.0
    open_interest: float = 0.0
    open_interest_value: float = 0.0
    funding_rate: float = 0.0
    next_funding_time_ms: int = 0
    observed_at_ms: int = 0
class MarketTickerBatch(BaseModel):
    exchange: str
    category: MarketCategory
    observed_at_ms: int = 0
    count: int = Field(
        default=0,
        ge=0,
    )
    tickers: list[MarketTickerSnapshot] = Field(
        default_factory=list
    )
class MarketScanRequest(BaseModel):
    exchange: Literal["BYBIT"] = "BYBIT"
    category: MarketCategory = "spot"
    is_testnet: bool = False
    quote_coin: str | None = Field(
        default="USDT",
        max_length=20,
    )
    symbols: list[str] = Field(
        default_factory=list,
        max_length=100,
    )
    minimum_price: float | None = Field(
        default=None,
        ge=0,
    )
    maximum_price: float | None = Field(
        default=None,
        ge=0,
    )
    minimum_volume_24h: float = Field(
        default=0.0,
        ge=0,
    )
    minimum_turnover_24h: float = Field(
        default=0.0,
        ge=0,
    )
    minimum_change_percent_24h: float | None = None
    maximum_change_percent_24h: float | None = None
    sort_by: MarketSortField = "turnover_24h"
    descending: bool = True
    limit: int = Field(
        default=50,
        ge=1,
        le=200,
    )
    @field_validator("quote_coin")
    @classmethod
    def normalize_quote_coin(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if not normalized:
            return None
        return normalized
    @field_validator("symbols")
    @classmethod
    def normalize_symbols(
        cls,
        values: list[str],
    ) -> list[str]:
        normalized: list[str] = []
        for value in values:
            symbol = value.strip().upper()
            if not symbol:
                raise ValueError(
                    "symbols cannot contain blank values"
                )
            if symbol not in normalized:
                normalized.append(symbol)
        return normalized
    @model_validator(mode="after")
    def validate_ranges(self):
        if (
            self.minimum_price is not None
            and self.maximum_price is not None
            and self.minimum_price
            > self.maximum_price
        ):
            raise ValueError(
                "minimum_price cannot exceed "
                "maximum_price"
            )
        if (
            self.minimum_change_percent_24h
            is not None
            and self.maximum_change_percent_24h
            is not None
            and self.minimum_change_percent_24h
            > self.maximum_change_percent_24h
        ):
            raise ValueError(
                "minimum_change_percent_24h "
                "cannot exceed "
                "maximum_change_percent_24h"
            )
        return self
class MarketScanResult(BaseModel):
    exchange: str
    category: MarketCategory
    quote_coin: str | None
    total_received: int = Field(ge=0)
    total_matched: int = Field(ge=0)
    returned_count: int = Field(ge=0)
    scanned_at_ms: int = 0
    tickers: list[MarketTickerSnapshot] = Field(
        default_factory=list
    )
