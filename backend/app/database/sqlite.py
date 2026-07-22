from sqlite3 import (
    Connection as SQLiteConnection,
)
from sqlalchemy import (
    event,
)
from sqlalchemy.engine import (
    Engine,
)
SQLITE_BUSY_TIMEOUT_MS = 5000
def configure_sqlite_connection(
    dbapi_connection,
    connection_record,
) -> None:
    if not isinstance(
        dbapi_connection,
        SQLiteConnection,
    ):
        return
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute(
            "PRAGMA foreign_keys=ON"
        )
        cursor.execute(
            (
                "PRAGMA busy_timeout="
                f"{SQLITE_BUSY_TIMEOUT_MS}"
            )
        )
        cursor.execute(
            "PRAGMA synchronous=NORMAL"
        )
    finally:
        cursor.close()
def configure_sqlite_engine(
    engine: Engine,
) -> bool:
    if engine.dialect.name != "sqlite":
        return False
    if not event.contains(
        engine,
        "connect",
        configure_sqlite_connection,
    ):
        event.listen(
            engine,
            "connect",
            configure_sqlite_connection,
        )
    return True
