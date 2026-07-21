from datetime import (
    UTC,
    datetime,
    timedelta,
    timezone,
)
import pytest
from pydantic import (
    ValidationError,
)
from app.schemas.trading_bot_backtest import (
    HistoricalMarketCandle,
    TradingBotBacktestRequest,
)
BASE_TIME = datetime(
    2026,
    7,
    1,
    0,
    0,
    tzinfo=UTC,
)
def build_candle(
    *,
    opened_at=BASE_TIME,
    closed_at=None,
    open_price=100,
    high_price=105,
    low_price=95,
    close_price=102,
):
    return HistoricalMarketCandle(
        opened_at=opened_at,
        closed_at=(
            closed_at
            or (
                opened_at
                + timedelta(hours=1)
            )
        ),
        open_price=open_price,
        high_price=high_price,
        low_price=low_price,
        close_price=close_price,
        volume=10,
        turnover_usd=1000,
    )
def test_candle_normalizes_timestamps():
    local_timezone = timezone(
        timedelta(hours=2)
    )
    opened_at = datetime(
        2026,
        7,
        1,
        2,
        0,
        tzinfo=local_timezone,
    )
    candle = build_candle(
        opened_at=opened_at,
        closed_at=(
            opened_at
            + timedelta(hours=1)
        ),
    )
    assert candle.opened_at == BASE_TIME
    assert candle.closed_at == (
        BASE_TIME
        + timedelta(hours=1)
    )
def test_candle_rejects_invalid_high():
    with pytest.raises(
        ValidationError,
        match="high_price",
    ):
        build_candle(
            high_price=101,
            close_price=102,
        )
def test_candle_rejects_invalid_low():
    with pytest.raises(
        ValidationError,
        match="low_price",
    ):
        build_candle(
            low_price=101,
            open_price=100,
        )
def test_candle_rejects_invalid_time_range():
    with pytest.raises(
        ValidationError,
        match="closed_at",
    ):
        build_candle(
            opened_at=BASE_TIME,
            closed_at=BASE_TIME,
        )
def test_candle_rejects_naive_timestamp():
    with pytest.raises(
        ValidationError,
        match="timezone",
    ):
        build_candle(
            opened_at=datetime(
                2026,
                7,
                1,
            ),
        )
def test_request_requires_two_candles():
    with pytest.raises(
        ValidationError,
    ):
        TradingBotBacktestRequest(
            candles=[
                build_candle()
            ]
        )
def test_request_rejects_unordered_candles():
    later = build_candle(
        opened_at=(
            BASE_TIME
            + timedelta(hours=2)
        )
    )
    earlier = build_candle(
        opened_at=BASE_TIME
    )
    with pytest.raises(
        ValidationError,
        match="chronologically",
    ):
        TradingBotBacktestRequest(
            candles=[
                later,
                earlier,
            ]
        )
def test_request_rejects_overlapping_candles():
    first = build_candle(
        opened_at=BASE_TIME,
        closed_at=(
            BASE_TIME
            + timedelta(hours=2)
        ),
    )
    second = build_candle(
        opened_at=(
            BASE_TIME
            + timedelta(hours=1)
        ),
        closed_at=(
            BASE_TIME
            + timedelta(hours=3)
        ),
    )
    with pytest.raises(
        ValidationError,
        match="overlap",
    ):
        TradingBotBacktestRequest(
            candles=[
                first,
                second,
            ]
        )
def test_request_defaults_and_extra_safety():
    request = TradingBotBacktestRequest(
        candles=[
            build_candle(),
            build_candle(
                opened_at=(
                    BASE_TIME
                    + timedelta(hours=1)
                ),
            ),
        ]
    )
    assert (
        request.initial_balance_usd
        == 10000
    )
    assert request.fee_rate == 0.0006
    assert request.slippage_rate == 0.0001
    assert request.force_close_at_end is True
    with pytest.raises(
        ValidationError,
    ):
        TradingBotBacktestRequest(
            candles=request.candles,
            unknown_setting=True,
        )
