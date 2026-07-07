from app.exchanges.base import BaseExchangeClient


class GateIOClient(BaseExchangeClient):
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        is_testnet: bool = False,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.is_testnet = is_testnet

    async def test_connection(self):
        raise NotImplementedError

    async def get_account_balance(self):
        raise NotImplementedError

    async def get_positions(self):
        raise NotImplementedError

    async def get_open_orders(self):
        raise NotImplementedError

    async def get_ticker(self, symbol: str):
        raise NotImplementedError

    async def get_orderbook(self, symbol: str):
        raise NotImplementedError

    async def place_market_order(self, symbol: str, side: str, quantity: float):
        raise NotImplementedError

    async def place_limit_order(self, symbol: str, side: str, quantity: float, price: float):
        raise NotImplementedError

    async def cancel_order(self, symbol: str, order_id: str):
        raise NotImplementedError