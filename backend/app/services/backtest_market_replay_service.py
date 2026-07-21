from datetime import (
    timedelta,
)
from app.schemas.market_scanner import (
    MarketTickerSnapshot,
)
from app.schemas.trading_bot_backtest import (
    BacktestMarketFrame,
    HistoricalMarketCandle,
    TradingBotBacktestRequest,
)
class BacktestMarketReplayService:
    LOOKBACK = timedelta(
        hours=24
    )
    @staticmethod
    def _effective_turnover(
        candle: HistoricalMarketCandle,
    ) -> float:
        if candle.turnover_usd > 0:
            return candle.turnover_usd
        return (
            candle.close_price
            * candle.volume
        )
    @classmethod
    def _previous_price_24h(
        cls,
        *,
        candles: list[
            HistoricalMarketCandle
        ],
        current_index: int,
    ) -> float:
        current = candles[
            current_index
        ]
        cutoff = (
            current.closed_at
            - cls.LOOKBACK
        )
        for previous in reversed(
            candles[
                : current_index + 1
            ]
        ):
            if (
                previous.closed_at
                <= cutoff
            ):
                return (
                    previous.close_price
                )
        return 0.0
    @classmethod
    def _rolling_window(
        cls,
        *,
        candles: list[
            HistoricalMarketCandle
        ],
        current_index: int,
    ) -> list[
        HistoricalMarketCandle
    ]:
        current = candles[
            current_index
        ]
        cutoff = (
            current.closed_at
            - cls.LOOKBACK
        )
        return [
            candle
            for candle in candles[
                : current_index + 1
            ]
            if candle.closed_at > cutoff
        ]
    @classmethod
    def _build_ticker(
        cls,
        *,
        bot,
        data: TradingBotBacktestRequest,
        current_index: int,
    ) -> tuple[
        MarketTickerSnapshot,
        bool,
    ]:
        candle = data.candles[
            current_index
        ]
        previous_price = (
            cls._previous_price_24h(
                candles=data.candles,
                current_index=(
                    current_index
                ),
            )
        )
        rolling = cls._rolling_window(
            candles=data.candles,
            current_index=current_index,
        )
        price_change = (
            candle.close_price
            - previous_price
            if previous_price > 0
            else 0.0
        )
        change_percent = (
            price_change
            / previous_price
            * 100
            if previous_price > 0
            else 0.0
        )
        volume_24h = sum(
            item.volume
            for item in rolling
        )
        turnover_24h = sum(
            cls._effective_turnover(
                item
            )
            for item in rolling
        )
        ticker = MarketTickerSnapshot(
            exchange="BACKTEST",
            category=bot.category,
            symbol=(
                str(bot.symbol)
                .strip()
                .upper()
            ),
            last_price=(
                candle.close_price
            ),
            bid_price=(
                candle.close_price
            ),
            bid_size=(
                candle.volume / 2
            ),
            ask_price=(
                candle.close_price
            ),
            ask_size=(
                candle.volume / 2
            ),
            spread=0.0,
            spread_percent=0.0,
            previous_price_24h=(
                previous_price
            ),
            price_change_24h=(
                price_change
            ),
            price_change_percent_24h=(
                change_percent
            ),
            high_24h=max(
                item.high_price
                for item in rolling
            ),
            low_24h=min(
                item.low_price
                for item in rolling
            ),
            volume_24h=volume_24h,
            turnover_24h=turnover_24h,
            index_price=(
                candle.close_price
            ),
            mark_price=(
                candle.close_price
            ),
            usd_index_price=(
                candle.close_price
            ),
            observed_at_ms=int(
                candle.closed_at
                .timestamp()
                * 1000
            ),
        )
        return (
            ticker,
            previous_price > 0,
        )
    @classmethod
    def build_frames(
        cls,
        *,
        bot,
        data: TradingBotBacktestRequest,
    ) -> list[BacktestMarketFrame]:
        frames = []
        for index, candle in enumerate(
            data.candles
        ):
            ticker, warmup_complete = (
                cls._build_ticker(
                    bot=bot,
                    data=data,
                    current_index=index,
                )
            )
            frames.append(
                BacktestMarketFrame(
                    sequence=index + 1,
                    candle=candle,
                    ticker=ticker,
                    warmup_complete=(
                        warmup_complete
                    ),
                )
            )
        return frames
