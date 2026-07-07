from datetime import datetime

from pydantic import BaseModel, Field


class ExchangeAccountCreateRequest(BaseModel):
    exchange_name: str = Field(min_length=2, max_length=50)
    account_name: str = Field(min_length=2, max_length=150)
    api_key: str = Field(min_length=5, max_length=500)
    api_secret: str = Field(min_length=5, max_length=500)
    is_testnet: bool = False


class ExchangeAccountUpdateRequest(BaseModel):
    account_name: str | None = Field(default=None, min_length=2, max_length=150)
    api_key: str | None = Field(default=None, min_length=5, max_length=500)
    api_secret: str | None = Field(default=None, min_length=5, max_length=500)
    is_testnet: bool | None = None
    is_active: bool | None = None


class ExchangeAccountResponse(BaseModel):
    id: int
    user_id: int
    exchange_name: str
    account_name: str
    is_testnet: bool
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }