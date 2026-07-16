from abc import ABC, abstractmethod


class BaseExchangeClient(ABC):
    """
    Abstract base class that every exchange client must implement.
    """

    @abstractmethod
    async def test_connection(self):
        """Verify API credentials."""
        raise NotImplementedError

    @abstractmethod
    async def get_account_balance(self):
        """Return wallet balances."""
        raise NotImplementedError

    @abstractmethod
    async def get_positions(
        self,
        category: str = "linear",
        settle_coin: str = "USDT",
    ):
        """Return normalized open positions."""
        raise NotImplementedError

    @abstractmethod
    async def get_open_orders(
        self,
        category: str = "linear",
        settle_coin: str = "USDT",
        symbol: str | None = None,
    ):
        """Return normalized active orders."""
        raise NotImplementedError

    @abstractmethod
    async def get_ticker(self, symbol: str):
        """Return ticker information."""
        raise NotImplementedError

    @abstractmethod
    async def get_orderbook(self, symbol: str):
        """Return order book."""
        raise NotImplementedError

    @abstractmethod
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
        tp_order_type: str = "Market",
        sl_order_type: str = "Market",
        tp_limit_price: float | None = None,
        sl_limit_price: float | None = None,
    ):
        """Create or simulate a market order."""
        raise NotImplementedError

    @abstractmethod
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
    ):
        """Create or simulate a limit order."""
        raise NotImplementedError
    
    @abstractmethod
    async def cancel_order(
        self,
        symbol: str,
        order_id: str | None = None,
        client_order_id: str | None = None,
        category: str = "linear",
        dry_run: bool = True,
    ):
        """Cancel or simulate cancellation of an active order."""
        raise NotImplementedError
    
    @abstractmethod
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
        """Amend or simulate amendment of an active order."""
        raise NotImplementedError
    
    @abstractmethod
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
        take_profit: float | None = None,
        stop_loss: float | None = None,
        tp_trigger_by: str = "LastPrice",
        sl_trigger_by: str = "LastPrice",
        tpsl_mode: str = "Full",
        client_order_id: str | None = None,
        dry_run: bool = True,
        
    ):
        """Create or simulate a conditional stop-market order."""
        raise NotImplementedError

async def place_stop_limit_order(
    self,
    **kwargs,
):
    raise NotImplementedError