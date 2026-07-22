from collections import (
    deque,
)
from datetime import (
    UTC,
    datetime,
)
from threading import (
    RLock,
)
from app.schemas.market_scanner import (
    MarketTickerSnapshot,
)
from app.schemas.trading_bot_strategy import (
    TradingBotMarketSample,
)
class TradingBotRuntimeMarketHistoryService:
    DEFAULT_MAX_SAMPLES = 500
    def __init__(
        self,
        *,
        max_samples: int = (
            DEFAULT_MAX_SAMPLES
        ),
    ):
        if (
            isinstance(
                max_samples,
                bool,
            )
            or not isinstance(
                max_samples,
                int,
            )
            or max_samples <= 0
            or max_samples > 500
        ):
            raise ValueError(
                "max_samples must be an "
                "integer between 1 and 500"
            )
        self.max_samples = max_samples
        self._history: dict[
            tuple[
                int,
                int,
                str,
                str,
                str,
            ],
            deque[
                TradingBotMarketSample
            ],
        ] = {}
        self._lock = RLock()
    @staticmethod
    def _key(
        bot,
    ) -> tuple[
        int,
        int,
        str,
        str,
        str,
    ]:
        return (
            int(bot.user_id),
            int(bot.id),
            str(bot.symbol)
            .strip()
            .upper(),
            str(bot.category)
            .strip()
            .lower(),
            str(bot.timeframe)
            .strip()
            .lower(),
        )
    @staticmethod
    def _timestamp(
        value: datetime,
    ) -> datetime:
        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise ValueError(
                "Runtime market-history "
                "timestamps must include "
                "a timezone"
            )
        return value.astimezone(UTC)
    @staticmethod
    def _sample(
        *,
        ticker: MarketTickerSnapshot,
        observed_at: datetime,
    ) -> TradingBotMarketSample:
        price = float(
            ticker.last_price
        )
        if price <= 0:
            raise ValueError(
                "Runtime market history "
                "requires a positive price"
            )
        bid_price = (
            float(ticker.bid_price)
            if ticker.bid_price > 0
            else price
        )
        ask_price = (
            float(ticker.ask_price)
            if ticker.ask_price > 0
            else price
        )
        if ask_price < bid_price:
            bid_price = price
            ask_price = price
        return TradingBotMarketSample(
            observed_at=observed_at,
            open_price=price,
            high_price=price,
            low_price=price,
            close_price=price,
            bid_price=bid_price,
            ask_price=ask_price,
            volume=max(
                float(ticker.volume_24h),
                0.0,
            ),
            turnover_usd=max(
                float(ticker.turnover_24h),
                0.0,
            ),
            source="TICKER",
        )
    def append_ticker(
        self,
        *,
        bot,
        ticker: MarketTickerSnapshot,
        observed_at: datetime,
    ) -> list[
        TradingBotMarketSample
    ]:
        timestamp = self._timestamp(
            observed_at
        )
        sample = self._sample(
            ticker=ticker,
            observed_at=timestamp,
        )
        key = self._key(bot)
        with self._lock:
            history = self._history.get(
                key
            )
            if history is None:
                history = deque(
                    maxlen=self.max_samples
                )
                self._history[key] = (
                    history
                )
            if history:
                latest = history[-1]
                if (
                    sample.observed_at
                    < latest.observed_at
                ):
                    raise ValueError(
                        "Runtime market history "
                        "cannot move backwards"
                    )
                if (
                    sample.observed_at
                    == latest.observed_at
                ):
                    history[-1] = sample
                    return list(history)
            history.append(sample)
            return list(history)
    def get(
        self,
        *,
        bot,
    ) -> list[
        TradingBotMarketSample
    ]:
        key = self._key(bot)
        with self._lock:
            history = self._history.get(
                key
            )
            return (
                list(history)
                if history is not None
                else []
            )
    def clear(
        self,
        *,
        bot,
    ) -> bool:
        key = self._key(bot)
        with self._lock:
            return (
                self._history.pop(
                    key,
                    None,
                )
                is not None
            )
