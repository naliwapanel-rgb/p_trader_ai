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
    async def get_open_orders(self):
        """Return open orders."""
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
    ):
        """Execute market order."""
        raise NotImplementedError

    @abstractmethod
    async def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
    ):
        """Execute limit order."""
        raise NotImplementedError

    @abstractmethod
    async def cancel_order(
        self,
        symbol: str,
        order_id: str,
    ):
        """Cancel order."""
        raise NotImplementedError