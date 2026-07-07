from datetime import datetime

from pydantic import BaseModel, Field


class PortfolioCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    base_currency: str = Field(default="USDT", min_length=2, max_length=20)


class PortfolioUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    base_currency: str | None = Field(default=None, min_length=2, max_length=20)
    total_value: float | None = Field(default=None, ge=0)
    profit_loss: float | None = None


class PortfolioResponse(BaseModel):
    id: int
    user_id: int
    name: str
    base_currency: str
    total_value: float
    profit_loss: float
    created_at: datetime

    model_config = {
        "from_attributes": True
    }