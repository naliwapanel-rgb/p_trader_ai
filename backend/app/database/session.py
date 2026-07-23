from sqlalchemy import (
    create_engine,
)
from sqlalchemy.engine import (
    Engine,
    make_url,
)
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
)
from app.core.config import (
    Settings,
    get_settings,
)
from app.database.sqlite import (
    configure_sqlite_engine,
)
def create_database_engine(
    settings: Settings | None = None,
) -> Engine:
    active_settings = (
        settings
        or get_settings()
    )
    database_url = make_url(
        active_settings.database_url
    )
    backend = (
        database_url
        .get_backend_name()
    )
    engine_options: dict = {
        "pool_pre_ping": True,
    }
    if backend == "sqlite":
        engine_options[
            "connect_args"
        ] = {
            "check_same_thread": False,
        }
    else:
        engine_options.update({
            "pool_size": (
                active_settings
                .database_pool_size
            ),
            "max_overflow": (
                active_settings
                .database_max_overflow
            ),
            "pool_timeout": (
                active_settings
                .database_pool_timeout_seconds
            ),
            "pool_recycle": (
                active_settings
                .database_pool_recycle_seconds
            ),
        })
    database_engine = create_engine(
        database_url,
        **engine_options,
    )
    configure_sqlite_engine(
        database_engine
    )
    return database_engine
settings = get_settings()
engine = create_database_engine(
    settings
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
Base = declarative_base()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
