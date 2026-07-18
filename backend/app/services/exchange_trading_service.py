from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.exchanges.factory import ExchangeFactory
from app.models.user import User
from app.schemas.exchange_trade import (
    AmendOrderRequest,
    CancelOrderRequest,
    LimitOrderRequest,
    MarketOrderRequest,
)
from app.schemas.risk_management import (
    PositionSizeResult,
    PreTradeRiskRequest,
    PreTradeRiskResult,
)
from app.services.exchange_account_service import (
    ExchangeAccountService,
)
from app.services.risk_management_registry import (
    get_user_risk_management_service,
)
class ExchangeTradingService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.exchange_account_service = (
            ExchangeAccountService(db)
        )
    def _get_client(
        self,
        current_user: User,
        account_id: int,
    ):
        account = (
            self.exchange_account_service.get_account(
                current_user=current_user,
                account_id=account_id,
            )
        )
        if not account.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exchange account is inactive",
            )
        return ExchangeFactory.create_client(account)
    def _validate_quantity(
        self,
        quantity: float,
    ) -> None:
        if quantity > self.settings.max_order_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Order quantity exceeds configured "
                    "safety limit of "
                    f"{self.settings.max_order_quantity}"
                ),
            )
    @staticmethod
    def _build_position_size_result(
        data: MarketOrderRequest | LimitOrderRequest,
        entry_price: float,
    ) -> PositionSizeResult:
        risk_context = data.risk_context
        if risk_context is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "risk_context is required for "
                    "opening orders"
                ),
            )
        stop_distance = abs(
            entry_price
            - risk_context.stop_loss_price
        )
        risk_amount = (
            data.quantity * stop_distance
        )
        risk_percent = (
            risk_amount
            / risk_context.account_equity
            * 100
        )
        position_notional = (
            data.quantity * entry_price
        )
        required_margin = (
            position_notional
            / risk_context.requested_leverage
        )
        return PositionSizeResult(
            valid=True,
            account_equity=(
                risk_context.account_equity
            ),
            requested_risk_percent=risk_percent,
            requested_risk_amount=risk_amount,
            entry_price=entry_price,
            stop_loss_price=(
                risk_context.stop_loss_price
            ),
            stop_distance=stop_distance,
            raw_quantity=data.quantity,
            rounded_quantity=data.quantity,
            position_notional=position_notional,
            required_margin=required_margin,
            actual_risk_amount=risk_amount,
            actual_risk_percent=risk_percent,
            quantity_step=0,
            minimum_quantity=0,
            maximum_quantity=data.quantity,
            minimum_notional=0,
            leverage=(
                risk_context.requested_leverage
            ),
            capped_by_maximum_quantity=False,
            rejection_reasons=[],
        )
    def _validate_opening_order_risk(
        self,
        current_user: User,
        data: MarketOrderRequest | LimitOrderRequest,
        entry_price: float,
    ) -> PreTradeRiskResult | None:
        if data.reduce_only:
            return None
        risk_context = data.risk_context
        if risk_context is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "risk_context is required for "
                    "opening orders"
                ),
            )
        position_size = (
            self._build_position_size_result(
                data=data,
                entry_price=entry_price,
            )
        )
        try:
            request = PreTradeRiskRequest(
                side=data.side,
                account_equity=(
                    risk_context.account_equity
                ),
                requested_leverage=(
                    risk_context.requested_leverage
                ),
                current_open_positions=(
                    risk_context
                    .current_open_positions
                ),
                current_total_exposure_percent=(
                    risk_context
                    .current_total_exposure_percent
                ),
                current_daily_loss_percent=(
                    risk_context
                    .current_daily_loss_percent
                ),
                current_drawdown_percent=(
                    risk_context
                    .current_drawdown_percent
                ),
                entry_price=entry_price,
                stop_loss_price=(
                    risk_context.stop_loss_price
                ),
                take_profit_price=(
                    risk_context.take_profit_price
                ),
                position_size=position_size,
            )
        except ValidationError as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail={
                    "message": (
                        "Invalid order risk context"
                    ),
                    "errors": exc.errors(
                        include_url=False
                    ),
                },
            ) from exc
        risk_service = (
            get_user_risk_management_service(
                current_user.id
            )
        )
        result = risk_service.validate_pre_trade(
            request
        )
        if not result.accepted:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail={
                    "message": (
                        "Order rejected by risk "
                        "management"
                    ),
                    "risk_validation": (
                        result.model_dump()
                    ),
                },
            )
        return result
    @staticmethod
    def _attach_risk_validation(
        result: dict,
        risk_result: PreTradeRiskResult | None,
    ) -> dict:
        if risk_result is None:
            return result
        enriched_result = dict(result)
        enriched_result["risk_validation"] = (
            risk_result.model_dump()
        )
        return enriched_result
    async def cancel_order(
        self,
        current_user: User,
        account_id: int,
        data: CancelOrderRequest,
    ) -> dict:
        client = self._get_client(
            current_user=current_user,
            account_id=account_id,
        )
        return await client.cancel_order(
            symbol=data.symbol,
            order_id=data.order_id,
            client_order_id=data.client_order_id,
            category=data.category,
            dry_run=(
                self.settings.exchange_dry_run
                or not (
                    self.settings
                    .exchange_trading_enabled
                )
            ),
        )
    async def amend_order(
        self,
        current_user: User,
        account_id: int,
        data: AmendOrderRequest,
    ) -> dict:
        if data.quantity is not None:
            self._validate_quantity(data.quantity)
        client = self._get_client(
            current_user=current_user,
            account_id=account_id,
        )
        return await client.amend_order(
            symbol=data.symbol,
            order_id=data.order_id,
            client_order_id=data.client_order_id,
            quantity=data.quantity,
            price=data.price,
            trigger_price=data.trigger_price,
            take_profit=data.take_profit,
            stop_loss=data.stop_loss,
            category=data.category,
            dry_run=(
                self.settings.exchange_dry_run
                or not (
                    self.settings
                    .exchange_trading_enabled
                )
            ),
        )
    async def place_market_order(
        self,
        current_user: User,
        account_id: int,
        data: MarketOrderRequest,
    ) -> dict:
        self._validate_quantity(data.quantity)
        if data.reduce_only:
            entry_price = 0
        else:
            risk_context = data.risk_context
            if (
                risk_context is None
                or (
                    risk_context
                    .estimated_entry_price is None
                )
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "estimated_entry_price and "
                        "risk_context are required for "
                        "opening market orders"
                    ),
                )
            entry_price = (
                risk_context.estimated_entry_price
            )
        risk_result = (
            self._validate_opening_order_risk(
                current_user=current_user,
                data=data,
                entry_price=entry_price,
            )
        )
        client = self._get_client(
            current_user=current_user,
            account_id=account_id,
        )
        result = await client.place_market_order(
            symbol=data.symbol,
            side=data.side,
            quantity=data.quantity,
            category=data.category,
            time_in_force=data.time_in_force,
            reduce_only=data.reduce_only,
            close_on_trigger=data.close_on_trigger,
            client_order_id=data.client_order_id,
            dry_run=(
                self.settings.exchange_dry_run
                or not (
                    self.settings
                    .exchange_trading_enabled
                )
            ),
        )
        return self._attach_risk_validation(
            result=result,
            risk_result=risk_result,
        )
    async def place_limit_order(
        self,
        current_user: User,
        account_id: int,
        data: LimitOrderRequest,
    ) -> dict:
        self._validate_quantity(data.quantity)
        estimated_value = data.quantity * data.price
        if (
            estimated_value
            > self.settings.max_order_value_usd
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Estimated order value exceeds "
                    "configured safety limit of "
                    f"{self.settings.max_order_value_usd} "
                    "USD"
                ),
            )
        risk_result = (
            self._validate_opening_order_risk(
                current_user=current_user,
                data=data,
                entry_price=data.price,
            )
        )
        client = self._get_client(
            current_user=current_user,
            account_id=account_id,
        )
        result = await client.place_limit_order(
            symbol=data.symbol,
            side=data.side,
            quantity=data.quantity,
            price=data.price,
            category=data.category,
            time_in_force=data.time_in_force,
            reduce_only=data.reduce_only,
            close_on_trigger=data.close_on_trigger,
            client_order_id=data.client_order_id,
            dry_run=(
                self.settings.exchange_dry_run
                or not (
                    self.settings
                    .exchange_trading_enabled
                )
            ),
        )
        return self._attach_risk_validation(
            result=result,
            risk_result=risk_result,
        )
