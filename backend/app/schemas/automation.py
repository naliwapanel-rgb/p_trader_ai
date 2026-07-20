import time
from typing import Any, Literal
from pydantic import (
    BaseModel,
    Field,
    field_validator,
)
AutomationJobStatus = Literal[
    "QUEUED",
    "RUNNING",
    "SUCCEEDED",
    "FAILED",
    "CANCELLED",
]
class AutomationJobSubmission(BaseModel):
    job_type: str = Field(
        min_length=2,
        max_length=100,
    )
    payload: dict[str, Any] = Field(
        default_factory=dict
    )
    deduplication_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    @field_validator("job_type")
    @classmethod
    def normalize_job_type(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError(
                "job_type cannot be blank"
            )
        return normalized
    @field_validator("deduplication_key")
    @classmethod
    def normalize_deduplication_key(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError(
                "deduplication_key cannot be blank"
            )
        return normalized
class AutomationJob(BaseModel):
    id: str
    job_type: str
    payload: dict[str, Any] = Field(
        default_factory=dict
    )
    deduplication_key: str | None = None
    status: AutomationJobStatus = "QUEUED"
    created_at_ms: int = Field(
        default_factory=lambda: int(
            time.time() * 1000
        ),
        ge=0,
    )
    started_at_ms: int = Field(
        default=0,
        ge=0,
    )
    completed_at_ms: int = Field(
        default=0,
        ge=0,
    )
    result: Any = None
    error_message: str | None = None
class AutomationJobSubmissionResult(BaseModel):
    job: AutomationJob
    created: bool
class AutomationWorkerSnapshot(BaseModel):
    running: bool
    accepting_jobs: bool
    queue_size: int = Field(
        ge=0,
    )
    total_jobs: int = Field(
        ge=0,
    )
    queued_count: int = Field(
        ge=0,
    )
    running_count: int = Field(
        ge=0,
    )
    succeeded_count: int = Field(
        ge=0,
    )
    failed_count: int = Field(
        ge=0,
    )
    cancelled_count: int = Field(
        ge=0,
    )
    registered_job_types: list[str] = Field(
        default_factory=list
    )
