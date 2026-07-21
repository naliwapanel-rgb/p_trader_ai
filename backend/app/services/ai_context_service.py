import time
from collections.abc import (
    Callable,
)
from typing import Any
from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.notification_preference_repository import (
    NotificationPreferenceRepository,
)
from app.schemas.ai_context import (
    AIAutomationContext,
    AIContextRequest,
    AIPortfolioSnapshotContext,
    AIUserContextResponse,
)
from app.schemas.alert import (
    AlertResponse,
)
from app.schemas.exchange_account import (
    ExchangeAccountResponse,
)
from app.schemas.notification_preference import (
    NotificationPreferenceResponse,
)
from app.schemas.portfolio import (
    PortfolioResponse,
)
from app.schemas.portfolio_sync import (
    PortfolioSyncSnapshotResponse,
)
from app.schemas.watchlist import (
    WatchlistResponse,
)
from app.services.alert_service import (
    AlertService,
)
from app.services.automation_runtime_service import (
    AutomationRuntime,
)
from app.services.exchange_account_service import (
    ExchangeAccountService,
)
from app.services.portfolio_service import (
    PortfolioService,
)
from app.services.portfolio_sync_service import (
    PortfolioSyncService,
)
from app.services.risk_management_registry import (
    get_user_risk_management_service,
)
from app.services.watchlist_service import (
    WatchlistService,
)
class AIContextBuilderService:
    """
    Build read-only AI context using data that belongs
    to the authenticated user.
    Exchange credentials are never included. Sensitive
    keys found inside nested snapshot payloads are removed.
    """
    _SENSITIVE_KEY_PARTS = (
        "api_key",
        "apikey",
        "api_secret",
        "apisecret",
        "secret",
        "password",
        "passphrase",
        "authorization",
        "access_token",
        "refresh_token",
        "signature",
    )
    def __init__(
        self,
        db: Session | None,
        *,
        runtime: AutomationRuntime | None = None,
        portfolio_service: Any | None = None,
        portfolio_sync_service: Any | None = None,
        watchlist_service: Any | None = None,
        alert_service: Any | None = None,
        exchange_account_service: Any | None = None,
        preference_repository: Any | None = None,
        risk_service_getter: (
            Callable[[int], Any] | None
        ) = None,
        clock_ms: Callable[[], int] | None = None,
    ):
        self.runtime = runtime
        self.portfolio_service = (
            portfolio_service
            or PortfolioService(db)
        )
        self.portfolio_sync_service = (
            portfolio_sync_service
            or PortfolioSyncService(db)
        )
        self.watchlist_service = (
            watchlist_service
            or WatchlistService(db)
        )
        self.alert_service = (
            alert_service
            or AlertService(db)
        )
        self.exchange_account_service = (
            exchange_account_service
            or ExchangeAccountService(db)
        )
        self.preference_repository = (
            preference_repository
            or NotificationPreferenceRepository(db)
        )
        self.risk_service_getter = (
            risk_service_getter
            or get_user_risk_management_service
        )
        self.clock_ms = (
            clock_ms
            or (
                lambda:
                int(time.time() * 1000)
            )
        )
    @classmethod
    def _is_sensitive_key(
        cls,
        key: Any,
    ) -> bool:
        normalized = (
            str(key)
            .strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )
        return any(
            part in normalized
            for part in cls._SENSITIVE_KEY_PARTS
        )
    @classmethod
    def _scrub_sensitive_data(
        cls,
        value: Any,
    ) -> Any:
        if isinstance(value, dict):
            return {
                str(key): cls._scrub_sensitive_data(
                    item
                )
                for key, item in value.items()
                if not cls._is_sensitive_key(key)
            }
        if isinstance(value, list):
            return [
                cls._scrub_sensitive_data(item)
                for item in value
            ]
        if isinstance(value, tuple):
            return [
                cls._scrub_sensitive_data(item)
                for item in value
            ]
        return value
    @classmethod
    def _snapshot_context(
        cls,
        snapshot: Any,
    ) -> AIPortfolioSnapshotContext:
        validated = (
            PortfolioSyncSnapshotResponse
            .model_validate(snapshot)
        )
        return AIPortfolioSnapshotContext(
            id=validated.id,
            user_id=validated.user_id,
            portfolio_id=(
                validated.portfolio_id
            ),
            exchange_account_id=(
                validated.exchange_account_id
            ),
            exchange_name=(
                validated.exchange_name
            ),
            account_type=(
                validated.account_type
            ),
            category=validated.category,
            settle_coin=(
                validated.settle_coin
            ),
            status=validated.status,
            total_equity_usd=(
                validated.total_equity_usd
            ),
            total_wallet_balance_usd=(
                validated
                .total_wallet_balance_usd
            ),
            total_available_balance_usd=(
                validated
                .total_available_balance_usd
            ),
            total_unrealized_pnl_usd=(
                validated
                .total_unrealized_pnl_usd
            ),
            total_realized_pnl_usd=(
                validated
                .total_realized_pnl_usd
            ),
            total_position_value_usd=(
                validated
                .total_position_value_usd
            ),
            coin_count=validated.coin_count,
            open_position_count=(
                validated.open_position_count
            ),
            open_order_count=(
                validated.open_order_count
            ),
            balance_payload=(
                cls._scrub_sensitive_data(
                    validated.balance_payload
                )
            ),
            positions_payload=(
                cls._scrub_sensitive_data(
                    validated.positions_payload
                )
            ),
            orders_payload=(
                cls._scrub_sensitive_data(
                    validated.orders_payload
                )
            ),
            error_message=(
                validated.error_message
            ),
            synced_at=validated.synced_at,
            created_at=validated.created_at,
        )
    def _automation_context(
        self,
    ) -> AIAutomationContext | None:
        if self.runtime is None:
            return None
        health = self.runtime.health()
        return AIAutomationContext(
            available=True,
            healthy=health.healthy,
            started=health.started,
            handlers_registered=(
                health.handlers_registered
            ),
            worker_running=(
                health.worker.running
            ),
            accepting_jobs=(
                health.worker.accepting_jobs
            ),
        )
    def build(
        self,
        *,
        current_user: User,
        request: AIContextRequest,
    ) -> AIUserContextResponse:
        portfolios_raw = (
            self.portfolio_service
            .list_portfolios(
                current_user=current_user
            )
        )
        watchlist_raw = (
            self.watchlist_service
            .list_items(
                current_user=current_user
            )
        )
        alerts_raw = (
            self.alert_service
            .list_alerts(
                current_user=current_user
            )
        )
        accounts_raw = (
            self.exchange_account_service
            .list_accounts(
                current_user=current_user
            )
        )
        portfolios = [
            PortfolioResponse.model_validate(
                item
            )
            for item in portfolios_raw
        ]
        watchlist = [
            WatchlistResponse.model_validate(
                item
            )
            for item in watchlist_raw
        ]
        alerts = [
            AlertResponse.model_validate(
                item
            )
            for item in alerts_raw
        ]
        accounts = [
            ExchangeAccountResponse
            .model_validate(item)
            for item in accounts_raw
        ]
        selected_portfolio = None
        if request.portfolio_id is not None:
            selected_portfolio = (
                PortfolioResponse
                .model_validate(
                    self.portfolio_service
                    .get_portfolio(
                        current_user=(
                            current_user
                        ),
                        portfolio_id=(
                            request.portfolio_id
                        ),
                    )
                )
            )
        selected_account = None
        if (
            request.exchange_account_id
            is not None
        ):
            selected_account = (
                ExchangeAccountResponse
                .model_validate(
                    self
                    .exchange_account_service
                    .get_account(
                        current_user=(
                            current_user
                        ),
                        account_id=(
                            request
                            .exchange_account_id
                        ),
                    )
                )
            )
        latest_snapshot = None
        if request.portfolio_id is not None:
            try:
                snapshot = (
                    self
                    .portfolio_sync_service
                    .get_latest_snapshot(
                        current_user=(
                            current_user
                        ),
                        portfolio_id=(
                            request.portfolio_id
                        ),
                        exchange_account_id=(
                            request
                            .exchange_account_id
                        ),
                    )
                )
            except HTTPException as exc:
                expected_missing_snapshot = (
                    exc.status_code
                    == status.HTTP_404_NOT_FOUND
                    and exc.detail
                    == (
                        "Portfolio synchronization "
                        "snapshot not found"
                    )
                )
                if not expected_missing_snapshot:
                    raise
            else:
                latest_snapshot = (
                    self._snapshot_context(
                        snapshot
                    )
                )
        preference = (
            self.preference_repository
            .get_by_user_id(
                current_user.id
            )
        )
        notification_preferences = None
        if preference is not None:
            notification_preferences = (
                NotificationPreferenceResponse
                .model_validate(preference)
            )
        risk_service = (
            self.risk_service_getter(
                current_user.id
            )
        )
        risk_configuration = (
            risk_service.get_configuration()
        )
        automation = None
        if request.include_automation:
            automation = (
                self._automation_context()
            )
        data_sources = [
            "RISK_ENGINE",
        ]
        if portfolios or latest_snapshot:
            data_sources.append(
                "PORTFOLIO"
            )
        if watchlist:
            data_sources.append(
                "WATCHLIST"
            )
        if alerts:
            data_sources.append(
                "ALERTS"
            )
        if accounts:
            data_sources.append(
                "EXCHANGE_ACCOUNTS"
            )
        if notification_preferences:
            data_sources.append(
                "NOTIFICATION_PREFERENCES"
            )
        if automation is not None:
            data_sources.append(
                "AUTOMATION_RUNTIME"
            )
        return AIUserContextResponse(
            user_id=current_user.id,
            generated_at_ms=self.clock_ms(),
            portfolios=portfolios,
            selected_portfolio=(
                selected_portfolio
            ),
            latest_portfolio_snapshot=(
                latest_snapshot
            ),
            watchlist=watchlist,
            alerts=alerts,
            exchange_accounts=accounts,
            selected_exchange_account=(
                selected_account
            ),
            notification_preferences=(
                notification_preferences
            ),
            risk_configuration=(
                risk_configuration
            ),
            automation=automation,
            data_sources=data_sources,
            portfolio_count=len(portfolios),
            watchlist_count=len(watchlist),
            alert_count=len(alerts),
            exchange_account_count=(
                len(accounts)
            ),
            advisory_only=True,
            execution_enabled=False,
        )
