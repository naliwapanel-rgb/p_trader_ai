from fastapi import HTTPException
from app.schemas.automation import (
    AutomationRetryDecision,
    AutomationRetryPolicy,
)
class AutomationRetryService:
    @staticmethod
    def _error_type_names(
        error: BaseException,
    ) -> set[str]:
        return {
            error_type.__name__
            for error_type
            in type(error).mro()
        }
    @classmethod
    def is_retryable(
        cls,
        *,
        error: BaseException,
        policy: AutomationRetryPolicy,
    ) -> bool:
        if isinstance(error, HTTPException):
            if (
                error.status_code
                in (
                    policy
                    .retryable_http_status_codes
                )
            ):
                return True
        error_type_names = (
            cls._error_type_names(error)
        )
        configured_error_names = set(
            policy.retryable_error_names
        )
        if (
            error_type_names
            & configured_error_names
        ):
            return True
        return policy.retry_on_unknown_errors
    @staticmethod
    def calculate_delay(
        *,
        policy: AutomationRetryPolicy,
        attempt_number: int,
    ) -> float:
        if attempt_number < 1:
            raise ValueError(
                "attempt_number must be "
                "greater than zero"
            )
        if (
            policy.initial_delay_seconds
            == 0
        ):
            return 0.0
        if (
            policy.backoff_strategy
            == "FIXED"
        ):
            delay = (
                policy.initial_delay_seconds
            )
        else:
            delay = (
                policy.initial_delay_seconds
                * (
                    policy.backoff_multiplier
                    ** (attempt_number - 1)
                )
            )
        return min(
            delay,
            policy.maximum_delay_seconds,
        )
    @classmethod
    def decide(
        cls,
        *,
        error: BaseException,
        attempt_number: int,
        policy: AutomationRetryPolicy,
    ) -> AutomationRetryDecision:
        if attempt_number < 1:
            raise ValueError(
                "attempt_number must be "
                "greater than zero"
            )
        if (
            attempt_number
            >= policy.max_attempts
        ):
            return AutomationRetryDecision(
                retry=False,
                attempt_number=attempt_number,
                max_attempts=(
                    policy.max_attempts
                ),
                delay_seconds=0.0,
                reason=(
                    "Maximum retry attempts "
                    "reached"
                ),
            )
        if not cls.is_retryable(
            error=error,
            policy=policy,
        ):
            return AutomationRetryDecision(
                retry=False,
                attempt_number=attempt_number,
                max_attempts=(
                    policy.max_attempts
                ),
                delay_seconds=0.0,
                reason=(
                    "Error is not retryable "
                    "under the configured policy"
                ),
            )
        delay_seconds = (
            cls.calculate_delay(
                policy=policy,
                attempt_number=(
                    attempt_number
                ),
            )
        )
        return AutomationRetryDecision(
            retry=True,
            attempt_number=attempt_number,
            max_attempts=(
                policy.max_attempts
            ),
            delay_seconds=delay_seconds,
            reason=(
                "Error is retryable and "
                "attempts remain"
            ),
        )
