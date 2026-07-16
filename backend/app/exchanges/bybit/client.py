import json
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status

from app.schemas.exchange_trade import ExchangeOrderPlacement
from app.exchanges.base import BaseExchangeClient
from app.exchanges.bybit.auth import BybitAuth
from app.exchanges.utils import to_float
from app.schemas.exchange_balance import (
    ExchangeBalance,
    ExchangeCoinBalance,
)
from app.exchanges.bybit.errors import get_bybit_error
from app.exchanges.exceptions import ExchangeAPIException
from app.schemas.exchange_trade import (
    ExchangeOrderActionResult,
    ExchangeOrderExecution,
    ExchangeOrderPlacement,
)
from app.schemas.exchange_trade import (
    ExchangeOrderActionResult,
    ExchangeOrderPlacement,
)
from app.schemas.exchange_position import (
    ExchangePosition,
    ExchangePositionList,
)
from decimal import Decimal

from app.exchanges.decimal_utils import (
    decimal_to_plain_string,
    is_step_aligned,
    to_decimal,
)
from app.schemas.exchange_instrument import ExchangeInstrumentRules
from app.schemas.exchange_order import (
    ExchangeOrder,
    ExchangeOrderList,
)

class BybitClient(BaseExchangeClient):
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        is_testnet: bool = False,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.is_testnet = is_testnet

        self.base_url = (
            "https://api-testnet.bybit.com"
            if is_testnet
            else "https://api.bybit.com"
        )

        self.auth = BybitAuth(
            api_key=api_key,
            api_secret=api_secret,
        )
    @staticmethod
    def _validate_bybit_payload(
        payload: dict,
    ) -> None:
        ret_code = int(payload.get("retCode") or 0)

        if ret_code == 0:
            return

        exchange_message = str(
            payload.get("retMsg") or ""
        )

        error = get_bybit_error(
            code=ret_code,
            exchange_message=exchange_message,
        )

        raise ExchangeAPIException(
            status_code=error.http_status,
            exchange="BYBIT",
            error_code=error.code,
            error_type=error.error_type,
            message=error.message,
            exchange_message=exchange_message,
        )
    async def _private_get(
        self,
        endpoint: str,
        params: dict[str, str] | None = None,
    ) -> dict:
        request_params = params or {}
        query_string = urlencode(request_params)

        url = f"{self.base_url}{endpoint}"

        if query_string:
            url = f"{url}?{query_string}"

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    url,
                    headers=self.auth.headers(query_string),
                )
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Bybit request timed out",
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Unable to connect to Bybit: {exc}",
            ) from exc

        try:
            payload = response.json()
        except ValueError:
            message = (
                response.text.strip()
                or "Invalid response from Bybit"
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bybit API error: {message}",
            )

        if response.status_code >= 400 and payload.get("retCode") is None:
            raise ExchangeAPIException(
                status_code=response.status_code,
                exchange="BYBIT",
                error_code=response.status_code,
                error_type="HTTP_ERROR",
                message="Bybit returned an HTTP error.",
                exchange_message=response.text.strip(),
            )

        self._validate_bybit_payload(payload)

        return payload
    async def _private_post(
        self,
        endpoint: str,
        body: dict,
    ) -> dict:
        body_string = json.dumps(
            body,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        url = f"{self.base_url}{endpoint}"

        headers = self.auth.headers(body_string)
        headers["Content-Type"] = "application/json"

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    content=body_string,
                )
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Bybit request timed out",
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Unable to connect to Bybit: {exc}",
            ) from exc

        try:
            payload = response.json()
        except ValueError:
            message = response.text.strip() or "Invalid response from Bybit"

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bybit API error: {message}",
            )

        if response.status_code >= 400 and payload.get("retCode") is None:
            raise ExchangeAPIException(
                status_code=response.status_code,
                exchange="BYBIT",
                error_code=response.status_code,
                error_type="HTTP_ERROR",
                message="Bybit returned an HTTP error.",
                exchange_message=response.text.strip(),
            )

        self._validate_bybit_payload(payload)

        return payload

    async def test_connection(self):
        payload = await self._private_get(
            endpoint="/v5/user/query-api",
        )

        result = payload.get("result", {})

        return {
            "exchange": "BYBIT",
            "connected": True,
            "account_type": result.get("type"),
            "read_only": result.get("readOnly"),
            "permissions": result.get("permissions", {}),
            "expires_at": result.get("expiredAt"),
            "is_testnet": self.is_testnet,
        }

    async def get_account_balance(self) -> dict:
        payload = await self._private_get(
            endpoint="/v5/account/wallet-balance",
            params={
                "accountType": "UNIFIED",
            },
        )

        result = payload.get("result", {})
        accounts = result.get("list", [])

        if not accounts:
            return ExchangeBalance(
                exchange="BYBIT",
                account_type="UNIFIED",
            ).model_dump()

        account = accounts[0]

        coins = [
            ExchangeCoinBalance(
                coin=coin_data.get("coin", ""),
                equity=to_float(coin_data.get("equity")),
                wallet_balance=to_float(
                    coin_data.get("walletBalance")
                ),
                available_balance=to_float(
                    coin_data.get("availableToWithdraw")
                    or coin_data.get("availableBalance")
                ),
                locked_balance=to_float(
                    coin_data.get("locked")
                ),
                usd_value=to_float(
                    coin_data.get("usdValue")
                ),
                unrealized_pnl=to_float(
                    coin_data.get("unrealisedPnl")
                ),
            )
            for coin_data in account.get("coin", [])
            if coin_data.get("coin")
        ]

        balance = ExchangeBalance(
            exchange="BYBIT",
            account_type=account.get(
                "accountType",
                "UNIFIED",
            ),
            total_equity_usd=to_float(
                account.get("totalEquity")
            ),
            total_wallet_balance_usd=to_float(
                account.get("totalWalletBalance")
            ),
            total_available_balance_usd=to_float(
                account.get("totalAvailableBalance")
            ),
            total_unrealized_pnl_usd=to_float(
                account.get("totalPerpUPL")
            ),
            coins=coins,
        )

        return balance.model_dump()

    async def get_positions(
        self,
        category: str = "linear",
        settle_coin: str = "USDT",
    ) -> dict:
        normalized_category = category.lower()
        normalized_settle_coin = settle_coin.upper()

        if normalized_category not in {
            "linear",
            "inverse",
            "option",
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported Bybit position category",
            )

        params = {
            "category": normalized_category,
        }

        if normalized_category == "linear":
            params["settleCoin"] = normalized_settle_coin

        payload = await self._private_get(
            endpoint="/v5/position/list",
            params=params,
        )

        result = payload.get("result", {})
        raw_positions = result.get("list", [])

        positions = []

        for position_data in raw_positions:
            size = to_float(position_data.get("size"))

            # Bybit may return an empty position when a symbol is queried.
            # Only active positions should appear in the normalized result.
            if size <= 0:
                continue

            raw_side = position_data.get("side", "")

            if raw_side == "Buy":
                normalized_side = "LONG"
            elif raw_side == "Sell":
                normalized_side = "SHORT"
            else:
                normalized_side = "UNKNOWN"

            position = ExchangePosition(
                exchange="BYBIT",
                category=normalized_category,
                symbol=position_data.get("symbol", ""),
                side=normalized_side,
                size=size,
                position_value=to_float(
                    position_data.get("positionValue")
                ),
                entry_price=to_float(
                    position_data.get("avgPrice")
                ),
                break_even_price=to_float(
                    position_data.get("breakEvenPrice")
                ),
                mark_price=to_float(
                    position_data.get("markPrice")
                ),
                liquidation_price=to_float(
                    position_data.get("liqPrice")
                ),
                leverage=to_float(
                    position_data.get("leverage")
                ),
                unrealized_pnl=to_float(
                    position_data.get("unrealisedPnl")
                ),
                realized_pnl=to_float(
                    position_data.get("curRealisedPnl")
                ),
                cumulative_realized_pnl=to_float(
                    position_data.get("cumRealisedPnl")
                ),
                take_profit=to_float(
                    position_data.get("takeProfit")
                ),
                stop_loss=to_float(
                    position_data.get("stopLoss")
                ),
                trailing_stop=to_float(
                    position_data.get("trailingStop")
                ),
                initial_margin=to_float(
                    position_data.get("positionIM")
                ),
                maintenance_margin=to_float(
                    position_data.get("positionMM")
                ),
                position_status=position_data.get(
                    "positionStatus",
                    "",
                ),
                position_index=int(
                    position_data.get("positionIdx") or 0
                ),
                auto_add_margin=(
                    position_data.get("autoAddMargin") == 1
                ),
                reduce_only=bool(
                    position_data.get("isReduceOnly", False)
                ),
                created_at_ms=int(
                    position_data.get("createdTime") or 0
                ),
                updated_at_ms=int(
                    position_data.get("updatedTime") or 0
                ),
            )

            positions.append(position)

        response = ExchangePositionList(
            exchange="BYBIT",
            category=normalized_category,
            settle_coin=normalized_settle_coin,
            count=len(positions),
            positions=positions,
        )

        return response.model_dump()

    async def get_open_orders(
        self,
        category: str = "linear",
        settle_coin: str = "USDT",
        symbol: str | None = None,
    ) -> dict:
        normalized_category = category.lower()
        normalized_settle_coin = settle_coin.upper()

        supported_categories = {
            "spot",
            "linear",
            "inverse",
            "option",
        }

        if normalized_category not in supported_categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported Bybit order category",
            )

        params = {
            "category": normalized_category,
            "openOnly": "0",
            "limit": "50",
        }

        if symbol:
            params["symbol"] = symbol.upper()
        elif normalized_category == "linear":
            params["settleCoin"] = normalized_settle_coin

        payload = await self._private_get(
            endpoint="/v5/order/realtime",
            params=params,
        )

        result = payload.get("result", {})
        raw_orders = result.get("list", [])

        orders = []

        for order_data in raw_orders:
            raw_side = order_data.get("side", "")

            if raw_side == "Buy":
                normalized_side = "BUY"
            elif raw_side == "Sell":
                normalized_side = "SELL"
            else:
                normalized_side = "UNKNOWN"

            order = ExchangeOrder(
                exchange="BYBIT",
                category=normalized_category,
                order_id=order_data.get("orderId", ""),
                client_order_id=order_data.get(
                    "orderLinkId",
                    "",
                ),
                symbol=order_data.get("symbol", ""),
                side=normalized_side,
                order_type=order_data.get(
                    "orderType",
                    "",
                ).upper(),
                status=order_data.get(
                    "orderStatus",
                    "",
                ).upper(),
                price=to_float(
                    order_data.get("price")
                ),
                average_price=to_float(
                    order_data.get("avgPrice")
                ),
                quantity=to_float(
                    order_data.get("qty")
                ),
                filled_quantity=to_float(
                    order_data.get("cumExecQty")
                ),
                remaining_quantity=to_float(
                    order_data.get("leavesQty")
                ),
                order_value=to_float(
                    order_data.get("leavesValue")
                ),
                cumulative_execution_value=to_float(
                    order_data.get("cumExecValue")
                ),
                cumulative_execution_fee=to_float(
                    order_data.get("cumExecFee")
                ),
                time_in_force=order_data.get(
                    "timeInForce",
                    "",
                ),
                position_index=int(
                    order_data.get("positionIdx") or 0
                ),
                reduce_only=bool(
                    order_data.get("reduceOnly", False)
                ),
                close_on_trigger=bool(
                    order_data.get("closeOnTrigger", False)
                ),
                trigger_price=to_float(
                    order_data.get("triggerPrice")
                ),
                trigger_direction=int(
                    order_data.get("triggerDirection") or 0
                ),
                trigger_by=order_data.get(
                    "triggerBy",
                    "",
                ),
                take_profit=to_float(
                    order_data.get("takeProfit")
                ),
                stop_loss=to_float(
                    order_data.get("stopLoss")
                ),
                order_filter=order_data.get(
                    "orderFilter",
                    "",
                ),
                reject_reason=order_data.get(
                    "rejectReason",
                    "",
                ),
                cancel_type=order_data.get(
                    "cancelType",
                    "",
                ),
                created_at_ms=int(
                    order_data.get("createdTime") or 0
                ),
                updated_at_ms=int(
                    order_data.get("updatedTime") or 0
                ),
            )

            orders.append(order)

        response = ExchangeOrderList(
            exchange="BYBIT",
            category=normalized_category,
            settle_coin=normalized_settle_coin,
            count=len(orders),
            next_cursor=result.get(
                "nextPageCursor",
                "",
            ),
            orders=orders,
        )

        return response.model_dump()
    
    async def get_order_by_id(
        self,
        order_id: str,
        category: str = "linear",
        symbol: str | None = None,
    ) -> dict | None:
        normalized_category = category.lower()

        params = {
            "category": normalized_category,
            "orderId": order_id,
            "openOnly": "0",
            "limit": "1",
        }

        if symbol:
            params["symbol"] = symbol.upper()

        payload = await self._private_get(
            endpoint="/v5/order/realtime",
            params=params,
        )

        result = payload.get("result", {})
        orders = result.get("list", [])

        if not orders:
            return None

        order_data = orders[0]
        raw_side = order_data.get("side", "")

        if raw_side == "Buy":
            normalized_side = "BUY"
        elif raw_side == "Sell":
            normalized_side = "SELL"
        else:
            normalized_side = "UNKNOWN"

        execution = ExchangeOrderExecution(
            exchange="BYBIT",
            category=normalized_category,
            order_id=order_data.get(
                "orderId",
                order_id,
            ),
            client_order_id=order_data.get(
                "orderLinkId",
                "",
            ),
            symbol=order_data.get(
                "symbol",
                symbol.upper() if symbol else "",
            ),
            side=normalized_side,
            order_type=order_data.get(
                "orderType",
                "",
            ).upper(),
            status=self._normalize_order_status(
                order_data.get("orderStatus")
            ),
            quantity=to_float(
                order_data.get("qty")
            ),
            filled_quantity=to_float(
                order_data.get("cumExecQty")
            ),
            remaining_quantity=to_float(
                order_data.get("leavesQty")
            ),
            price=to_float(
                order_data.get("price")
            ),
            average_price=to_float(
                order_data.get("avgPrice")
            ),
            cumulative_execution_value=to_float(
                order_data.get("cumExecValue")
            ),
            cumulative_execution_fee=to_float(
                order_data.get("cumExecFee")
            ),
            reduce_only=bool(
                order_data.get("reduceOnly", False)
            ),
            close_on_trigger=bool(
                order_data.get("closeOnTrigger", False)
            ),
            dry_run=False,
            accepted=True,
            verified=True,
            created_at_ms=int(
                order_data.get("createdTime") or 0
            ),
            updated_at_ms=int(
                order_data.get("updatedTime") or 0
            ),
            message="Order status verified through Bybit.",
        )

        return execution.model_dump()

    async def get_ticker(self, symbol: str):
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    f"{self.base_url}/v5/market/tickers",
                    params={
                        "category": "spot",
                        "symbol": symbol.upper(),
                    },
                )

            response.raise_for_status()
            payload = response.json()

        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Bybit market request timed out",
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Unable to connect to Bybit: {exc}",
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    "Bybit market request failed with status "
                    f"{exc.response.status_code}"
                ),
            ) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Bybit returned invalid market data",
            ) from exc

        if payload.get("retCode") != 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Bybit API error: "
                    f"{payload.get('retMsg', 'Unknown error')}"
                ),
            )

        items = payload.get("result", {}).get("list", [])

        if not items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bybit ticker not found",
            )

        ticker = items[0]

        return {
            "exchange": "BYBIT",
            "symbol": ticker.get("symbol"),
            "last_price": float(ticker.get("lastPrice") or 0),
            "bid_price": float(ticker.get("bid1Price") or 0),
            "ask_price": float(ticker.get("ask1Price") or 0),
            "high_24h": float(ticker.get("highPrice24h") or 0),
            "low_24h": float(ticker.get("lowPrice24h") or 0),
            "volume_24h": float(ticker.get("volume24h") or 0),
        }
    
    async def get_instrument_rules(
        self,
        symbol: str,
        category: str = "linear",
    ) -> dict:
        normalized_symbol = symbol.upper()
        normalized_category = category.lower()

        supported_categories = {
            "spot",
            "linear",
            "inverse",
            "option",
        }

        if normalized_category not in supported_categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported Bybit instrument category",
            )

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    f"{self.base_url}/v5/market/instruments-info",
                    params={
                        "category": normalized_category,
                        "symbol": normalized_symbol,
                    },
                )
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Bybit instrument request timed out",
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Unable to connect to Bybit: {exc}",
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Bybit returned invalid instrument data",
            ) from exc

        if response.status_code >= 400 or payload.get("retCode") != 0:
            message = payload.get("retMsg") or "Request failed"

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bybit API error: {message}",
            )

        instruments = payload.get("result", {}).get("list", [])

        if not instruments:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bybit instrument not found",
            )

        instrument = instruments[0]
        price_filter = instrument.get("priceFilter", {})
        lot_size_filter = instrument.get("lotSizeFilter", {})

        rules = ExchangeInstrumentRules(
            exchange="BYBIT",
            category=normalized_category,
            symbol=instrument.get(
                "symbol",
                normalized_symbol,
            ),
            status=instrument.get("status", ""),
            base_coin=instrument.get("baseCoin", ""),
            quote_coin=instrument.get("quoteCoin", ""),
            settle_coin=instrument.get("settleCoin", ""),
            min_price=to_decimal(
                price_filter.get("minPrice")
            ),
            max_price=to_decimal(
                price_filter.get("maxPrice")
            ),
            tick_size=to_decimal(
                price_filter.get("tickSize")
            ),
            min_order_quantity=to_decimal(
                lot_size_filter.get("minOrderQty")
            ),
            max_limit_order_quantity=to_decimal(
                lot_size_filter.get("maxOrderQty")
            ),
            max_market_order_quantity=to_decimal(
                lot_size_filter.get("maxMktOrderQty")
            ),
            quantity_step=to_decimal(
                lot_size_filter.get("qtyStep")
            ),
            min_notional_value=to_decimal(
                lot_size_filter.get("minNotionalValue")
            ),
        )

        return rules.model_dump()

    async def get_orderbook(self, symbol: str):
        raise NotImplementedError

    @staticmethod
    def _validate_quantity_against_rules(
        quantity: Decimal,
        rules: ExchangeInstrumentRules,
        order_type: str,
    ) -> None:
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order quantity must be greater than zero",
            )

        if (
            rules.min_order_quantity > 0
            and quantity < rules.min_order_quantity
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Order quantity is below Bybit minimum of "
                    f"{rules.min_order_quantity}"
                ),
            )

        maximum_quantity = (
            rules.max_market_order_quantity
            if order_type == "MARKET"
            else rules.max_limit_order_quantity
        )

        if maximum_quantity > 0 and quantity > maximum_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Order quantity exceeds Bybit maximum of "
                    f"{maximum_quantity}"
                ),
            )

        if not is_step_aligned(
            quantity,
            rules.quantity_step,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Order quantity must align with Bybit quantity "
                    f"step {rules.quantity_step}"
                ),
            )

    @staticmethod
    def _validate_limit_price_against_rules(
        price: Decimal,
        rules: ExchangeInstrumentRules,
    ) -> None:
        if price <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit price must be greater than zero",
            )

        if rules.min_price > 0 and price < rules.min_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Limit price is below Bybit minimum of "
                    f"{rules.min_price}"
                ),
            )

        if rules.max_price > 0 and price > rules.max_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Limit price exceeds Bybit maximum of "
                    f"{rules.max_price}"
                ),
            )

        if not is_step_aligned(
            price,
            rules.tick_size,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Limit price must align with Bybit tick size "
                    f"{rules.tick_size}"
                ),
            )

    @staticmethod
    def _validate_minimum_notional(
        quantity: Decimal,
        price: Decimal,
        rules: ExchangeInstrumentRules,
    ) -> None:
        notional = quantity * price

        if (
            rules.min_notional_value > 0
            and notional < rules.min_notional_value
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Order notional value is below Bybit minimum of "
                    f"{rules.min_notional_value}"
                ),
            )
    @staticmethod
    def _validate_attached_tpsl(
        take_profit: float | None,
        stop_loss: float | None,
        tp_trigger_by: str,
        sl_trigger_by: str,
        tpsl_mode: str,
        tp_order_type: str = "Market",
        sl_order_type: str = "Market",
        tp_limit_price: float | None = None,
        sl_limit_price: float | None = None,
    ) -> None:
        supported_trigger_types = {
            "LastPrice",
            "MarkPrice",
            "IndexPrice",
        }

        supported_modes = {
            "Full",
            "Partial",
        }

        supported_order_types = {
            "Market",
            "Limit",
        }

        if take_profit is not None and take_profit <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Take-profit price must be greater than zero",
            )

        if stop_loss is not None and stop_loss <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stop-loss price must be greater than zero",
            )

        if tp_trigger_by not in supported_trigger_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported take-profit trigger type",
            )

        if sl_trigger_by not in supported_trigger_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported stop-loss trigger type",
            )

        if tpsl_mode not in supported_modes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported TP/SL mode",
            )

        if tp_order_type not in supported_order_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported take-profit order type",
            )

        if sl_order_type not in supported_order_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported stop-loss order type",
            )

        if tpsl_mode == "Full":
            if (
                tp_order_type != "Market"
                or sl_order_type != "Market"
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Full TP/SL mode supports only "
                        "market TP/SL orders"
                    ),
                )

            if (
                tp_limit_price is not None
                or sl_limit_price is not None
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Limit TP/SL prices are not allowed "
                        "in Full mode"
                    ),
                )

        if tp_order_type == "Limit":
            if take_profit is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "take_profit is required for "
                        "a limit take-profit order"
                    ),
                )

            if tp_limit_price is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "tp_limit_price is required when "
                        "tp_order_type is Limit"
                    ),
                )

        elif tp_limit_price is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "tp_limit_price requires "
                    "tp_order_type=Limit"
                ),
            )

        if sl_order_type == "Limit":
            if stop_loss is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "stop_loss is required for "
                        "a limit stop-loss order"
                    ),
                )

            if sl_limit_price is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "sl_limit_price is required when "
                        "sl_order_type is Limit"
                    ),
                )

        elif sl_limit_price is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "sl_limit_price requires "
                    "sl_order_type=Limit"
                ),
            )
    async def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        category: str = "linear",
        time_in_force: str = "IOC",
        reduce_only: bool = False,
        close_on_trigger: bool = False,
        take_profit: float | None = None,
        stop_loss: float | None = None,
        tp_trigger_by: str = "LastPrice",
        sl_trigger_by: str = "LastPrice",
        tpsl_mode: str = "Full",
        tp_order_type: str = "Market",
        sl_order_type: str = "Market",
        tp_limit_price: float | None = None,
        sl_limit_price: float | None = None,
        client_order_id: str | None = None,
        dry_run: bool = True,
    ) -> dict:
        normalized_symbol = symbol.upper()
        normalized_side = side.upper()
        normalized_category = category.lower()

        bybit_side = (
            "Buy"
            if normalized_side == "BUY"
            else "Sell"
        )

        self._validate_attached_tpsl(
            take_profit=take_profit,
            stop_loss=stop_loss,
            tp_trigger_by=tp_trigger_by,
            sl_trigger_by=sl_trigger_by,
            tpsl_mode=tpsl_mode,
            tp_order_type=tp_order_type,
            sl_order_type=sl_order_type,
            tp_limit_price=tp_limit_price,
            sl_limit_price=sl_limit_price,
        )

        rules_data = await self.get_instrument_rules(
            symbol=normalized_symbol,
            category=normalized_category,
        )

        rules = ExchangeInstrumentRules.model_validate(
            rules_data
        )

        quantity_decimal = to_decimal(quantity)

        self._validate_quantity_against_rules(
            quantity=quantity_decimal,
            rules=rules,
            order_type="MARKET",
        )

        body = {
            "category": normalized_category,
            "symbol": normalized_symbol,
            "side": bybit_side,
            "orderType": "Market",
            "qty": decimal_to_plain_string(
                quantity_decimal
            ),
            "timeInForce": time_in_force,
            "reduceOnly": reduce_only,
            "closeOnTrigger": close_on_trigger,
        }

        if client_order_id:
            body["orderLinkId"] = client_order_id

        if take_profit is not None:
            body["takeProfit"] = decimal_to_plain_string(
                to_decimal(take_profit)
            )
            body["tpTriggerBy"] = tp_trigger_by
            body["tpOrderType"] = tp_order_type

        if stop_loss is not None:
            body["stopLoss"] = decimal_to_plain_string(
                to_decimal(stop_loss)
            )
            body["slTriggerBy"] = sl_trigger_by
            body["slOrderType"] = sl_order_type

        if (
            take_profit is not None
            or stop_loss is not None
        ):
            body["tpslMode"] = tpsl_mode

        if tp_limit_price is not None:
            body["tpLimitPrice"] = decimal_to_plain_string(
                to_decimal(tp_limit_price)
            )

        if sl_limit_price is not None:
            body["slLimitPrice"] = decimal_to_plain_string(
                to_decimal(sl_limit_price)
            )

        if dry_run:
            return ExchangeOrderPlacement(
                exchange="BYBIT",
                category=normalized_category,
                order_id="",
                client_order_id=client_order_id or "",
                symbol=normalized_symbol,
                side=normalized_side,
                order_type="MARKET",
                quantity=quantity,
                price=0.0,
                dry_run=True,
                accepted=False,
                message=(
                    "Dry run completed. "
                    "No order was sent to Bybit."
                ),
            ).model_dump()

        payload = await self._private_post(
            endpoint="/v5/order/create",
            body=body,
        )

        result = payload.get("result", {})
        order_id = result.get("orderId", "")

        verified_order = await self.get_order_by_id(
            order_id=order_id,
            category=normalized_category,
            symbol=normalized_symbol,
        )

        if verified_order is not None:
            return verified_order

        return ExchangeOrderExecution(
            exchange="BYBIT",
            category=normalized_category,
            order_id=order_id,
            client_order_id=result.get(
                "orderLinkId",
                client_order_id or "",
            ),
            symbol=normalized_symbol,
            side=normalized_side,
            order_type="MARKET",
            status="PENDING",
            quantity=quantity,
            price=0.0,
            reduce_only=reduce_only,
            close_on_trigger=close_on_trigger,
            dry_run=False,
            accepted=True,
            verified=False,
            message=(
                "Market order accepted by Bybit, "
                "but its status is not available yet."
            ),
        ).model_dump()
    
    async def place_stop_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        trigger_price: float,
        trigger_direction: int,
        trigger_by: str = "LastPrice",
        category: str = "linear",
        time_in_force: str = "GTC",
        reduce_only: bool = False,
        close_on_trigger: bool = False,
        position_index: int = 0,
        take_profit: float | None = None,
        stop_loss: float | None = None,
        tp_trigger_by: str = "LastPrice",
        sl_trigger_by: str = "LastPrice",
        tpsl_mode: str = "Full",
        client_order_id: str | None = None,
        dry_run: bool = True,
    ) -> dict:
        normalized_symbol = symbol.upper()
        normalized_side = side.upper()
        normalized_category = category.lower()

        bybit_side = (
            "Buy"
            if normalized_side == "BUY"
            else "Sell"
        )
        
        if trigger_direction not in {1, 2}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "trigger_direction must be 1 "
                    "for rising price or 2 for falling price"
                ),
            )

        supported_trigger_types = {
            "LastPrice",
            "MarkPrice",
            "IndexPrice",
        }

        if trigger_by not in supported_trigger_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported Bybit trigger price type",
            )

        rules_data = await self.get_instrument_rules(
            symbol=normalized_symbol,
            category=normalized_category,
        )

        rules = ExchangeInstrumentRules.model_validate(
            rules_data
        )

        quantity_decimal = to_decimal(quantity)
        price_decimal = to_decimal(price)
        trigger_price_decimal = to_decimal(
            trigger_price
        )

        self._validate_quantity_against_rules(
            quantity=quantity_decimal,
            rules=rules,
            order_type="LIMIT",
        )

        self._validate_limit_price_against_rules(
            price=price_decimal,
            rules=rules,
        )

        self._validate_limit_price_against_rules(
            price=trigger_price_decimal,
            rules=rules,
        )

        self._validate_minimum_notional(
            quantity=quantity_decimal,
            price=price_decimal,
            rules=rules,
        )

        body = {
            "category": normalized_category,
            "symbol": normalized_symbol,
            "side": bybit_side,
            "orderType": "Limit",
            "qty": decimal_to_plain_string(
                quantity_decimal
            ),
            "price": decimal_to_plain_string(
                price_decimal
            ),
            "triggerPrice": decimal_to_plain_string(
                trigger_price_decimal
            ),
            "triggerDirection": trigger_direction,
            "triggerBy": trigger_by,
            "timeInForce": time_in_force,
            "reduceOnly": reduce_only,
            "closeOnTrigger": close_on_trigger,
            "positionIdx": position_index,
        }
        if take_profit is not None:
            body["takeProfit"] = decimal_to_plain_string(
                to_decimal(take_profit)
            )
            body["tpTriggerBy"] = tp_trigger_by

        if stop_loss is not None:
            body["stopLoss"] = decimal_to_plain_string(
                to_decimal(stop_loss)
            )
            body["slTriggerBy"] = sl_trigger_by

        if (
            take_profit is not None
            or stop_loss is not None
        ):
            body["tpslMode"] = tpsl_mode
            body["tpOrderType"] = "Market"
            body["slOrderType"] = "Market"
        if client_order_id:
            body["orderLinkId"] = client_order_id

        if dry_run:
            return ExchangeOrderExecution(
                exchange="BYBIT",
                category=normalized_category,
                order_id="",
                client_order_id=client_order_id or "",
                symbol=normalized_symbol,
                side=normalized_side,
                order_type="STOP_LIMIT",
                status="PENDING",
                quantity=quantity,
                price=price,
                dry_run=True,
                accepted=False,
                verified=False,
                message=(
                    "Dry run completed. "
                    "No stop-limit order was sent to Bybit."
                ),
            ).model_dump()

        payload = await self._private_post(
            endpoint="/v5/order/create",
            body=body,
        )

        result = payload.get("result", {})
        order_id = result.get("orderId", "")

        verified_order = await self.get_order_by_id(
            order_id=order_id,
            category=normalized_category,
            symbol=normalized_symbol,
        )

        if verified_order is not None:
            return verified_order

        return ExchangeOrderExecution(
            exchange="BYBIT",
            category=normalized_category,
            order_id=order_id,
            client_order_id=result.get(
                "orderLinkId",
                client_order_id or "",
            ),
            symbol=normalized_symbol,
            side=normalized_side,
            order_type="STOP_LIMIT",
            status="PENDING",
            quantity=quantity,
            price=price,
            dry_run=False,
            accepted=True,
            verified=False,
            message=(
                "Stop-limit order accepted by Bybit, "
                "but its status is not available yet."
            ),
        ).model_dump()

    async def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        category: str = "linear",
        time_in_force: str = "GTC",
        reduce_only: bool = False,
        close_on_trigger: bool = False,
        take_profit: float | None = None,
        stop_loss: float | None = None,
        tp_trigger_by: str = "LastPrice",
        sl_trigger_by: str = "LastPrice",
        tpsl_mode: str = "Full",
        client_order_id: str | None = None,
        dry_run: bool = True,
        tp_order_type: str = "Market",
        sl_order_type: str = "Market",
        tp_limit_price: float | None = None,
        sl_limit_price: float | None = None,
    ) -> dict:
        normalized_symbol = symbol.upper()
        normalized_side = side.upper()
        bybit_side = "Buy" if normalized_side == "BUY" else "Sell"

        rules_data = await self.get_instrument_rules(
            symbol=normalized_symbol,
            category=category,
        )

        rules = ExchangeInstrumentRules.model_validate(
            rules_data
        )

        quantity_decimal = to_decimal(quantity)
        price_decimal = to_decimal(price)

        self._validate_quantity_against_rules(
            quantity=quantity_decimal,
            rules=rules,
            order_type="LIMIT",
        )

        self._validate_limit_price_against_rules(
            price=price_decimal,
            rules=rules,
        )

        self._validate_minimum_notional(
            quantity=quantity_decimal,
            price=price_decimal,
            rules=rules,
        )

        body = {
            "category": category.lower(),
            "symbol": normalized_symbol,
            "side": bybit_side,
            "orderType": "Limit",
            "qty": decimal_to_plain_string(
                quantity_decimal
            ),
            "price": decimal_to_plain_string(
                price_decimal
            ),
            "timeInForce": time_in_force,
            "reduceOnly": reduce_only,
            "closeOnTrigger": close_on_trigger,
        }
        if take_profit is not None:
            body["takeProfit"] = decimal_to_plain_string(
                to_decimal(take_profit)
            )
            body["tpTriggerBy"] = tp_trigger_by
            body["tpOrderType"] = tp_order_type

        if stop_loss is not None:
            body["stopLoss"] = decimal_to_plain_string(
                to_decimal(stop_loss)
            )
            body["slTriggerBy"] = sl_trigger_by
            body["slOrderType"] = sl_order_type

        if take_profit is not None or stop_loss is not None:
            body["tpslMode"] = tpsl_mode

        if tp_limit_price is not None:
            body["tpLimitPrice"] = decimal_to_plain_string(
                to_decimal(tp_limit_price)
            )

        if sl_limit_price is not None:
            body["slLimitPrice"] = decimal_to_plain_string(
                to_decimal(sl_limit_price)
            )
        if client_order_id:
            body["orderLinkId"] = client_order_id

        if dry_run:
            return ExchangeOrderPlacement(
                exchange="BYBIT",
                category=category.lower(),
                symbol=normalized_symbol,
                side=normalized_side,
                order_type="LIMIT",
                quantity=quantity,
                price=price,
                dry_run=True,
                accepted=False,
                client_order_id=client_order_id or "",
                message=(
                    "Dry run completed. "
                    "No order was sent to Bybit."
                ),
            ).model_dump()

        payload = await self._private_post(
            endpoint="/v5/order/create",
            body=body,
        )

        result = payload.get("result", {})
        order_id = result.get("orderId", "")
        returned_client_order_id = result.get(
            "orderLinkId",
            client_order_id or "",
        )

        verified_order = await self.get_order_by_id(
            order_id=order_id,
            category=category,
            symbol=normalized_symbol,
        )

        if verified_order is not None:
            return verified_order

        return ExchangeOrderExecution(
            exchange="BYBIT",
            category=category.lower(),
            order_id=order_id,
            client_order_id=returned_client_order_id,
            symbol=normalized_symbol,
            side=normalized_side,
            order_type="LIMIT",
            status="PENDING",
            quantity=quantity,
            price=price,
            dry_run=False,
            accepted=True,
            verified=False,
            message=(
                "Order accepted by Bybit, but its status "
                "is not available yet."
            ),
        ).model_dump()

    @staticmethod
    def _normalize_order_status(
        bybit_status: str | None,
    ) -> str:
        status_mapping = {
            "Created": "PENDING",
            "New": "NEW",
            "PartiallyFilled": "PARTIALLY_FILLED",
            "Filled": "FILLED",
            "Cancelled": "CANCELLED",
            "PartiallyFilledCanceled": "CANCELLED",
            "Rejected": "REJECTED",
            "Deactivated": "EXPIRED",
            "Untriggered": "PENDING",
            "Triggered": "NEW",
        }

        return status_mapping.get(
            bybit_status or "",
            "UNKNOWN",
        )

        return ExchangeOrderPlacement(
            exchange="BYBIT",
            category=category.lower(),
            order_id=result.get("orderId", ""),
            client_order_id=result.get("orderLinkId", ""),
            symbol=normalized_symbol,
            side=normalized_side,
            order_type="LIMIT",
            quantity=quantity,
            price=price,
            dry_run=False,
            accepted=True,
            message="Order request accepted by Bybit.",
        ).model_dump()

    async def cancel_order(
        self,
        symbol: str,
        order_id: str | None = None,
        client_order_id: str | None = None,
        category: str = "linear",
        dry_run: bool = True,
    ) -> dict:
        normalized_symbol = symbol.upper()
        normalized_category = category.lower()

        if not order_id and not client_order_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Either order_id or client_order_id "
                    "is required"
                ),
            )

        body = {
            "category": normalized_category,
            "symbol": normalized_symbol,
        }

        if order_id:
            body["orderId"] = order_id

        if client_order_id:
            body["orderLinkId"] = client_order_id

        if dry_run:
            return ExchangeOrderActionResult(
                exchange="BYBIT",
                category=normalized_category,
                symbol=normalized_symbol,
                action="CANCEL",
                order_id=order_id or "",
                client_order_id=client_order_id or "",
                dry_run=True,
                accepted=False,
                message=(
                    "Dry run completed. No cancellation "
                    "was sent to Bybit."
                ),
            ).model_dump()

        payload = await self._private_post(
            endpoint="/v5/order/cancel",
            body=body,
        )

        result = payload.get("result", {})

        return ExchangeOrderActionResult(
            exchange="BYBIT",
            category=normalized_category,
            symbol=normalized_symbol,
            action="CANCEL",
            order_id=result.get(
                "orderId",
                order_id or "",
            ),
            client_order_id=result.get(
                "orderLinkId",
                client_order_id or "",
            ),
            dry_run=False,
            accepted=True,
            message="Cancellation request accepted by Bybit.",
        ).model_dump()
    
    async def amend_order(
        self,
        symbol: str,
        order_id: str | None = None,
        client_order_id: str | None = None,
        quantity: float | None = None,
        price: float | None = None,
        trigger_price: float | None = None,
        take_profit: float | None = None,
        stop_loss: float | None = None,
        category: str = "linear",
        dry_run: bool = True,
    ) -> dict:
        normalized_symbol = symbol.upper()
        normalized_category = category.lower()

        if not order_id and not client_order_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Either order_id or client_order_id "
                    "is required"
                ),
            )

        amendment_values = (
            quantity,
            price,
            trigger_price,
            take_profit,
            stop_loss,
        )

        if all(value is None for value in amendment_values):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one amendment value is required",
            )

        rules_data = await self.get_instrument_rules(
            symbol=normalized_symbol,
            category=normalized_category,
        )

        rules = ExchangeInstrumentRules.model_validate(
            rules_data
        )

        body = {
            "category": normalized_category,
            "symbol": normalized_symbol,
        }

        if order_id:
            body["orderId"] = order_id

        if client_order_id:
            body["orderLinkId"] = client_order_id

        if quantity is not None:
            quantity_decimal = to_decimal(quantity)

            self._validate_quantity_against_rules(
                quantity=quantity_decimal,
                rules=rules,
                order_type="LIMIT",
            )

            body["qty"] = decimal_to_plain_string(
                quantity_decimal
            )

        if price is not None:
            price_decimal = to_decimal(price)

            self._validate_limit_price_against_rules(
                price=price_decimal,
                rules=rules,
            )

            body["price"] = decimal_to_plain_string(
                price_decimal
            )

        if quantity is not None and price is not None:
            self._validate_minimum_notional(
                quantity=quantity_decimal,
                price=price_decimal,
                rules=rules,
            )

        if trigger_price is not None:
            body["triggerPrice"] = decimal_to_plain_string(
                to_decimal(trigger_price)
            )

        if take_profit is not None:
            body["takeProfit"] = decimal_to_plain_string(
                to_decimal(take_profit)
            )

        if stop_loss is not None:
            body["stopLoss"] = decimal_to_plain_string(
                to_decimal(stop_loss)
            )

        if dry_run:
            return ExchangeOrderActionResult(
                exchange="BYBIT",
                category=normalized_category,
                symbol=normalized_symbol,
                action="AMEND",
                order_id=order_id or "",
                client_order_id=client_order_id or "",
                dry_run=True,
                accepted=False,
                message=(
                    "Dry run completed. No amendment "
                    "was sent to Bybit."
                ),
            ).model_dump()

        payload = await self._private_post(
            endpoint="/v5/order/amend",
            body=body,
        )

        result = payload.get("result", {})

        return ExchangeOrderActionResult(
            exchange="BYBIT",
            category=normalized_category,
            symbol=normalized_symbol,
            action="AMEND",
            order_id=result.get(
                "orderId",
                order_id or "",
            ),
            client_order_id=result.get(
                "orderLinkId",
                client_order_id or "",
            ),
            dry_run=False,
            accepted=True,
            message="Amendment request accepted by Bybit.",
        ).model_dump()
        
    async def place_stop_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        trigger_price: float,
        trigger_direction: int,
        trigger_by: str = "LastPrice",
        category: str = "linear",
        reduce_only: bool = False,
        close_on_trigger: bool = False,
        position_index: int = 0,
        client_order_id: str | None = None,
        dry_run: bool = True,
    ) -> dict:
        normalized_symbol = symbol.upper()
        normalized_side = side.upper()
        normalized_category = category.lower()

        bybit_side = (
            "Buy"
            if normalized_side == "BUY"
            else "Sell"
        )

        if trigger_direction not in {1, 2}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "trigger_direction must be 1 "
                    "for rising price or 2 for falling price"
                ),
            )

        supported_trigger_types = {
            "LastPrice",
            "MarkPrice",
            "IndexPrice",
        }

        if trigger_by not in supported_trigger_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported Bybit trigger price type",
            )

        rules_data = await self.get_instrument_rules(
            symbol=normalized_symbol,
            category=normalized_category,
        )

        rules = ExchangeInstrumentRules.model_validate(
            rules_data
        )

        quantity_decimal = to_decimal(quantity)
        trigger_price_decimal = to_decimal(
            trigger_price
        )

        self._validate_quantity_against_rules(
            quantity=quantity_decimal,
            rules=rules,
            order_type="MARKET",
        )

        self._validate_limit_price_against_rules(
            price=trigger_price_decimal,
            rules=rules,
        )

        body = {
            "category": normalized_category,
            "symbol": normalized_symbol,
            "side": bybit_side,
            "orderType": "Market",
            "qty": decimal_to_plain_string(
                quantity_decimal
            ),
            "triggerPrice": decimal_to_plain_string(
                trigger_price_decimal
            ),
            "triggerDirection": trigger_direction,
            "triggerBy": trigger_by,
            "reduceOnly": reduce_only,
            "closeOnTrigger": close_on_trigger,
            "positionIdx": position_index,
        }

        if client_order_id:
            body["orderLinkId"] = client_order_id

        if dry_run:
            return ExchangeOrderExecution(
                exchange="BYBIT",
                category=normalized_category,
                order_id="",
                client_order_id=client_order_id or "",
                symbol=normalized_symbol,
                side=normalized_side,
                order_type="STOP_MARKET",
                status="PENDING",
                quantity=quantity,
                price=trigger_price,
                dry_run=True,
                accepted=False,
                verified=False,
                message=(
                    "Dry run completed. "
                    "No stop-market order was sent to Bybit."
                ),
            ).model_dump()

        payload = await self._private_post(
            endpoint="/v5/order/create",
            body=body,
        )

        result = payload.get("result", {})
        order_id = result.get("orderId", "")

        verified_order = await self.get_order_by_id(
            order_id=order_id,
            category=normalized_category,
            symbol=normalized_symbol,
        )

        if verified_order is not None:
            return verified_order

        return ExchangeOrderExecution(
            exchange="BYBIT",
            category=normalized_category,
            order_id=order_id,
            client_order_id=result.get(
                "orderLinkId",
                client_order_id or "",
            ),
            symbol=normalized_symbol,
            side=normalized_side,
            order_type="STOP_MARKET",
            status="PENDING",
            quantity=quantity,
            price=trigger_price,
            dry_run=False,
            accepted=True,
            verified=False,
            message=(
                "Stop-market order accepted by Bybit, "
                "but its status is not available yet."
            ),
        ).model_dump()
    
async def place_stop_market_order(
    self,
    **kwargs,
):
    raise NotImplementedError

async def place_stop_limit_order(
    self,
    **kwargs,
):
    raise NotImplementedError