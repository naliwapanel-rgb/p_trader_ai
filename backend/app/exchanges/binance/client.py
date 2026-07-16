from app.exchanges.base import BaseExchangeClient


class BinanceClient(BaseExchangeClient):
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

    async def get_positions(
    self,
    category: str = "linear",
    settle_coin: str = "USDT",
):
     raise NotImplementedError

    async def get_open_orders(
        self,
        category: str = "linear",
        settle_coin: str = "USDT",
        symbol: str | None = None,
    ):
        raise NotImplementedError

    async def get_ticker(self, symbol: str):
        raise NotImplementedError

    async def get_orderbook(self, symbol: str):
        raise NotImplementedError

    async def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        category: str = "linear",
        time_in_force: str = "IOC",
        reduce_only: bool = False,
        close_on_trigger: bool = False,
        client_order_id: str | None = None,
        dry_run: bool = True,
    ):
        """Create or simulate a market order."""
        raise NotImplementedError

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
        client_order_id: str | None = None,
        dry_run: bool = True,
    ):
        """Create or simulate a limit order."""
        raise NotImplementedError

    async def cancel_order(
        self,
        symbol: str,
        order_id: str | None = None,
        client_order_id: str | None = None,
        category: str = "linear",
        dry_run: bool = True,
    ):
        raise NotImplementedError
    
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
    ):
        raise NotImplementedError
    
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
    ):
        raise NotImplementedError
    
    async def set_position_tpsl(
        self,
        symbol: str,
        category: str = "linear",
        position_index: int = 0,
        take_profit: float | None = None,
        stop_loss: float | None = None,
        tp_trigger_by: str = "LastPrice",
        sl_trigger_by: str = "LastPrice",
        tpsl_mode: str = "Full",
        tp_order_type: str = "Market",
        sl_order_type: str = "Market",
        tp_size: float | None = None,
        sl_size: float | None = None,
        tp_limit_price: float | None = None,
        sl_limit_price: float | None = None,
        dry_run: bool = True,
    ) -> dict:
        """Set or update TP/SL on an existing position."""
        raise NotImplementedError