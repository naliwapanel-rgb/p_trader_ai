import httpx

from app.exchanges.base import BaseExchangeClient


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

    async def test_connection(self):
        return await self.get_ticker("BTCUSDT")

    async def get_account_balance(self):
        raise NotImplementedError

    async def get_positions(self):
        raise NotImplementedError

    async def get_open_orders(self):
        raise NotImplementedError

    async def get_ticker(self, symbol: str):
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.base_url}/v5/market/tickers",
                params={
                    "category": "spot",
                    "symbol": symbol.upper(),
                },
            )

            response.raise_for_status()
            payload = response.json()

            if payload.get("retCode") != 0:
                raise RuntimeError(payload.get("retMsg", "Bybit API error"))

            result = payload.get("result", {})
            items = result.get("list", [])

            if not items:
                raise RuntimeError("Ticker not found")

            ticker = items[0]

            return {
                "exchange": "BYBIT",
                "symbol": ticker.get("symbol"),
                "last_price": float(ticker.get("lastPrice", 0)),
                "bid_price": float(ticker.get("bid1Price", 0)),
                "ask_price": float(ticker.get("ask1Price", 0)),
                "high_24h": float(ticker.get("highPrice24h", 0)),
                "low_24h": float(ticker.get("lowPrice24h", 0)),
                "volume_24h": float(ticker.get("volume24h", 0)),
            }

    async def get_orderbook(self, symbol: str):
        raise NotImplementedError

    async def place_market_order(self, symbol: str, side: str, quantity: float):
        raise NotImplementedError

    async def place_limit_order(self, symbol: str, side: str, quantity: float, price: float):
        raise NotImplementedError

    async def cancel_order(self, symbol: str, order_id: str):
        raise NotImplementedError