from contextlib import (
    asynccontextmanager,
)
from fastapi import (
    FastAPI,
    HTTPException,
)
from fastapi.exceptions import (
    RequestValidationError,
)
from fastapi.middleware.cors import (
    CORSMiddleware,
)
from starlette.middleware.trustedhost import (
    TrustedHostMiddleware,
)
from app.api.v1.router import (
    api_router,
)
from app.core.config import (
    get_settings,
)
from app.core.exceptions import (
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.security.runtime import (
    validate_runtime_security,
)
from app.database.session import (
    engine,
)
from app.middleware.request_logger import (
    request_logger_middleware,
)
from app.middleware.security_headers import (
    security_headers_middleware,
)
from app.services.automation_runtime_service import (
    AutomationRuntime,
)
from app.services.database_recovery_service import (
    DatabaseRecoveryService,
)
settings = get_settings()
validate_runtime_security(
    settings
)
@asynccontextmanager
async def lifespan(
    application: FastAPI,
):
    database_recovery_service = (
        DatabaseRecoveryService(
            engine
        )
    )
    runtime = (
        AutomationRuntime()
        if settings.automation_runtime_enabled
        else None
    )
    application.state.automation_runtime = (
        runtime
    )
    database_prepared = False
    try:
        database_recovery = (
            database_recovery_service
            .prepare_startup()
        )
        database_prepared = True
        application.state.database_recovery = (
            database_recovery
        )
        if runtime is not None:
            await runtime.start()
            trading_bot_restore = (
                await runtime
                .bot_runtime_service
                .restore_running_bots()
            )
        else:
            trading_bot_restore = None
        application.state.trading_bot_restore = (
            trading_bot_restore
        )
        yield
    finally:
        try:
            if runtime is not None:
                await runtime.stop(
                    drain=True
                )
        finally:
            if database_prepared:
                try:
                    checkpoint = (
                        database_recovery_service
                        .checkpoint()
                    )
                    (
                        application
                        .state
                        .database_checkpoint
                    ) = checkpoint
                except Exception as error:
                    (
                        application
                        .state
                        .database_checkpoint
                    ) = None
                    (
                        application
                        .state
                        .database_checkpoint_error
                    ) = (
                        error
                        .__class__
                        .__name__
                    )
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        settings.app_description
    ),
    debug=settings.debug,
    openapi_url=(
        "/openapi.json"
        if settings.api_docs_enabled
        else None
    ),
    docs_url=(
        "/docs"
        if settings.api_docs_enabled
        else None
    ),
    redoc_url=(
        "/redoc"
        if settings.api_docs_enabled
        else None
    ),
    lifespan=lifespan,
)
app.middleware("http")(
    request_logger_middleware
)
app.add_exception_handler(
    HTTPException,
    http_exception_handler,
)
app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)
app.add_exception_handler(
    Exception,
    general_exception_handler,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        settings.backend_cors_origins
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if settings.is_hardened_environment:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.trusted_hosts,
        www_redirect=False,
    )
if settings.security_headers_enabled:
    app.middleware("http")(
        security_headers_middleware
    )
app.include_router(
    api_router,
    prefix="/api/v1",
)
@app.get("/")
async def root():
    return {
        "status": "online",
        "application": (
            settings.app_name
        ),
        "version": settings.app_version,
        "environment": (
            settings.environment
        ),
        "api_version": "v1",
    }
