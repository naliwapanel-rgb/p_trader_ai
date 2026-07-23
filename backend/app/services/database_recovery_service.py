from sqlalchemy.engine import (
    Engine,
)
from app.schemas.database_recovery import (
    DatabaseCheckpointResult,
    DatabaseRecoverySnapshot,
)
class DatabaseRecoveryService:
    def __init__(
        self,
        engine: Engine,
    ):
        self.engine = engine
    @property
    def is_sqlite(self) -> bool:
        return (
            self.engine.dialect.name
            == "sqlite"
        )
    @property
    def is_file_sqlite(self) -> bool:
        if not self.is_sqlite:
            return False
        database = self.engine.url.database
        return database not in {
            None,
            "",
            ":memory:",
        }
    def _prepare_sqlite_journal(
        self,
    ) -> None:
        raw_connection = (
            self.engine.raw_connection()
        )
        cursor = raw_connection.cursor()
        try:
            if self.is_file_sqlite:
                row = cursor.execute(
                    "PRAGMA journal_mode=WAL"
                ).fetchone()
                journal_mode = (
                    str(row[0]).lower()
                    if row
                    else ""
                )
                if journal_mode != "wal":
                    raise RuntimeError(
                        "SQLite WAL journal "
                        "mode could not be enabled"
                    )
                cursor.execute(
                    "PRAGMA "
                    "wal_autocheckpoint=1000"
                )
            raw_connection.commit()
        finally:
            cursor.close()
            raw_connection.close()
    def _inspect_non_sqlite(
        self,
    ) -> DatabaseRecoverySnapshot:
        try:
            with self.engine.connect() as connection:
                probe = (
                    connection
                    .exec_driver_sql(
                        "SELECT 1"
                    )
                    .scalar_one()
                )
        except Exception as error:
            raise RuntimeError(
                "Database startup validation "
                "failed"
            ) from error
        healthy = probe == 1
        return DatabaseRecoverySnapshot(
            backend=(
                self.engine.dialect.name
            ),
            healthy=healthy,
            integrity_check=(
                "CONNECTION_OK"
                if healthy
                else "CONNECTION_FAILED"
            ),
        )
    def inspect(
        self,
    ) -> DatabaseRecoverySnapshot:
        if not self.is_sqlite:
            return (
                self._inspect_non_sqlite()
            )
        with self.engine.connect() as connection:
            foreign_keys = int(
                connection.exec_driver_sql(
                    "PRAGMA foreign_keys"
                ).scalar_one()
            )
            integrity_rows = list(
                connection.exec_driver_sql(
                    "PRAGMA quick_check"
                ).scalars()
            )
            integrity_check = "; ".join(
                str(value)
                for value in integrity_rows
            )
            journal_mode = str(
                connection.exec_driver_sql(
                    "PRAGMA journal_mode"
                ).scalar_one()
            ).lower()
            busy_timeout_ms = int(
                connection.exec_driver_sql(
                    "PRAGMA busy_timeout"
                ).scalar_one()
            )
            foreign_key_violations = (
                connection.exec_driver_sql(
                    "PRAGMA foreign_key_check"
                ).fetchall()
            )
        integrity_healthy = (
            integrity_rows == ["ok"]
        )
        journal_healthy = (
            not self.is_file_sqlite
            or journal_mode == "wal"
        )
        healthy = (
            foreign_keys == 1
            and integrity_healthy
            and journal_healthy
            and not foreign_key_violations
        )
        return DatabaseRecoverySnapshot(
            backend="sqlite",
            healthy=healthy,
            foreign_keys_enabled=(
                foreign_keys == 1
            ),
            integrity_check=(
                integrity_check
            ),
            journal_mode=journal_mode,
            busy_timeout_ms=(
                busy_timeout_ms
            ),
            foreign_key_violation_count=len(
                foreign_key_violations
            ),
        )
    def prepare_startup(
        self,
    ) -> DatabaseRecoverySnapshot:
        if self.is_sqlite:
            self._prepare_sqlite_journal()
        snapshot = self.inspect()
        if not snapshot.healthy:
            raise RuntimeError(
                "Database startup validation "
                "failed"
            )
        return snapshot
    def checkpoint(
        self,
    ) -> (
        DatabaseCheckpointResult
        | None
    ):
        if not self.is_file_sqlite:
            return None
        raw_connection = (
            self.engine.raw_connection()
        )
        cursor = raw_connection.cursor()
        try:
            row = cursor.execute(
                "PRAGMA "
                "wal_checkpoint(PASSIVE)"
            ).fetchone()
            if row is None:
                raise RuntimeError(
                    "SQLite WAL checkpoint "
                    "did not return a result"
                )
            return DatabaseCheckpointResult(
                busy=int(row[0]),
                log_frames=int(row[1]),
                checkpointed_frames=int(
                    row[2]
                ),
            )
        finally:
            cursor.close()
            raw_connection.close()
