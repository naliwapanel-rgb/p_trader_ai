from app.core.config import (
    Settings,
)
from app.database.session import (
    create_database_engine,
)
def test_sqlite_engine_configuration(
) -> None:
    settings = Settings(
        _env_file=None,
        database_url=(
            "sqlite:///:memory:"
        ),
    )
    engine = create_database_engine(
        settings
    )
    try:
        assert engine.dialect.name == "sqlite"
        assert engine.pool._pre_ping is True
    finally:
        engine.dispose()
def test_postgresql_engine_pool_configuration(
) -> None:
    settings = Settings(
        _env_file=None,
        database_url=(
            "postgresql+psycopg2://"
            "user:password@localhost/"
            "p_trader_ai"
        ),
        database_pool_size=7,
        database_max_overflow=13,
        database_pool_timeout_seconds=21,
        database_pool_recycle_seconds=900,
    )
    engine = create_database_engine(
        settings
    )
    try:
        assert (
            engine.dialect.name
            == "postgresql"
        )
        assert engine.pool.size() == 7
        assert engine.pool._max_overflow == 13
        assert engine.pool.timeout() == 21
        assert engine.pool._recycle == 900
        assert engine.pool._pre_ping is True
    finally:
        engine.dispose()
