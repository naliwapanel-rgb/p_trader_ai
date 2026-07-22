import sqlite3
import pytest
from sqlalchemy import (
    create_engine,
)
from app.database.sqlite import (
    configure_sqlite_engine,
)
from app.services.database_recovery_service import (
    DatabaseRecoveryService,
)
def build_file_engine(
    tmp_path,
    name="recovery.db",
):
    engine = create_engine(
        (
            "sqlite:///"
            + str(tmp_path / name)
        ),
        connect_args={
            "check_same_thread": False,
        },
    )
    configure_sqlite_engine(
        engine
    )
    return engine
def test_prepare_startup_enables_wal(
    tmp_path,
):
    engine = build_file_engine(
        tmp_path
    )
    try:
        service = (
            DatabaseRecoveryService(
                engine
            )
        )
        snapshot = (
            service.prepare_startup()
        )
        assert snapshot.healthy is True
        assert (
            snapshot
            .foreign_keys_enabled
            is True
        )
        assert (
            snapshot.integrity_check
            == "ok"
        )
        assert (
            snapshot.journal_mode
            == "wal"
        )
        assert (
            snapshot
            .foreign_key_violation_count
            == 0
        )
    finally:
        engine.dispose()
def test_checkpoint_returns_result(
    tmp_path,
):
    engine = build_file_engine(
        tmp_path
    )
    try:
        service = (
            DatabaseRecoveryService(
                engine
            )
        )
        service.prepare_startup()
        checkpoint = (
            service.checkpoint()
        )
        assert checkpoint is not None
        assert checkpoint.busy >= 0
        assert checkpoint.log_frames >= 0
        assert (
            checkpoint
            .checkpointed_frames
            >= 0
        )
    finally:
        engine.dispose()
def test_existing_foreign_key_violation_is_detected(
    tmp_path,
):
    database_path = (
        tmp_path
        / "violations.db"
    )
    raw_connection = (
        sqlite3.connect(
            database_path
        )
    )
    try:
        raw_connection.execute(
            (
                "CREATE TABLE parent "
                "(id INTEGER PRIMARY KEY)"
            )
        )
        raw_connection.execute(
            (
                "CREATE TABLE child ("
                "id INTEGER PRIMARY KEY, "
                "parent_id INTEGER NOT NULL, "
                "FOREIGN KEY(parent_id) "
                "REFERENCES parent(id)"
                ")"
            )
        )
        raw_connection.execute(
            (
                "INSERT INTO child "
                "(id, parent_id) "
                "VALUES (1, 999)"
            )
        )
        raw_connection.commit()
    finally:
        raw_connection.close()
    engine = create_engine(
        (
            "sqlite:///"
            + str(database_path)
        ),
        connect_args={
            "check_same_thread": False,
        },
    )
    configure_sqlite_engine(
        engine
    )
    try:
        service = (
            DatabaseRecoveryService(
                engine
            )
        )
        snapshot = service.inspect()
        assert snapshot.healthy is False
        assert (
            snapshot
            .foreign_key_violation_count
            == 1
        )
        with pytest.raises(
            RuntimeError,
            match=(
                "Database startup "
                "validation failed"
            ),
        ):
            service.prepare_startup()
    finally:
        engine.dispose()
def test_memory_database_is_supported():
    engine = create_engine(
        "sqlite:///:memory:"
    )
    configure_sqlite_engine(
        engine
    )
    try:
        service = (
            DatabaseRecoveryService(
                engine
            )
        )
        snapshot = (
            service.prepare_startup()
        )
        assert snapshot.healthy is True
        assert snapshot.journal_mode in {
            "memory",
            "off",
        }
        assert service.checkpoint() is None
    finally:
        engine.dispose()
