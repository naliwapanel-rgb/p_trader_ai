from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status

from app.exchanges.base import BaseExchangeClient
from app.exchanges.bybit.auth import BybitAuth


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

    async def get_account_balance(self):
        payload = await self._private_get(
            endpoint="/v5/account/wallet-balance",
            params={
                "accountType": "UNIFIED",
            },
        )

        return payload.get("result", {})

    async def get_positions(self):
        raise NotImplementedError

    async def get_open_orders(self):
        raise NotImplementedError

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