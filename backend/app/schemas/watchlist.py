from datetime import datetime

from pydantic import BaseModel, Field


class WatchlistCreateRequest(BaseModel):
    symbol: str = Field(min_length=2, max_length=30)
    exchange: str = Field(default="BINANCE", min_length=2, max_length=50)


class WatchlistResponse(BaseModel):
    id: int
    user_id: int
    symbol: str
    exchange: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }