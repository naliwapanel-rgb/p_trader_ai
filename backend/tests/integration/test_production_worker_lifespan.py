from fastapi import FastAPI
import pytest

import app.main as main_module


class StubDatabaseRecoveryService:
    def __init__(
        self,
        engine,
    ):
        self.engine = engine

    def prepare_startup(
        self,
    ) -> dict[str, bool]:
        return {
            "prepared": True,
        }

    def checkpoint(
        self,
    ) -> dict[str, bool]:
        return {
            "checkpointed": True,
        }


@pytest.mark.asyncio
async def test_lifespan_skips_runtime_when_disabled(
    monkeypatch,
):
    monkeypatch.setattr(
        main_module.settings,
        "automation_runtime_enabled",
        False,
    )
    monkeypatch.setattr(
        main_module,
        "DatabaseRecoveryService",
        StubDatabaseRecoveryService,
    )

    def unexpected_runtime():
        raise AssertionError(
            "AutomationRuntime must not be "
            "constructed when disabled"
        )

    monkeypatch.setattr(
        main_module,
        "AutomationRuntime",
        unexpected_runtime,
    )

    application = FastAPI()

    async with main_module.lifespan(
        application
    ):
        assert (
            application.state
            .automation_runtime
            is None
        )
        assert (
            application.state
            .trading_bot_restore
            is None
        )
        assert (
            application.state
            .database_recovery
            == {
                "prepared": True,
            }
        )

    assert (
        application.state
        .database_checkpoint
        == {
            "checkpointed": True,
        }
    )
