from pydantic import (
    BaseModel,
    Field,
)
class DatabaseRecoverySnapshot(
    BaseModel
):
    backend: str
    healthy: bool
    foreign_keys_enabled: (
        bool | None
    ) = None
    integrity_check: str
    journal_mode: str | None = None
    busy_timeout_ms: int | None = (
        Field(
            default=None,
            ge=0,
        )
    )
    foreign_key_violation_count: int = (
        Field(
            default=0,
            ge=0,
        )
    )
class DatabaseCheckpointResult(
    BaseModel
):
    busy: int = Field(
        ge=0,
    )
    log_frames: int = Field(
        ge=0,
    )
    checkpointed_frames: int = Field(
        ge=0,
    )
