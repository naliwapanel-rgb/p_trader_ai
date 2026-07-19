import asyncio
import json
import time
from collections.abc import (
    AsyncIterator,
    Callable,
)
from contextlib import suppress
from typing import Any
from fastapi import HTTPException, status
from websockets.asyncio.client import connect
from websockets.exceptions import (
    ConnectionClosed,
    InvalidHandshake,
    InvalidURI,
)
from app.exchanges.bybit.market_data import (
    BybitMarketDataClient,
)
from app.schemas.market_scanner import (
    MarketCategory,
    MarketTickerStreamEvent,
)
class BybitTickerStreamClient:
    SUPPORTED_CATEGORIES = {
        "spot",
        "linear",
        "inverse",
    }
    def __init__(
        self,
        *,
        is_testnet: bool = False,
        connect_factory: (
            Callable[..., Any] | None
        ) = None,
        heartbeat_interval_seconds: float = 20.0,
    ):
        self.is_testnet = is_testnet
        self.connect_factory = (
            connect_factory or connect
        )
        self.heartbeat_interval_seconds = (
            heartbeat_interval_seconds
        )
    @classmethod
    def normalize_category(
        cls,
        category: str,
    ) -> MarketCategory:
        normalized = category.strip().lower()
        if normalized not in cls.SUPPORTED_CATEGORIES:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "category must be spot, "
                    "linear or inverse"
                ),
            )
        return normalized
    @staticmethod
    def normalize_symbols(
        symbols: list[str],
    ) -> list[str]:
        normalized: list[str] = []
        for value in symbols:
            symbol = value.strip().upper()
            if not symbol:
                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "symbols cannot contain "
                        "blank values"
                    ),
                )
            if symbol not in normalized:
                normalized.append(symbol)
        if not normalized:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "At least one symbol is required"
                ),
            )
        if len(normalized) > 100:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "A maximum of 100 symbols "
                    "is supported"
                ),
            )
        return normalized
    def websocket_url(
        self,
        category: str,
    ) -> str:
        normalized_category = (
            self.normalize_category(category)
        )
        host = (
            "stream-testnet.bybit.com"
            if self.is_testnet
            else "stream.bybit.com"
        )
        return (
            f"wss://{host}/v5/public/"
            f"{normalized_category}"
        )
    @staticmethod
    def _to_int(value: Any) -> int:
        try:
            return int(float(value or 0))
        except (TypeError, ValueError):
            return 0
    @staticmethod
    def _decode_message(
        raw_message: str | bytes,
    ) -> dict:
        try:
            message = json.loads(raw_message)
        except (
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_502_BAD_GATEWAY
                ),
                detail=(
                    "Bybit returned malformed "
                    "WebSocket data"
                ),
            ) from exc
        if not isinstance(message, dict):
            raise HTTPException(
                status_code=(
                    status.HTTP_502_BAD_GATEWAY
                ),
                detail=(
                    "Bybit returned malformed "
                    "WebSocket data"
                ),
            )
        return message
    @staticmethod
    def _subscription_batches(
        *,
        category: MarketCategory,
        symbols: list[str],
    ) -> list[list[str]]:
        batch_size = (
            10
            if category == "spot"
            else 100
        )
        topics = [
            f"tickers.{symbol}"
            for symbol in symbols
        ]
        return [
            topics[index:index + batch_size]
            for index in range(
                0,
                len(topics),
                batch_size,
            )
        ]
    async def _send_subscriptions(
        self,
        *,
        websocket: Any,
        category: MarketCategory,
        symbols: list[str],
    ) -> None:
        batches = self._subscription_batches(
            category=category,
            symbols=symbols,
        )
        for index, topics in enumerate(
            batches,
            start=1,
        ):
            request = {
                "req_id": (
                    f"market-stream-{index}"
                ),
                "op": "subscribe",
                "args": topics,
            }
            await websocket.send(
                json.dumps(
                    request,
                    separators=(",", ":"),
                )
            )
    async def _heartbeat(
        self,
        websocket: Any,
    ) -> None:
        while True:
            await asyncio.sleep(
                self.heartbeat_interval_seconds
            )
            await websocket.send(
                json.dumps(
                    {
                        "op": "ping",
                    },
                    separators=(",", ":"),
                )
            )
    async def stream_tickers(
        self,
        *,
        symbols: list[str],
        category: str = "spot",
        max_messages: int | None = None,
    ) -> AsyncIterator[
        MarketTickerStreamEvent
    ]:
        normalized_category = (
            self.normalize_category(category)
        )
        normalized_symbols = (
            self.normalize_symbols(symbols)
        )
        if (
            max_messages is not None
            and max_messages <= 0
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "max_messages must be "
                    "greater than zero"
                ),
            )
        url = self.websocket_url(
            normalized_category
        )
        ticker_state: dict[str, dict] = {}
        emitted_messages = 0
        try:
            async with self.connect_factory(
                url,
                open_timeout=15,
                ping_interval=None,
                close_timeout=5,
                max_size=2 ** 20,
            ) as websocket:
                await self._send_subscriptions(
                    websocket=websocket,
                    category=normalized_category,
                    symbols=normalized_symbols,
                )
                heartbeat_task = asyncio.create_task(
                    self._heartbeat(websocket)
                )
                try:
                    async for raw_message in websocket:
                        message = self._decode_message(
                            raw_message
                        )
                        operation = str(
                            message.get("op") or ""
                        ).lower()
                        if operation == "subscribe":
                            if (
                                message.get("success")
                                is False
                            ):
                                error_message = str(
                                    message.get(
                                        "ret_msg"
                                    )
                                    or (
                                        "Unknown "
                                        "subscription error"
                                    )
                                )
                                raise HTTPException(
                                    status_code=(
                                        status
                                        .HTTP_502_BAD_GATEWAY
                                    ),
                                    detail=(
                                        "Bybit WebSocket "
                                        "subscription failed: "
                                        f"{error_message}"
                                    ),
                                )
                            continue
                        if (
                            operation in {
                                "ping",
                                "pong",
                            }
                            or str(
                                message.get(
                                    "ret_msg"
                                )
                                or ""
                            ).lower()
                            == "pong"
                        ):
                            continue
                        topic = str(
                            message.get("topic") or ""
                        )
                        if not topic.startswith(
                            "tickers."
                        ):
                            continue
                        message_type = str(
                            message.get("type")
                            or "snapshot"
                        ).lower()
                        if message_type not in {
                            "snapshot",
                            "delta",
                        }:
                            continue
                        raw_data = message.get("data")
                        if not isinstance(
                            raw_data,
                            dict,
                        ):
                            continue
                        topic_symbol = (
                            topic.split(".", 1)[1]
                            .strip()
                            .upper()
                        )
                        symbol = str(
                            raw_data.get("symbol")
                            or topic_symbol
                        ).strip().upper()
                        if (
                            symbol
                            not in normalized_symbols
                        ):
                            continue
                        if message_type == "snapshot":
                            merged_data = dict(
                                raw_data
                            )
                        else:
                            merged_data = dict(
                                ticker_state.get(
                                    symbol,
                                    {},
                                )
                            )
                            merged_data.update(
                                raw_data
                            )
                        merged_data["symbol"] = symbol
                        ticker_state[symbol] = (
                            merged_data
                        )
                        received_at_ms = int(
                            time.time() * 1000
                        )
                        exchange_timestamp_ms = (
                            self._to_int(
                                message.get("ts")
                            )
                        )
                        ticker = (
                            BybitMarketDataClient
                            ._normalize_ticker(
                                raw_ticker=(
                                    merged_data
                                ),
                                category=(
                                    normalized_category
                                ),
                                observed_at_ms=(
                                    exchange_timestamp_ms
                                    or received_at_ms
                                ),
                            )
                        )
                        event = (
                            MarketTickerStreamEvent(
                                category=(
                                    normalized_category
                                ),
                                topic=topic,
                                message_type=(
                                    message_type
                                ),
                                symbol=symbol,
                                sequence=self._to_int(
                                    message.get("cs")
                                ),
                                exchange_timestamp_ms=(
                                    exchange_timestamp_ms
                                ),
                                received_at_ms=(
                                    received_at_ms
                                ),
                                ticker=ticker,
                            )
                        )
                        yield event
                        emitted_messages += 1
                        if (
                            max_messages is not None
                            and emitted_messages
                            >= max_messages
                        ):
                            return
                finally:
                    heartbeat_task.cancel()
                    with suppress(
                        asyncio.CancelledError,
                        ConnectionClosed,
                        OSError,
                    ):
                        await heartbeat_task
        except HTTPException:
            raise
        except (
            ConnectionClosed,
            InvalidHandshake,
            InvalidURI,
            OSError,
        ) as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_502_BAD_GATEWAY
                ),
                detail=(
                    "Bybit WebSocket connection "
                    f"failed: {exc}"
                ),
            ) from exc
