import time
from typing import Any, Literal
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)
AutomationJobStatus = Literal[
    "QUEUED",
    "RUNNING",
    "SUCCEEDED",
    "FAILED",
    "CANCELLED",
]
AutomationBackoffStrategy = Literal[
    "FIXED",
    "EXPONENTIAL",
]
class AutomationRetryPolicy(BaseModel):
    max_attempts: int = Field(
        default=1,
        ge=1,
        le=10,
    )
    initial_delay_seconds: float = Field(
        default=0.0,
        ge=0,
        le=3600,
    )
    backoff_strategy: (
        AutomationBackoffStrategy
    ) = "EXPONENTIAL"
    backoff_multiplier: float = Field(
        default=2.0,
        ge=1,
        le=10,
    )
    maximum_delay_seconds: float = Field(
        default=60.0,
        ge=0,
        le=3600,
    )
    retryable_error_names: list[str] = Field(
        default_factory=lambda: [
            "TimeoutError",
            "ConnectionError",
            "OSError",
        ],
        max_length=50,
    )
    retryable_http_status_codes: list[int] = (
        Field(
            default_factory=lambda: [
                408,
                425,
                429,
                500,
                502,
                503,
                504,
            ],
            max_length=50,
        )
    )
    retry_on_unknown_errors: bool = False
    @field_validator(
        "retryable_error_names"
    )
    @classmethod
    def normalize_error_names(
        cls,
        values: list[str],
    ) -> list[str]:
        normalized: list[str] = []
        for value in values:
            name = value.strip()
            if not name:
                raise ValueError(
                    "retryable error names "
                    "cannot be blank"
                )
            if name not in normalized:
                normalized.append(name)
        return normalized
    @field_validator(
        "retryable_http_status_codes"
    )
    @classmethod
    def validate_http_status_codes(
        cls,
        values: list[int],
    ) -> list[int]:
        normalized: list[int] = []
        for value in values:
            if value < 100 or value > 599:
                raise ValueError(
                    "retryable HTTP status codes "
                    "must be between 100 and 599"
                )
            if value not in normalized:
                normalized.append(value)
        return normalized
    @model_validator(mode="after")
    def validate_delay_range(self):
        if (
            self.maximum_delay_seconds
            < self.initial_delay_seconds
        ):
            raise ValueError(
                "maximum_delay_seconds cannot "
                "be below initial_delay_seconds"
            )
        return self
class AutomationRetryDecision(BaseModel):
    retry: bool
    attempt_number: int = Field(
        ge=1,
    )
    max_attempts: int = Field(
        ge=1,
    )
    delay_seconds: float = Field(
        default=0.0,
        ge=0,
    )
    reason: str
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
    attempt_count: int = Field(
        default=0,
        ge=0,
    )
    retry_count: int = Field(
        default=0,
        ge=0,
    )
    max_attempts: int = Field(
        default=1,
        ge=1,
    )
    retry_delays_seconds: list[float] = (
        Field(
            default_factory=list
        )
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
    total_attempts: int = Field(
        ge=0,
    )
    retried_job_count: int = Field(
        ge=0,
    )
    registered_job_types: list[str] = Field(
        default_factory=list
    )
class AutomationIntervalSchedule(BaseModel):
    schedule_id: str = Field(
        min_length=1,
        max_length=100,
    )
    job_type: str = Field(
        min_length=2,
        max_length=100,
    )
    interval_seconds: float = Field(
        gt=0,
        le=86400,
    )
    initial_delay_seconds: float = Field(
        default=0.0,
        ge=0,
        le=86400,
    )
    payload: dict[str, Any] = Field(
        default_factory=dict
    )
    deduplication_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    enabled: bool = True
    max_runs: int | None = Field(
        default=None,
        ge=1,
        le=100000,
    )
    @field_validator("schedule_id")
    @classmethod
    def normalize_schedule_id(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError(
                "schedule_id cannot be blank"
            )
        return normalized
    @field_validator("job_type")
    @classmethod
    def normalize_schedule_job_type(
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
    def normalize_schedule_deduplication_key(
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
class AutomationScheduleState(BaseModel):
    schedule_id: str
    job_type: str
    enabled: bool
    running: bool = False
    interval_seconds: float = Field(
        gt=0,
    )
    max_runs: int | None = Field(
        default=None,
        ge=1,
    )
    submission_count: int = Field(
        default=0,
        ge=0,
    )
    created_job_count: int = Field(
        default=0,
        ge=0,
    )
    duplicate_submission_count: int = Field(
        default=0,
        ge=0,
    )
    failure_count: int = Field(
        default=0,
        ge=0,
    )
    started_at_ms: int = Field(
        default=0,
        ge=0,
    )
    stopped_at_ms: int = Field(
        default=0,
        ge=0,
    )
    last_submitted_at_ms: int = Field(
        default=0,
        ge=0,
    )
    next_run_at_ms: int = Field(
        default=0,
        ge=0,
    )
    last_job_id: str | None = None
    last_error: str | None = None
class AutomationSchedulerSnapshot(BaseModel):
    registered_schedule_count: int = Field(
        ge=0,
    )
    running_schedule_count: int = Field(
        ge=0,
    )
    total_submissions: int = Field(
        ge=0,
    )
    total_created_jobs: int = Field(
        ge=0,
    )
    total_duplicate_submissions: int = Field(
        ge=0,
    )
    total_failures: int = Field(
        ge=0,
    )
    schedules: list[
        AutomationScheduleState
    ] = Field(
        default_factory=list
    )
class AutomationRuntimeHealth(BaseModel):
    healthy: bool
    started: bool
    handlers_registered: bool
    worker: AutomationWorkerSnapshot
    scheduler: AutomationSchedulerSnapshot
class AutomationScheduleActionResult(BaseModel):
    changed: bool
    schedule: AutomationScheduleState
