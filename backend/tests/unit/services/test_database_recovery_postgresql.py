from unittest.mock import (
    MagicMock,
)
import pytest
from app.services.database_recovery_service import (
    DatabaseRecoveryService,
)
def build_postgresql_engine(
    *,
    probe=1,
    connect_error=None,
):
    engine = MagicMock()
    engine.dialect.name = "postgresql"
    engine.url.database = "p_trader_ai"
    connection = MagicMock()
    (
        connection
        .exec_driver_sql
        .return_value
        .scalar_one
        .return_value
    ) = probe
    context_manager = MagicMock()
    if connect_error is not None:
        (
            context_manager
            .__enter__
            .side_effect
        ) = connect_error
    else:
        (
            context_manager
            .__enter__
            .return_value
        ) = connection
    engine.connect.return_value = (
        context_manager
    )
    return engine, connection
def test_postgresql_startup_probes_connection(
):
    engine, connection = (
        build_postgresql_engine()
    )
    service = DatabaseRecoveryService(
        engine
    )
    snapshot = service.prepare_startup()
    assert snapshot.healthy is True
    assert snapshot.backend == "postgresql"
    assert (
        snapshot.integrity_check
        == "CONNECTION_OK"
    )
    (
        connection
        .exec_driver_sql
        .assert_called_once_with(
            "SELECT 1"
        )
    )
    assert service.checkpoint() is None
def test_postgresql_failed_probe_is_unhealthy(
):
    engine, _ = build_postgresql_engine(
        probe=0,
    )
    service = DatabaseRecoveryService(
        engine
    )
    snapshot = service.inspect()
    assert snapshot.healthy is False
    assert (
        snapshot.integrity_check
        == "CONNECTION_FAILED"
    )
    with pytest.raises(
        RuntimeError,
        match=(
            "Database startup "
            "validation failed"
        ),
    ):
        service.prepare_startup()
def test_postgresql_connection_error_is_sanitized(
):
    engine, _ = build_postgresql_engine(
        connect_error=RuntimeError(
            "credential-bearing driver error"
        ),
    )
    service = DatabaseRecoveryService(
        engine
    )
    with pytest.raises(
        RuntimeError,
        match=(
            "^Database startup "
            "validation failed$"
        ),
    ):
        service.prepare_startup()
