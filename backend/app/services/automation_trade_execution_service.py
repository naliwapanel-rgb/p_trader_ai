from collections.abc import Callable
from typing import Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.repositories.user_repository import (
    UserRepository,
)
from app.schemas.automation_trade import (
    AutomatedLimitOrderJob,
    AutomatedMarketOrderJob,
    AutomatedTradeExecutionResult,
)
from app.services.exchange_trading_service import (
    ExchangeTradingService,
)
from app.workers.automation_worker import (
    AutomationWorker,
)
SessionFactory = Callable[[], Session]
UserRepositoryFactory = Callable[
    [Session],
    UserRepository,
]
TradingServiceFactory = Callable[
    [Session],
    ExchangeTradingService,
]
class AutomatedTradeExecutionService:
    MARKET_ORDER_JOB_TYPE = (
        "TRADE_MARKET_ORDER"
    )
    LIMIT_ORDER_JOB_TYPE = (
        "TRADE_LIMIT_ORDER"
    )
    def __init__(
        self,
        *,
        session_factory: (
            SessionFactory | None
        ) = None,
        user_repository_factory: (
            UserRepositoryFactory | None
        ) = None,
        trading_service_factory: (
            TradingServiceFactory | None
        ) = None,
    ):
        self.session_factory = (
            session_factory
            or SessionLocal
        )
        self.user_repository_factory = (
            user_repository_factory
            or UserRepository
        )
        self.trading_service_factory = (
            trading_service_factory
            or ExchangeTradingService
        )
    def _get_active_user(
        self,
        *,
        db: Session,
        user_id: int,
    ):
        repository = (
            self.user_repository_factory(db)
        )
        user = repository.get_by_id(
            user_id
        )
        if user is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Automation trade user "
                    "was not found"
                ),
            )
        if not user.is_active:
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Automation trade user "
                    "is inactive"
                ),
            )
        return user
    @staticmethod
    def _rollback_safely(
        db: Session,
    ) -> None:
        rollback = getattr(
            db,
            "rollback",
            None,
        )
        if callable(rollback):
            rollback()
    @staticmethod
    def _close_safely(
        db: Session,
    ) -> None:
        close = getattr(
            db,
            "close",
            None,
        )
        if callable(close):
            close()
    async def execute_market_order(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        data = (
            AutomatedMarketOrderJob
            .model_validate(payload)
        )
        db = self.session_factory()
        try:
            user = self._get_active_user(
                db=db,
                user_id=data.user_id,
            )
            trading_service = (
                self.trading_service_factory(
                    db
                )
            )
            exchange_result = (
                await trading_service
                .place_market_order(
                    current_user=user,
                    account_id=(
                        data.account_id
                    ),
                    data=data.order,
                )
            )
            result = (
                AutomatedTradeExecutionResult(
                    execution_type=(
                        "MARKET_ORDER"
                    ),
                    user_id=data.user_id,
                    account_id=(
                        data.account_id
                    ),
                    symbol=data.order.symbol,
                    side=data.order.side,
                    exchange_result=(
                        exchange_result
                    ),
                )
            )
            return result.model_dump(
                mode="json"
            )
        except Exception:
            self._rollback_safely(db)
            raise
        finally:
            self._close_safely(db)
    async def execute_limit_order(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        data = (
            AutomatedLimitOrderJob
            .model_validate(payload)
        )
        db = self.session_factory()
        try:
            user = self._get_active_user(
                db=db,
                user_id=data.user_id,
            )
            trading_service = (
                self.trading_service_factory(
                    db
                )
            )
            exchange_result = (
                await trading_service
                .place_limit_order(
                    current_user=user,
                    account_id=(
                        data.account_id
                    ),
                    data=data.order,
                )
            )
            result = (
                AutomatedTradeExecutionResult(
                    execution_type=(
                        "LIMIT_ORDER"
                    ),
                    user_id=data.user_id,
                    account_id=(
                        data.account_id
                    ),
                    symbol=data.order.symbol,
                    side=data.order.side,
                    exchange_result=(
                        exchange_result
                    ),
                )
            )
            return result.model_dump(
                mode="json"
            )
        except Exception:
            self._rollback_safely(db)
            raise
        finally:
            self._close_safely(db)
    def register_handlers(
        self,
        worker: AutomationWorker,
    ) -> None:
        required_job_types = {
            self.MARKET_ORDER_JOB_TYPE,
            self.LIMIT_ORDER_JOB_TYPE,
        }
        registered_job_types = set(
            worker
            .snapshot()
            .registered_job_types
        )
        duplicates = (
            required_job_types
            & registered_job_types
        )
        if duplicates:
            duplicate_text = ", ".join(
                sorted(duplicates)
            )
            raise ValueError(
                "Automated trade handlers "
                "are already registered: "
                f"{duplicate_text}"
            )
        worker.register_handler(
            self.MARKET_ORDER_JOB_TYPE,
            self.execute_market_order,
        )
        worker.register_handler(
            self.LIMIT_ORDER_JOB_TYPE,
            self.execute_limit_order,
        )
