from datetime import datetime

from pydantic import BaseModel


class NotificationPreferenceUpdateRequest(BaseModel):
    email_enabled: bool | None = None
    push_enabled: bool | None = None
    sound_enabled: bool | None = None
    price_alerts: bool | None = None
    arbitrage_alerts: bool | None = None
    ai_alerts: bool | None = None
    news_alerts: bool | None = None


class NotificationPreferenceResponse(BaseModel):
    id: int
    user_id: int
    email_enabled: bool
    push_enabled: bool
    sound_enabled: bool
    price_alerts: bool
    arbitrage_alerts: bool
    ai_alerts: bool
    news_alerts: bool
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }