from fastapi.testclient import (
    TestClient,
)
from app.main import app
from app.services.automation_runtime_service import (
    AutomationRuntime,
)
def test_fastapi_lifespan_starts_and_stops_runtime():
    runtime = None
    with TestClient(app):
        runtime = getattr(
            app.state,
            "automation_runtime",
            None,
        )
        assert isinstance(
            runtime,
            AutomationRuntime,
        )
        health = runtime.health()
        assert health.healthy is True
        assert health.started is True
        assert health.worker.running is True
        assert (
            health.scheduler
            .running_schedule_count
            == 0
        )
    assert runtime is not None
    assert runtime.started is False
    assert runtime.worker.is_running is False
