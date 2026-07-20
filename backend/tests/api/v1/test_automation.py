from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.testclient import (
    TestClient,
)
from app.api.dependencies import (
    get_current_user,
)
from app.api.v1.endpoints.automation import (
    router,
)
from app.services.automation_runtime_service import (
    AutomationRuntime,
)
def _market_job_payload(
    *,
    user_id: int | None = None,
):
    payload = {
        "account_id": 1,
        "order": {
            "symbol": "btcusdt",
            "side": "SELL",
            "quantity": 0.001,
            "reduce_only": True,
        },
    }
    if user_id is not None:
        payload["user_id"] = user_id
    return payload
def _build_app(
    *,
    user_id: int = 7,
):
    test_app = FastAPI()
    runtime = AutomationRuntime()
    test_app.state.automation_runtime = (
        runtime
    )
    test_app.include_router(router)
    test_app.dependency_overrides[
        get_current_user
    ] = lambda: SimpleNamespace(
        id=user_id
    )
    return test_app, runtime
def test_automation_routes_require_authentication():
    test_app = FastAPI()
    test_app.state.automation_runtime = (
        AutomationRuntime()
    )
    test_app.include_router(router)
    with TestClient(test_app) as client:
        response = client.get(
            "/automation/health"
        )
    assert response.status_code == 401
def test_health_and_snapshots_are_available():
    test_app, _ = _build_app()
    with TestClient(test_app) as client:
        health = client.get(
            "/automation/health"
        )
        worker = client.get(
            "/automation/worker"
        )
        scheduler = client.get(
            "/automation/scheduler"
        )
    assert health.status_code == 200
    assert worker.status_code == 200
    assert scheduler.status_code == 200
    assert (
        health.json()
        ["handlers_registered"]
        is True
    )
    assert (
        worker.json()
        ["registered_job_types"]
        == [
            "TRADE_LIMIT_ORDER",
            "TRADE_MARKET_ORDER",
        ]
    )
    assert (
        scheduler.json()
        ["registered_schedule_count"]
        == 0
    )
def test_job_submission_get_and_list():
    test_app, _ = _build_app()
    request_body = {
        "job_type": "trade_market_order",
        "payload": _market_job_payload(),
        "deduplication_key": "close-btc",
    }
    with TestClient(test_app) as client:
        submitted = client.post(
            "/automation/jobs",
            json=request_body,
        )
        assert submitted.status_code == 202
        result = submitted.json()
        job_id = result["job"]["id"]
        fetched = client.get(
            f"/automation/jobs/{job_id}"
        )
        listed = client.get(
            "/automation/jobs"
        )
    assert result["created"] is True
    assert (
        result["job"]["job_type"]
        == "TRADE_MARKET_ORDER"
    )
    assert (
        result["job"]["payload"]["user_id"]
        == 7
    )
    assert (
        result["job"]["deduplication_key"]
        == "close-btc"
    )
    assert fetched.status_code == 200
    assert fetched.json()["id"] == job_id
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["id"] == job_id
def test_job_submission_rejects_other_user():
    test_app, _ = _build_app(
        user_id=7
    )
    request_body = {
        "job_type": "TRADE_MARKET_ORDER",
        "payload": _market_job_payload(
            user_id=99
        ),
    }
    with TestClient(test_app) as client:
        response = client.post(
            "/automation/jobs",
            json=request_body,
        )
    assert response.status_code == 403
def test_unknown_job_is_not_visible():
    test_app, _ = _build_app()
    with TestClient(test_app) as client:
        response = client.get(
            "/automation/jobs/missing"
        )
    assert response.status_code == 404
def test_schedule_registration_start_and_stop():
    test_app, _ = _build_app()
    request_body = {
        "schedule_id": "reduce-btc",
        "job_type": "TRADE_MARKET_ORDER",
        "interval_seconds": 60,
        "initial_delay_seconds": 60,
        "payload": _market_job_payload(),
        "deduplication_key": (
            "reduce-btc-order"
        ),
    }
    with TestClient(test_app) as client:
        registered = client.post(
            "/automation/schedules",
            json=request_body,
        )
        started = client.post(
            (
                "/automation/schedules/"
                "reduce-btc/start"
            )
        )
        stopped = client.post(
            (
                "/automation/schedules/"
                "reduce-btc/stop"
            )
        )
        snapshot = client.get(
            "/automation/scheduler"
        )
    assert registered.status_code == 201
    assert (
        registered.json()["schedule_id"]
        == "reduce-btc"
    )
    assert started.status_code == 200
    assert started.json()["changed"] is True
    assert (
        started.json()
        ["schedule"]["running"]
        is True
    )
    assert stopped.status_code == 200
    assert stopped.json()["changed"] is True
    assert (
        stopped.json()
        ["schedule"]["running"]
        is False
    )
    assert snapshot.status_code == 200
    assert (
        snapshot.json()
        ["registered_schedule_count"]
        == 1
    )
    assert (
        snapshot.json()
        ["running_schedule_count"]
        == 0
    )
def test_schedule_ids_are_scoped_by_user():
    first_app, first_runtime = _build_app(
        user_id=7
    )
    second_app, _ = _build_app(
        user_id=8
    )
    second_app.state.automation_runtime = (
        first_runtime
    )
    request_body = {
        "schedule_id": "shared-name",
        "job_type": "TRADE_MARKET_ORDER",
        "interval_seconds": 60,
        "initial_delay_seconds": 60,
        "payload": _market_job_payload(),
    }
    with TestClient(first_app) as client:
        first_response = client.post(
            "/automation/schedules",
            json=request_body,
        )
    with TestClient(second_app) as client:
        second_response = client.post(
            "/automation/schedules",
            json=request_body,
        )
        second_snapshot = client.get(
            "/automation/scheduler"
        )
    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert (
        second_snapshot.json()
        ["registered_schedule_count"]
        == 1
    )
def test_missing_runtime_returns_service_unavailable():
    test_app = FastAPI()
    test_app.include_router(router)
    test_app.dependency_overrides[
        get_current_user
    ] = lambda: SimpleNamespace(id=7)
    with TestClient(test_app) as client:
        response = client.get(
            "/automation/health"
        )
    assert response.status_code == 503
def test_jobs_are_not_visible_to_other_users():
    first_app, shared_runtime = _build_app(
        user_id=7
    )
    second_app, _ = _build_app(
        user_id=8
    )
    second_app.state.automation_runtime = (
        shared_runtime
    )
    request_body = {
        "job_type": "TRADE_MARKET_ORDER",
        "payload": _market_job_payload(),
        "deduplication_key": (
            "private-user-seven-job"
        ),
    }
    with TestClient(first_app) as client:
        submitted = client.post(
            "/automation/jobs",
            json=request_body,
        )
    assert submitted.status_code == 202
    job_id = submitted.json()["job"]["id"]
    with TestClient(second_app) as client:
        fetched = client.get(
            f"/automation/jobs/{job_id}"
        )
        listed = client.get(
            "/automation/jobs"
        )
        worker = client.get(
            "/automation/worker"
        )
    assert fetched.status_code == 404
    assert listed.status_code == 200
    assert listed.json() == []
    assert worker.status_code == 200
    assert worker.json()["total_jobs"] == 0
def test_schedule_controls_are_not_visible_to_other_users():
    first_app, shared_runtime = _build_app(
        user_id=7
    )
    second_app, _ = _build_app(
        user_id=8
    )
    second_app.state.automation_runtime = (
        shared_runtime
    )
    request_body = {
        "schedule_id": "private-schedule",
        "job_type": "TRADE_MARKET_ORDER",
        "interval_seconds": 60,
        "initial_delay_seconds": 60,
        "payload": _market_job_payload(),
    }
    with TestClient(first_app) as client:
        registered = client.post(
            "/automation/schedules",
            json=request_body,
        )
    assert registered.status_code == 201
    with TestClient(second_app) as client:
        start_response = client.post(
            (
                "/automation/schedules/"
                "private-schedule/start"
            )
        )
        stop_response = client.post(
            (
                "/automation/schedules/"
                "private-schedule/stop"
            )
        )
        scheduler = client.get(
            "/automation/scheduler"
        )
    assert start_response.status_code == 404
    assert stop_response.status_code == 404
    assert scheduler.status_code == 200
    assert (
        scheduler.json()
        ["registered_schedule_count"]
        == 0
    )
