from datetime import datetime

from pydantic import BaseModel, Field


class AlertCreateRequest(BaseModel):
    symbol: str = Field(min_length=2, max_length=30)
    exchange: str = Field(default="BINANCE", min_length=2, max_length=50)
    alert_type: str = Field(min_length=2, max_length=50)
    target_value: float


class AlertUpdateRequest(BaseModel):
    symbol: str | None = Field(default=None, min_length=2, max_length=30)
    exchange: str | None = Field(default=None, min_length=2, max_length=50)
    alert_type: str | None = Field(default=None, min_length=2, max_length=50)
    target_value: float | None = None
    is_enabled: bool | None = None
    triggered: bool | None = None


class AlertResponse(BaseModel):
    id: int
    user_id: int
    symbol: str
    exchange: str
    alert_type: str
    target_value: float
    is_enabled: bool
    triggered: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }