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
        client_order_id: str | None = None,
        dry_run: bool = True,
    ):
        """Create or simulate a limit order."""
        raise NotImplementedError
    
    @abstractmethod
    async def cancel_order(
        self,
        symbol: str,
        order_id: str,
    ):
        """Cancel order."""
        raise NotImplementedError