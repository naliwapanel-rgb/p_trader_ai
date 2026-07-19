from collections.abc import Callable
from typing import Any
from app.exchanges.bybit.market_data import (
    BybitMarketDataClient,
)
from app.schemas.market_scanner import (
    MarketScanRequest,
    MarketScanResult,
    MarketTickerBatch,
    MarketTickerSnapshot,
)
class MarketScannerService:
    def __init__(
        self,
        client_factory: (
            Callable[[bool], Any] | None
        ) = None,
    ):
        self.client_factory = (
            client_factory
            or (
                lambda is_testnet:
                BybitMarketDataClient(
                    is_testnet=is_testnet
                )
            )
        )
    @staticmethod
    def _sort_value(
        ticker: MarketTickerSnapshot,
        sort_by: str,
    ):
        if (
            sort_by
            == (
                "absolute_"
                "price_change_percent_24h"
            )
        ):
            return abs(
                ticker.price_change_percent_24h
            )
        return getattr(
            ticker,
            sort_by,
        )
    @staticmethod
    def _matches(
        *,
        ticker: MarketTickerSnapshot,
        data: MarketScanRequest,
        allowed_symbols: set[str],
    ) -> bool:
        if (
            allowed_symbols
            and ticker.symbol
            not in allowed_symbols
        ):
            return False
        if (
            data.quote_coin
            and not ticker.symbol.endswith(
                data.quote_coin
            )
        ):
            return False
        if (
            data.minimum_price is not None
            and ticker.last_price
            < data.minimum_price
        ):
            return False
        if (
            data.maximum_price is not None
            and ticker.last_price
            > data.maximum_price
        ):
            return False
        if (
            ticker.volume_24h
            < data.minimum_volume_24h
        ):
            return False
        if (
            ticker.turnover_24h
            < data.minimum_turnover_24h
        ):
            return False
        if (
            data.minimum_change_percent_24h
            is not None
            and (
                ticker.price_change_percent_24h
                < (
                    data
                    .minimum_change_percent_24h
                )
            )
        ):
            return False
        if (
            data.maximum_change_percent_24h
            is not None
            and (
                ticker.price_change_percent_24h
                > (
                    data
                    .maximum_change_percent_24h
                )
            )
        ):
            return False
        return True
    async def get_tickers(
        self,
        *,
        category: str = "spot",
        is_testnet: bool = False,
    ) -> MarketTickerBatch:
        client = self.client_factory(
            is_testnet
        )
        raw_batch = await client.get_tickers(
            category=category
        )
        return MarketTickerBatch.model_validate(
            raw_batch
        )
    async def scan(
        self,
        data: MarketScanRequest,
    ) -> MarketScanResult:
        batch = await self.get_tickers(
            category=data.category,
            is_testnet=data.is_testnet,
        )
        allowed_symbols = set(data.symbols)
        matched = [
            ticker
            for ticker in batch.tickers
            if self._matches(
                ticker=ticker,
                data=data,
                allowed_symbols=allowed_symbols,
            )
        ]
        matched.sort(
            key=lambda ticker: ticker.symbol
        )
        if data.sort_by == "symbol":
            if data.descending:
                matched.reverse()
        else:
            matched.sort(
                key=lambda ticker:
                self._sort_value(
                    ticker,
                    data.sort_by,
                ),
                reverse=data.descending,
            )
        total_matched = len(matched)
        returned = matched[: data.limit]
        return MarketScanResult(
            exchange=batch.exchange,
            category=batch.category,
            quote_coin=data.quote_coin,
            total_received=len(
                batch.tickers
            ),
            total_matched=total_matched,
            returned_count=len(returned),
            scanned_at_ms=(
                batch.observed_at_ms
            ),
            tickers=returned,
        )
