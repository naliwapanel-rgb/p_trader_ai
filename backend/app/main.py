from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    debug=settings.debug,
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "status": "online",
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "api_version": "v1",
    }