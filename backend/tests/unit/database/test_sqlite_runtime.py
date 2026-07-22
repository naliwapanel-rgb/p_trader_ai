import pytest
from sqlalchemy import (
    create_engine,
    event,
)
from sqlalchemy.exc import (
    IntegrityError,
)
from app.database.sqlite import (
    SQLITE_BUSY_TIMEOUT_MS,
    configure_sqlite_connection,
    configure_sqlite_engine,
)
def build_engine(
    tmp_path,
):
    return create_engine(
        (
            "sqlite:///"
            + str(
                tmp_path
                / "sqlite_runtime.db"
            )
        ),
        connect_args={
            "check_same_thread": False,
        },
    )
def test_sqlite_pragmas_are_enabled(
    tmp_path,
):
    engine = build_engine(
        tmp_path
    )
    try:
        assert (
            configure_sqlite_engine(
                engine
            )
            is True
        )
        with engine.connect() as (
            connection
        ):
            foreign_keys = (
                connection
                .exec_driver_sql(
                    "PRAGMA foreign_keys"
                )
                .scalar_one()
            )
            busy_timeout = (
                connection
                .exec_driver_sql(
                    "PRAGMA busy_timeout"
                )
                .scalar_one()
            )
            synchronous = (
                connection
                .exec_driver_sql(
                    "PRAGMA synchronous"
                )
                .scalar_one()
            )
        assert foreign_keys == 1
        assert busy_timeout == (
            SQLITE_BUSY_TIMEOUT_MS
        )
        assert synchronous == 1
    finally:
        engine.dispose()
def test_foreign_key_constraint_is_enforced(
    tmp_path,
):
    engine = build_engine(
        tmp_path
    )
    configure_sqlite_engine(
        engine
    )
    try:
        with engine.begin() as (
            connection
        ):
            connection.exec_driver_sql(
                (
                    "CREATE TABLE parent "
                    "(id INTEGER PRIMARY KEY)"
                )
            )
            connection.exec_driver_sql(
                (
                    "CREATE TABLE child ("
                    "id INTEGER PRIMARY KEY, "
                    "parent_id INTEGER NOT NULL, "
                    "FOREIGN KEY(parent_id) "
                    "REFERENCES parent(id)"
                    ")"
                )
            )
        with pytest.raises(
            IntegrityError,
        ):
            with engine.begin() as (
                connection
            ):
                connection.exec_driver_sql(
                    (
                        "INSERT INTO child "
                        "(id, parent_id) "
                        "VALUES (1, 999)"
                    )
                )
    finally:
        engine.dispose()
def test_engine_configuration_is_idempotent(
    tmp_path,
):
    engine = build_engine(
        tmp_path
    )
    try:
        assert configure_sqlite_engine(
            engine
        )
        assert configure_sqlite_engine(
            engine
        )
        assert event.contains(
            engine,
            "connect",
            configure_sqlite_connection,
        )
    finally:
        engine.dispose()
