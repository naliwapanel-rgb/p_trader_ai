from collections.abc import (
    Sequence,
)
from math import (
    isfinite,
    sqrt,
)
from app.schemas.trading_bot_strategy import (
    TradingBotMarketSample,
)
class TradingBotIndicatorService:
    @staticmethod
    def _period(
        period: int,
    ) -> int:
        if isinstance(period, bool):
            raise ValueError(
                "Indicator period must be "
                "a positive integer"
            )
        if not isinstance(period, int):
            raise ValueError(
                "Indicator period must be "
                "a positive integer"
            )
        if period <= 0:
            raise ValueError(
                "Indicator period must be "
                "greater than zero"
            )
        return period
    @staticmethod
    def _prices(
        values: Sequence[
            float
        ],
    ) -> list[float]:
        normalized = []
        for value in values:
            price = float(value)
            if (
                not isfinite(price)
                or price <= 0
            ):
                raise ValueError(
                    "Indicator prices must be "
                    "finite and greater than zero"
                )
            normalized.append(price)
        return normalized
    @classmethod
    def simple_moving_average(
        cls,
        values: Sequence[float],
        period: int,
    ) -> float | None:
        period = cls._period(period)
        prices = cls._prices(values)
        if len(prices) < period:
            return None
        window = prices[-period:]
        return sum(window) / period
    @classmethod
    def exponential_moving_average(
        cls,
        values: Sequence[float],
        period: int,
    ) -> float | None:
        period = cls._period(period)
        prices = cls._prices(values)
        if len(prices) < period:
            return None
        average = (
            sum(prices[:period])
            / period
        )
        multiplier = (
            2.0
            / (
                period
                + 1
            )
        )
        for price in prices[period:]:
            average = (
                (
                    price
                    - average
                )
                * multiplier
                + average
            )
        return average
    @classmethod
    def standard_deviation(
        cls,
        values: Sequence[float],
        period: int,
    ) -> float | None:
        period = cls._period(period)
        prices = cls._prices(values)
        if len(prices) < period:
            return None
        window = prices[-period:]
        mean = sum(window) / period
        variance = (
            sum(
                (
                    value
                    - mean
                )
                ** 2
                for value in window
            )
            / period
        )
        return sqrt(variance)
    @classmethod
    def z_score(
        cls,
        values: Sequence[float],
        period: int,
    ) -> float | None:
        period = cls._period(period)
        prices = cls._prices(values)
        if len(prices) < period:
            return None
        mean = cls.simple_moving_average(
            prices,
            period,
        )
        deviation = cls.standard_deviation(
            prices,
            period,
        )
        if (
            mean is None
            or deviation is None
        ):
            return None
        if deviation == 0:
            return 0.0
        return (
            prices[-1]
            - mean
        ) / deviation
    @classmethod
    def percentage_change(
        cls,
        values: Sequence[float],
        lookback: int,
    ) -> float | None:
        lookback = cls._period(
            lookback
        )
        prices = cls._prices(values)
        if len(prices) <= lookback:
            return None
        previous = prices[
            -lookback - 1
        ]
        return (
            prices[-1]
            - previous
        ) / previous * 100
    @classmethod
    def relative_strength_index(
        cls,
        values: Sequence[float],
        period: int,
    ) -> float | None:
        period = cls._period(period)
        prices = cls._prices(values)
        if len(prices) < period + 1:
            return None
        window = prices[
            -(period + 1):
        ]
        gains = []
        losses = []
        for previous, current in zip(
            window,
            window[1:],
        ):
            change = current - previous
            gains.append(
                max(change, 0.0)
            )
            losses.append(
                max(-change, 0.0)
            )
        average_gain = (
            sum(gains)
            / period
        )
        average_loss = (
            sum(losses)
            / period
        )
        if (
            average_gain == 0
            and average_loss == 0
        ):
            return 50.0
        if average_loss == 0:
            return 100.0
        if average_gain == 0:
            return 0.0
        relative_strength = (
            average_gain
            / average_loss
        )
        return (
            100.0
            - (
                100.0
                / (
                    1.0
                    + relative_strength
                )
            )
        )
    @classmethod
    def average_true_range(
        cls,
        samples: Sequence[
            TradingBotMarketSample
        ],
        period: int,
    ) -> float | None:
        period = cls._period(period)
        if len(samples) < period + 1:
            return None
        true_ranges = []
        start = len(samples) - period
        for index in range(
            start,
            len(samples),
        ):
            current = samples[index]
            previous_close = (
                samples[
                    index - 1
                ].close_price
            )
            true_range = max(
                (
                    current.high_price
                    - current.low_price
                ),
                abs(
                    current.high_price
                    - previous_close
                ),
                abs(
                    current.low_price
                    - previous_close
                ),
            )
            true_ranges.append(
                true_range
            )
        return (
            sum(true_ranges)
            / period
        )
