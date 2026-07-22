from datetime import (
    UTC,
    datetime,
    timedelta,
)
from math import (
    sqrt,
)
import pytest
from app.schemas.trading_bot_strategy import (
    TradingBotMarketSample,
)
from app.services.trading_bot_indicator_service import (
    TradingBotIndicatorService,
)
NOW = datetime(
    2026,
    7,
    21,
    20,
    0,
    tzinfo=UTC,
)
def sample(
    *,
    index,
    open_price,
    high_price,
    low_price,
    close_price,
):
    return TradingBotMarketSample(
        observed_at=(
            NOW
            + timedelta(minutes=index)
        ),
        open_price=open_price,
        high_price=high_price,
        low_price=low_price,
        close_price=close_price,
        source="CANDLE",
    )
def test_simple_moving_average():
    result = (
        TradingBotIndicatorService
        .simple_moving_average(
            [1, 2, 3, 4],
            3,
        )
    )
    assert result == pytest.approx(3)
def test_exponential_moving_average():
    result = (
        TradingBotIndicatorService
        .exponential_moving_average(
            [1, 2, 3, 4],
            3,
        )
    )
    assert result == pytest.approx(3)
def test_standard_deviation_and_z_score():
    deviation = (
        TradingBotIndicatorService
        .standard_deviation(
            [1, 2, 3],
            3,
        )
    )
    assert deviation == pytest.approx(
        sqrt(2 / 3)
    )
    score = (
        TradingBotIndicatorService
        .z_score(
            [1, 2, 3],
            3,
        )
    )
    assert score == pytest.approx(
        1 / sqrt(2 / 3)
    )
def test_percentage_change():
    result = (
        TradingBotIndicatorService
        .percentage_change(
            [100, 102, 105],
            2,
        )
    )
    assert result == pytest.approx(5)
def test_rsi_for_rising_market():
    result = (
        TradingBotIndicatorService
        .relative_strength_index(
            [1, 2, 3, 4],
            3,
        )
    )
    assert result == 100
def test_rsi_for_falling_and_flat_market():
    falling = (
        TradingBotIndicatorService
        .relative_strength_index(
            [4, 3, 2, 1],
            3,
        )
    )
    flat = (
        TradingBotIndicatorService
        .relative_strength_index(
            [2, 2, 2, 2],
            3,
        )
    )
    assert falling == 0
    assert flat == 50
def test_average_true_range():
    samples = [
        sample(
            index=0,
            open_price=100,
            high_price=102,
            low_price=99,
            close_price=101,
        ),
        sample(
            index=1,
            open_price=101,
            high_price=104,
            low_price=100,
            close_price=103,
        ),
        sample(
            index=2,
            open_price=103,
            high_price=105,
            low_price=102,
            close_price=104,
        ),
    ]
    result = (
        TradingBotIndicatorService
        .average_true_range(
            samples,
            2,
        )
    )
    assert result == pytest.approx(3.5)
def test_indicators_return_none_for_warmup():
    service = (
        TradingBotIndicatorService
    )
    assert (
        service.simple_moving_average(
            [1, 2],
            3,
        )
        is None
    )
    assert (
        service.relative_strength_index(
            [1, 2, 3],
            3,
        )
        is None
    )
    assert (
        service.average_true_range(
            [],
            3,
        )
        is None
    )
def test_indicators_reject_invalid_period():
    service = (
        TradingBotIndicatorService
    )
    for period in [
        0,
        -1,
        1.5,
        True,
    ]:
        with pytest.raises(
            ValueError,
            match="period",
        ):
            service.simple_moving_average(
                [1, 2, 3],
                period,
            )
