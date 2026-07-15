from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status

from app.exchanges.base import BaseExchangeClient
from app.exchanges.bybit.auth import BybitAuth
from app.exchanges.utils import to_float
from app.schemas.exchange_balance import (
    ExchangeBalance,
    ExchangeCoinBalance,
)
from app.schemas.exchange_position import (
    ExchangePosition,
    ExchangePositionList,
)
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
            message = response.text.strip() or "Invalid response from Bybit"

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bybit API error: {message}",
            )

        if response.status_code >= 400 or payload.get("retCode") != 0:
            message = payload.get("retMsg") or "Request failed"

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bybit API error: {message}",
            )

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

    async def get_orderbook(self, symbol: str):
        raise NotImplementedError

    async def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
    ):
        raise NotImplementedError

    async def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
    ):
        raise NotImplementedError

    async def cancel_order(
        self,
        symbol: str,
        order_id: str,
    ):
        raise NotImplementedError