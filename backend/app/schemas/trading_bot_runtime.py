from datetime import (
    datetime,
)
from typing import (
    Literal,
)
from pydantic import (
    BaseModel,
    Field,
)
class TradingBotTickJob(BaseModel):
    user_id: int = Field(
        ge=1,
    )
    bot_id: int = Field(
        ge=1,
    )
TradingBotTickOutcome = Literal[
    "HEARTBEAT",
    "SKIPPED",
]
class TradingBotTickResult(BaseModel):
    user_id: int = Field(
        ge=1,
    )
    bot_id: int = Field(
        ge=1,
    )
    outcome: TradingBotTickOutcome
    bot_status: str
    ran_at: datetime | None = None
class TradingBotRuntimeScheduleResult(
    BaseModel
):
    schedule_id: str
    registered: bool
    changed: bool
    running: bool
class TradingBotRuntimeRestoreResult(
    BaseModel
):
    scanned_count: int = Field(
        ge=0,
    )
    restored_count: int = Field(
        ge=0,
    )
    failed_count: int = Field(
        ge=0,
    )
    errors: list[str] = Field(
        default_factory=list
    )
