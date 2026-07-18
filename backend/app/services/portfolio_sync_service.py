import asyncio
import hashlib
import json
from collections.abc import Callable
from typing import Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.exchanges.factory import ExchangeFactory
from app.models.user import User
from app.repositories.portfolio_repository import (
    PortfolioRepository,
)
from app.repositories.portfolio_sync_repository import (
    PortfolioSyncRepository,
)
from app.schemas.portfolio_sync import (
    PortfolioSyncExecutionResult,
    PortfolioSyncSnapshotCreate,
    PortfolioSyncSnapshotResponse,
)
from app.services.exchange_account_service import (
    ExchangeAccountService,
)
from app.services.portfolio_service import (
    PortfolioService,
)
class PortfolioSyncService:
    def __init__(
        self,
        db: Session,
        client_factory: Callable | None = None,
    ):
        self.db = db
        self.portfolio_service = PortfolioService(db)
        self.exchange_account_service = (
            ExchangeAccountService(db)
        )
        self.portfolio_repository = (
            PortfolioRepository(db)
        )
        self.sync_repository = (
            PortfolioSyncRepository(db)
        )
        self.client_factory = (
            client_factory
            or ExchangeFactory.create_client
        )
    @staticmethod
    def _to_float(
        value: Any,
    ) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0
    @staticmethod
    def _error_text(
        error: BaseException,
    ) -> str:
        if isinstance(error, HTTPException):
            return str(error.detail)
        message = str(error).strip()
        if message:
            return message
        return error.__class__.__name__
    @classmethod
    def _canonicalize(
        cls,
        value: Any,
    ) -> Any:
        if isinstance(value, dict):
            return {
                key: cls._canonicalize(value[key])
                for key in sorted(value)
            }
        if isinstance(value, list):
            normalized = [
                cls._canonicalize(item)
                for item in value
            ]
            return sorted(
                normalized,
                key=lambda item: json.dumps(
                    item,
                    sort_keys=True,
                    separators=(",", ":"),
                    default=str,
                ),
            )
        return value
    @classmethod
    def build_fingerprint(
        cls,
        payload: dict,
    ) -> str:
        canonical_payload = cls._canonicalize(
            payload
        )
        serialized = json.dumps(
            canonical_payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return hashlib.sha256(
            serialized.encode("utf-8")
        ).hexdigest()
    @classmethod
    def _validate_mapping_result(
        cls,
        source: str,
        result: Any,
    ) -> tuple[dict, str | None]:
        if isinstance(result, BaseException):
            return {}, cls._error_text(result)
        if not isinstance(result, dict):
            return (
                {},
                (
                    f"{source} returned an invalid "
                    "response"
                ),
            )
        return result, None
    @classmethod
    def _extract_collection(
        cls,
        source: str,
        result: Any,
        primary_key: str,
        alternative_key: str | None = None,
    ) -> tuple[dict, list[dict], str | None]:
        container, error = (
            cls._validate_mapping_result(
                source=source,
                result=result,
            )
        )
        if error is not None:
            return {}, [], error
        items = container.get(primary_key)
        if (
            items is None
            and alternative_key is not None
        ):
            items = container.get(
                alternative_key
            )
        if items is None:
            items = []
        if not isinstance(items, list):
            return (
                container,
                [],
                (
                    f"{source} returned an invalid "
                    "collection"
                ),
            )
        valid_items = [
            item
            for item in items
            if isinstance(item, dict)
        ]
        if len(valid_items) != len(items):
            return (
                container,
                valid_items,
                (
                    f"{source} contained invalid "
                    "collection items"
                ),
            )
        return container, valid_items, None
    @staticmethod
    def _sync_status(
        source_errors: dict[str, str],
    ) -> str:
        error_count = len(source_errors)
        if error_count == 0:
            return "SUCCESS"
        if error_count == 3:
            return "FAILED"
        return "PARTIAL"
    async def synchronize(
        self,
        current_user: User,
        portfolio_id: int,
        exchange_account_id: int,
        category: str = "linear",
        settle_coin: str = "USDT",
    ) -> PortfolioSyncExecutionResult:
        portfolio = (
            self.portfolio_service.get_portfolio(
                current_user=current_user,
                portfolio_id=portfolio_id,
            )
        )
        account = (
            self.exchange_account_service
            .get_account(
                current_user=current_user,
                account_id=exchange_account_id,
            )
        )
        if not account.is_active:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail="Exchange account is inactive",
            )
        normalized_category = (
            category.strip().lower()
        )
        normalized_settle_coin = (
            settle_coin.strip().upper()
        )
        client = self.client_factory(account)
        results = await asyncio.gather(
            client.get_account_balance(),
            client.get_positions(
                category=normalized_category,
                settle_coin=(
                    normalized_settle_coin
                ),
            ),
            client.get_open_orders(
                category=normalized_category,
                settle_coin=(
                    normalized_settle_coin
                ),
            ),
            return_exceptions=True,
        )
        balance_result = results[0]
        positions_result = results[1]
        orders_result = results[2]
        source_errors: dict[str, str] = {}
        balance_payload, balance_error = (
            self._validate_mapping_result(
                source="balance",
                result=balance_result,
            )
        )
        if balance_error is not None:
            source_errors["balance"] = (
                balance_error
            )
        (
            positions_container,
            positions_payload,
            positions_error,
        ) = self._extract_collection(
            source="positions",
            result=positions_result,
            primary_key="positions",
        )
        if positions_error is not None:
            source_errors["positions"] = (
                positions_error
            )
        (
            orders_container,
            orders_payload,
            orders_error,
        ) = self._extract_collection(
            source="orders",
            result=orders_result,
            primary_key="orders",
            alternative_key="open_orders",
        )
        if orders_error is not None:
            source_errors["orders"] = (
                orders_error
            )
        total_equity = self._to_float(
            balance_payload.get(
                "total_equity_usd"
            )
        )
        total_wallet_balance = self._to_float(
            balance_payload.get(
                "total_wallet_balance_usd"
            )
        )
        total_available_balance = (
            self._to_float(
                balance_payload.get(
                    "total_available_balance_usd"
                )
            )
        )
        position_unrealized_pnl = sum(
            self._to_float(
                position.get("unrealized_pnl")
            )
            for position in positions_payload
        )
        if "balance" in source_errors:
            total_unrealized_pnl = (
                position_unrealized_pnl
            )
        else:
            total_unrealized_pnl = (
                self._to_float(
                    balance_payload.get(
                        "total_unrealized_pnl_usd"
                    )
                )
            )
        total_realized_pnl = sum(
            self._to_float(
                position.get("realized_pnl")
            )
            for position in positions_payload
        )
        total_position_value = sum(
            self._to_float(
                position.get("position_value")
            )
            for position in positions_payload
        )
        coins = balance_payload.get(
            "coins",
            [],
        )
        if not isinstance(coins, list):
            coins = []
            source_errors.setdefault(
                "balance",
                (
                    "balance returned an invalid "
                    "coin collection"
                ),
            )
        sync_status = self._sync_status(
            source_errors
        )
        fingerprint_payload = {
            "portfolio_id": portfolio.id,
            "exchange_account_id": account.id,
            "exchange_name": (
                account.exchange_name.upper()
            ),
            "category": normalized_category,
            "settle_coin": (
                normalized_settle_coin
            ),
            "status": sync_status,
            "balance": balance_payload,
            "positions": positions_payload,
            "orders": orders_payload,
            "errors": source_errors,
        }
        fingerprint = self.build_fingerprint(
            fingerprint_payload
        )
        error_message = None
        if source_errors:
            error_message = "; ".join(
                (
                    f"{source}: "
                    f"{source_errors[source]}"
                )
                for source in sorted(
                    source_errors
                )
            )
        snapshot_data = (
            PortfolioSyncSnapshotCreate(
                user_id=current_user.id,
                portfolio_id=portfolio.id,
                exchange_account_id=account.id,
                exchange_name=(
                    account.exchange_name.upper()
                ),
                account_type=str(
                    balance_payload.get(
                        "account_type",
                        "UNIFIED",
                    )
                ).upper(),
                category=normalized_category,
                settle_coin=(
                    normalized_settle_coin
                ),
                status=sync_status,
                fingerprint=fingerprint,
                total_equity_usd=total_equity,
                total_wallet_balance_usd=(
                    total_wallet_balance
                ),
                total_available_balance_usd=(
                    total_available_balance
                ),
                total_unrealized_pnl_usd=(
                    total_unrealized_pnl
                ),
                total_realized_pnl_usd=(
                    total_realized_pnl
                ),
                total_position_value_usd=(
                    total_position_value
                ),
                coin_count=len(coins),
                open_position_count=len(
                    positions_payload
                ),
                open_order_count=len(
                    orders_payload
                ),
                balance_payload=(
                    balance_payload
                ),
                positions_payload=(
                    positions_payload
                ),
                orders_payload=orders_payload,
                error_message=error_message,
            )
        )
        snapshot, created = (
            self.sync_repository.create_or_get(
                snapshot_data
            )
        )
        if "balance" not in source_errors:
            portfolio = (
                self.portfolio_repository.update(
                    portfolio=portfolio,
                    total_value=total_equity,
                    profit_loss=(
                        total_realized_pnl
                        + total_unrealized_pnl
                    ),
                )
            )
        return PortfolioSyncExecutionResult(
            snapshot=(
                PortfolioSyncSnapshotResponse
                .model_validate(snapshot)
            ),
            created=created,
            portfolio_total_value=self._to_float(
                portfolio.total_value
            ),
            portfolio_profit_loss=self._to_float(
                portfolio.profit_loss
            ),
            source_errors=source_errors,
        )
    def get_latest_snapshot(
        self,
        current_user: User,
        portfolio_id: int,
        exchange_account_id: int | None = None,
    ):
        self.portfolio_service.get_portfolio(
            current_user=current_user,
            portfolio_id=portfolio_id,
        )
        if exchange_account_id is not None:
            self.exchange_account_service.get_account(
                current_user=current_user,
                account_id=exchange_account_id,
            )
        snapshot = self.sync_repository.get_latest(
            user_id=current_user.id,
            portfolio_id=portfolio_id,
            exchange_account_id=(
                exchange_account_id
            ),
        )
        if snapshot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "Portfolio synchronization "
                    "snapshot not found"
                ),
            )
        return snapshot
    def list_snapshots(
        self,
        current_user: User,
        portfolio_id: int,
        limit: int = 50,
    ):
        self.portfolio_service.get_portfolio(
            current_user=current_user,
            portfolio_id=portfolio_id,
        )
        return self.sync_repository.list_by_portfolio(
            user_id=current_user.id,
            portfolio_id=portfolio_id,
            limit=limit,
        )
    def get_snapshot(
        self,
        current_user: User,
        portfolio_id: int,
        snapshot_id: int,
    ):
        self.portfolio_service.get_portfolio(
            current_user=current_user,
            portfolio_id=portfolio_id,
        )
        snapshot = (
            self.sync_repository.get_by_id_and_user(
                snapshot_id=snapshot_id,
                user_id=current_user.id,
            )
        )
        if (
            snapshot is None
            or snapshot.portfolio_id
            != portfolio_id
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "Portfolio synchronization "
                    "snapshot not found"
                ),
            )
        return snapshot
