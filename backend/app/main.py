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
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import (
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.middleware.request_logger import (
    request_logger_middleware,
)
from app.services.automation_runtime_service import (
    AutomationRuntime,
)
settings = get_settings()
@asynccontextmanager
async def lifespan(
    application: FastAPI,
):
    runtime = AutomationRuntime()
    application.state.automation_runtime = (
        runtime
    )
    await runtime.start()
    try:
        yield
    finally:
        await runtime.stop(
            drain=True
        )
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    debug=settings.debug,
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
app.include_router(
    api_router,
    prefix="/api/v1",
)
@app.get("/")
async def root():
    return {
        "status": "online",
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": (
            settings.environment
        ),
        "api_version": "v1",
    }
