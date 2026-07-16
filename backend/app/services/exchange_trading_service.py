from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.exchanges.factory import ExchangeFactory
from app.models.user import User
from app.schemas.exchange_trade import (
    AmendOrderRequest,
    CancelOrderRequest,
    LimitOrderRequest,
    MarketOrderRequest,
    StopLimitOrderRequest,
    StopMarketOrderRequest,
)

from app.services.exchange_account_service import ExchangeAccountService


class ExchangeTradingService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.exchange_account_service = ExchangeAccountService(db)

    def _get_client(
        self,
        current_user: User,
        account_id: int,
    ):
        account = self.exchange_account_service.get_account(
            current_user=current_user,
            account_id=account_id,
        )

        if not account.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exchange account is inactive",
            )

        return ExchangeFactory.create_client(account)

    def _validate_quantity(self, quantity: float) -> None:
        if quantity > self.settings.max_order_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Order quantity exceeds configured safety limit "
                    f"of {self.settings.max_order_quantity}"
                ),
            )
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
                or not self.settings.exchange_trading_enabled
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
                or not self.settings.exchange_trading_enabled
            ),
        )
    async def place_market_order(
        self,
        current_user: User,
        account_id: int,
        data: MarketOrderRequest,
    ) -> dict:
        self._validate_quantity(data.quantity)

        client = self._get_client(
            current_user=current_user,
            account_id=account_id,
        )

        return await client.place_market_order(
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
                or not self.settings.exchange_trading_enabled
            ),
        )

    async def place_limit_order(
        self,
        current_user: User,
        account_id: int,
        data: LimitOrderRequest,
    ) -> dict:
        self._validate_quantity(data.quantity)

        estimated_value = data.quantity * data.price

        if estimated_value > self.settings.max_order_value_usd:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Estimated order value exceeds configured safety limit "
                    f"of {self.settings.max_order_value_usd} USD"
                ),
            )

        client = self._get_client(
            current_user=current_user,
            account_id=account_id,
        )

        return await client.place_limit_order(
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
                or not self.settings.exchange_trading_enabled
            ),
        )
    
    async def place_stop_limit_order(
        self,
        current_user: User,
        account_id: int,
        data: StopLimitOrderRequest,
    ) -> dict:
        self._validate_quantity(data.quantity)

        client = self._get_client(
            current_user=current_user,
            account_id=account_id,
        )

        return await client.place_stop_limit_order(
            symbol=data.symbol,
            side=data.side,
            quantity=data.quantity,
            price=data.price,
            trigger_price=data.trigger_price,
            trigger_direction=data.trigger_direction,
            trigger_by=data.trigger_by,
            category=data.category,
            time_in_force=data.time_in_force,
            reduce_only=data.reduce_only,
            close_on_trigger=data.close_on_trigger,
            position_index=data.position_index,
            client_order_id=data.client_order_id,
            dry_run=(
                self.settings.exchange_dry_run
                or not self.settings.exchange_trading_enabled
            ),
        )