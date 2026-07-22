from datetime import (
    datetime,
)
from typing import (
    Any,
    Literal,
)
from pydantic import (
    BaseModel,
    Field,
)
CopyTradingMirrorOutcome = Literal[
    "EXECUTED",
    "SKIPPED",
    "FAILED",
]
class CopyTradingMirrorItemResult(
    BaseModel
):
    subscription_id: int = Field(
        gt=0,
    )
    follower_user_id: int = Field(
        gt=0,
    )
    follower_bot_id: int = Field(
        gt=0,
    )
    outcome: CopyTradingMirrorOutcome
    message: str
    paper_execution: (
        dict[str, Any] | None
    ) = None
class CopyTradingMirrorBatchResult(
    BaseModel
):
    source_template_id: int = Field(
        gt=0,
    )
    action: Literal[
        "BUY",
        "SELL",
        "HOLD",
    ]
    evaluated_at: datetime
    scanned_count: int = Field(
        ge=0,
    )
    executed_count: int = Field(
        ge=0,
    )
    skipped_count: int = Field(
        ge=0,
    )
    failed_count: int = Field(
        ge=0,
    )
    results: list[
        CopyTradingMirrorItemResult
    ] = Field(
        default_factory=list,
    )
