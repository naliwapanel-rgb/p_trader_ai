from fastapi import APIRouter

from app.api.v1.endpoints import (
    alerts,
    auth,
    exchange_accounts,
    exchange_connections,
    health,
    notification_preferences,
    portfolios,
    users,
    watchlists,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(portfolios.router)
api_router.include_router(watchlists.router)
api_router.include_router(alerts.router)
api_router.include_router(notification_preferences.router)
api_router.include_router(exchange_accounts.router)
api_router.include_router(exchange_connections.router)