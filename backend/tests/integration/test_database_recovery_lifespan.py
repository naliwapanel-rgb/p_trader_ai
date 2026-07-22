from types import (
    SimpleNamespace,
)
from unittest.mock import (
    AsyncMock,
    MagicMock,
)
import pytest
from fastapi import (
    FastAPI,
)
from app import (
    main as module,
)
def build_runtime(
    *,
    restore_result=None,
    restore_error=None,
):
    restore = AsyncMock(
        return_value=restore_result
    )
    if restore_error is not None:
        restore.side_effect = (
            restore_error
        )
    return SimpleNamespace(
        start=AsyncMock(
            return_value=True
        ),
        stop=AsyncMock(
            return_value=True
        ),
        bot_runtime_service=(
            SimpleNamespace(
                restore_running_bots=(
                    restore
                ),
            )
        ),
    )
@pytest.mark.asyncio
async def test_lifespan_prepares_and_checkpoints_database(
    monkeypatch,
):
    runtime = build_runtime(
        restore_result={
            "restored": 0,
        }
    )
    snapshot = SimpleNamespace(
        healthy=True,
    )
    checkpoint = SimpleNamespace(
        busy=0,
    )
    recovery_service = MagicMock()
    (
        recovery_service
        .prepare_startup
        .return_value
    ) = snapshot
    (
        recovery_service
        .checkpoint
        .return_value
    ) = checkpoint
    monkeypatch.setattr(
        module,
        "AutomationRuntime",
        lambda: runtime,
    )
    monkeypatch.setattr(
        module,
        "DatabaseRecoveryService",
        lambda engine: recovery_service,
    )
    application = FastAPI()
    async with module.lifespan(
        application
    ):
        assert (
            application
            .state
            .database_recovery
            is snapshot
        )
        assert (
            application
            .state
            .automation_runtime
            is runtime
        )
    runtime.start.assert_awaited_once()
    (
        runtime
        .bot_runtime_service
        .restore_running_bots
        .assert_awaited_once()
    )
    runtime.stop.assert_awaited_once_with(
        drain=True
    )
    (
        recovery_service
        .checkpoint
        .assert_called_once_with()
    )
    assert (
        application
        .state
        .database_checkpoint
        is checkpoint
    )
@pytest.mark.asyncio
async def test_restore_failure_stops_runtime(
    monkeypatch,
):
    runtime = build_runtime(
        restore_error=RuntimeError(
            "Restore failed"
        )
    )
    recovery_service = MagicMock()
    (
        recovery_service
        .prepare_startup
        .return_value
    ) = SimpleNamespace(
        healthy=True,
    )
    monkeypatch.setattr(
        module,
        "AutomationRuntime",
        lambda: runtime,
    )
    monkeypatch.setattr(
        module,
        "DatabaseRecoveryService",
        lambda engine: recovery_service,
    )
    application = FastAPI()
    with pytest.raises(
        RuntimeError,
        match="Restore failed",
    ):
        async with module.lifespan(
            application
        ):
            pass
    runtime.stop.assert_awaited_once_with(
        drain=True
    )
    (
        recovery_service
        .checkpoint
        .assert_called_once_with()
    )
@pytest.mark.asyncio
async def test_database_failure_prevents_runtime_start(
    monkeypatch,
):
    runtime = build_runtime()
    recovery_service = MagicMock()
    (
        recovery_service
        .prepare_startup
        .side_effect
    ) = RuntimeError(
        "Database startup validation failed"
    )
    monkeypatch.setattr(
        module,
        "AutomationRuntime",
        lambda: runtime,
    )
    monkeypatch.setattr(
        module,
        "DatabaseRecoveryService",
        lambda engine: recovery_service,
    )
    application = FastAPI()
    with pytest.raises(
        RuntimeError,
        match=(
            "Database startup "
            "validation failed"
        ),
    ):
        async with module.lifespan(
            application
        ):
            pass
    runtime.start.assert_not_awaited()
    runtime.stop.assert_awaited_once_with(
        drain=True
    )
    recovery_service.checkpoint.assert_not_called()
