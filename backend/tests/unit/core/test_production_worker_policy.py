import pytest

from app.core.config import Settings
from app.core.security.runtime import (
    validate_runtime_security,
)


def test_single_worker_with_runtime_is_valid():
    settings = Settings(
        _env_file=None,
        web_concurrency=1,
        automation_runtime_enabled=True,
    )
    validate_runtime_security(settings)


def test_multiple_workers_with_runtime_are_rejected():
    settings = Settings(
        _env_file=None,
        web_concurrency=2,
        automation_runtime_enabled=True,
    )
    with pytest.raises(
        RuntimeError,
        match=(
            "in-memory automation runtime "
            "requires WEB_CONCURRENCY=1"
        ),
    ):
        validate_runtime_security(settings)


def test_multiple_workers_without_runtime_are_valid():
    settings = Settings(
        _env_file=None,
        web_concurrency=4,
        automation_runtime_enabled=False,
    )
    validate_runtime_security(settings)
