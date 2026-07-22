from datetime import (
    datetime,
)
from typing import (
    Literal,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)
CopyTradingSubscriptionStatus = Literal[
    "ACTIVE",
    "PAUSED",
    "STOPPED",
]
CopyTradingExecutionMode = Literal[
    "PAPER_ONLY",
]
class CopyTradingSubscriptionCreateRequest(
    BaseModel
):
    source_template_id: int = Field(
        gt=0,
    )
    follower_bot_id: int = Field(
        gt=0,
    )
    model_config = ConfigDict(
        extra="forbid",
    )
class CopyTradingSubscriptionResponse(
    BaseModel
):
    id: int
    follower_user_id: int
    source_template_id: int
    follower_bot_id: int
    status: (
        CopyTradingSubscriptionStatus
    )
    execution_mode: (
        CopyTradingExecutionMode
    )
    subscribed_template_version: int = (
        Field(
            ge=1,
        )
    )
    last_error: str | None = None
    last_mirrored_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(
        from_attributes=True,
    )
CopyTradingSubscriptionAction = Literal[
    "PAUSE",
    "RESUME",
    "STOP",
]
class CopyTradingSubscriptionActionResult(
    BaseModel
):
    action: CopyTradingSubscriptionAction
    previous_status: (
        CopyTradingSubscriptionStatus
    )
    status: CopyTradingSubscriptionStatus
    changed: bool
    subscription: (
        CopyTradingSubscriptionResponse
    )
