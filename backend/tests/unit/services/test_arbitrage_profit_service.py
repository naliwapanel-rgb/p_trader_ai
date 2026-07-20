from decimal import Decimal
import pytest
from pydantic import ValidationError
from app.schemas.arbitrage import (
    ArbitrageEvaluationRequest,
    ArbitrageLegRequest,
)
from app.services.arbitrage_profit_service import (
    ArbitrageProfitService,
)
D = Decimal
def build_leg(
    *,
    exchange: str,
    symbol: str,
    base_asset: str,
    quote_asset: str,
    side: str,
    price: str,
    fee_rate_percent: str = "0",
    slippage_percent: str = "0",
    fixed_cost: str = "0",
) -> ArbitrageLegRequest:
    return ArbitrageLegRequest(
        exchange=exchange,
        symbol=symbol,
        base_asset=base_asset,
        quote_asset=quote_asset,
        side=side,
        price=D(price),
        fee_rate_percent=D(
            fee_rate_percent
        ),
        slippage_percent=D(
            slippage_percent
        ),
        fixed_cost=D(fixed_cost),
    )
def test_cross_exchange_route_is_profitable():
    request = ArbitrageEvaluationRequest(
        opportunity_type="CROSS_EXCHANGE",
        starting_asset="USDT",
        starting_amount=D("1000"),
        minimum_profit_percent=D("1"),
        legs=[
            build_leg(
                exchange="BYBIT",
                symbol="BTCUSDT",
                base_asset="BTC",
                quote_asset="USDT",
                side="BUY",
                price="50000",
            ),
            build_leg(
                exchange="BINANCE",
                symbol="BTCUSDT",
                base_asset="BTC",
                quote_asset="USDT",
                side="SELL",
                price="51000",
            ),
        ],
    )
    result = (
        ArbitrageProfitService.evaluate(
            request
        )
    )
    assert result.gross_ending_amount == (
        D("1020")
    )
    assert result.net_ending_amount == (
        D("1020")
    )
    assert result.net_profit_amount == D("20")
    assert result.net_profit_percent == D("2")
    assert result.profitable is True
    assert (
        result.meets_minimum_profit
        is True
    )
    assert result.executable is True
def test_costs_can_turn_gross_profit_negative():
    request = ArbitrageEvaluationRequest(
        opportunity_type="CROSS_EXCHANGE",
        starting_asset="USDT",
        starting_amount=D("1000"),
        legs=[
            build_leg(
                exchange="BYBIT",
                symbol="BTCUSDT",
                base_asset="BTC",
                quote_asset="USDT",
                side="BUY",
                price="50000",
                fee_rate_percent="0.1",
                slippage_percent="0.2",
            ),
            build_leg(
                exchange="BINANCE",
                symbol="BTCUSDT",
                base_asset="BTC",
                quote_asset="USDT",
                side="SELL",
                price="50200",
                fee_rate_percent="0.1",
                slippage_percent="0.2",
            ),
        ],
    )
    result = (
        ArbitrageProfitService.evaluate(
            request
        )
    )
    assert result.gross_profit_amount == D("4")
    assert result.net_profit_amount < 0
    assert result.total_cost_impact > 0
    assert result.profitable is False
    assert result.executable is False
def test_triangular_route_is_evaluated():
    request = ArbitrageEvaluationRequest(
        opportunity_type="TRIANGULAR",
        starting_asset="USDT",
        starting_amount=D("1000"),
        minimum_profit_percent=D("3"),
        legs=[
            build_leg(
                exchange="BYBIT",
                symbol="BTCUSDT",
                base_asset="BTC",
                quote_asset="USDT",
                side="BUY",
                price="50000",
            ),
            build_leg(
                exchange="BYBIT",
                symbol="BTCETH",
                base_asset="BTC",
                quote_asset="ETH",
                side="SELL",
                price="20",
            ),
            build_leg(
                exchange="BYBIT",
                symbol="ETHUSDT",
                base_asset="ETH",
                quote_asset="USDT",
                side="SELL",
                price="2600",
            ),
        ],
    )
    result = (
        ArbitrageProfitService.evaluate(
            request
        )
    )
    assert result.ending_asset == "USDT"
    assert result.gross_ending_amount == (
        D("1040")
    )
    assert result.net_profit_amount == D("40")
    assert result.net_profit_percent == D("4")
    assert result.executable is True
def test_fixed_costs_are_compounded():
    request = ArbitrageEvaluationRequest(
        opportunity_type="CROSS_EXCHANGE",
        starting_asset="USDT",
        starting_amount=D("1000"),
        legs=[
            build_leg(
                exchange="BYBIT",
                symbol="BTCUSDT",
                base_asset="BTC",
                quote_asset="USDT",
                side="BUY",
                price="50000",
                fixed_cost="0.0001",
            ),
            build_leg(
                exchange="BINANCE",
                symbol="BTCUSDT",
                base_asset="BTC",
                quote_asset="USDT",
                side="SELL",
                price="51000",
                fixed_cost="1",
            ),
        ],
    )
    result = (
        ArbitrageProfitService.evaluate(
            request
        )
    )
    assert result.gross_ending_amount == (
        D("1020")
    )
    assert result.net_ending_amount == (
        D("1013.9000")
    )
    assert result.total_cost_impact == (
        D("6.1000")
    )
def test_identifiers_are_normalized():
    request = ArbitrageEvaluationRequest(
        opportunity_type="CROSS_EXCHANGE",
        starting_asset=" usdt ",
        starting_amount=D("1000"),
        legs=[
            build_leg(
                exchange=" bybit ",
                symbol=" btcusdt ",
                base_asset=" btc ",
                quote_asset=" usdt ",
                side="BUY",
                price="50000",
            ),
            build_leg(
                exchange=" binance ",
                symbol=" btcusdt ",
                base_asset=" btc ",
                quote_asset=" usdt ",
                side="SELL",
                price="51000",
            ),
        ],
    )
    assert request.starting_asset == "USDT"
    assert request.legs[0].exchange == "BYBIT"
    assert request.legs[0].symbol == "BTCUSDT"
    assert request.legs[0].base_asset == "BTC"
    assert request.legs[0].quote_asset == "USDT"
def test_route_rejects_asset_chain_mismatch():
    with pytest.raises(
        ValidationError
    ) as exc_info:
        ArbitrageEvaluationRequest(
            opportunity_type="CROSS_EXCHANGE",
            starting_asset="USDT",
            starting_amount=D("1000"),
            legs=[
                build_leg(
                    exchange="BYBIT",
                    symbol="BTCUSDT",
                    base_asset="BTC",
                    quote_asset="USDT",
                    side="SELL",
                    price="50000",
                ),
                build_leg(
                    exchange="BINANCE",
                    symbol="BTCUSDT",
                    base_asset="BTC",
                    quote_asset="USDT",
                    side="SELL",
                    price="51000",
                ),
            ],
        )
    assert (
        "leg 1 requires BTC"
        in str(exc_info.value)
    )
def test_route_must_finish_in_starting_asset():
    with pytest.raises(
        ValidationError
    ) as exc_info:
        ArbitrageEvaluationRequest(
            opportunity_type="CUSTOM",
            starting_asset="USDT",
            starting_amount=D("1000"),
            legs=[
                build_leg(
                    exchange="BYBIT",
                    symbol="BTCUSDT",
                    base_asset="BTC",
                    quote_asset="USDT",
                    side="BUY",
                    price="50000",
                ),
                build_leg(
                    exchange="BYBIT",
                    symbol="BTCETH",
                    base_asset="BTC",
                    quote_asset="ETH",
                    side="SELL",
                    price="20",
                ),
            ],
        )
    assert (
        "must finish in the starting asset"
        in str(exc_info.value)
    )
def test_triangular_route_requires_three_legs():
    legs = [
        build_leg(
            exchange="BYBIT",
            symbol="BTCUSDT",
            base_asset="BTC",
            quote_asset="USDT",
            side="BUY",
            price="50000",
        ),
        build_leg(
            exchange="BYBIT",
            symbol="BTCUSDT",
            base_asset="BTC",
            quote_asset="USDT",
            side="SELL",
            price="51000",
        ),
    ]
    with pytest.raises(
        ValidationError
    ) as exc_info:
        ArbitrageEvaluationRequest(
            opportunity_type="TRIANGULAR",
            starting_asset="USDT",
            starting_amount=D("1000"),
            legs=legs,
        )
    assert (
        "must contain exactly three legs"
        in str(exc_info.value)
    )
def test_cross_exchange_requires_two_legs():
    legs = [
        build_leg(
            exchange="BYBIT",
            symbol="BTCUSDT",
            base_asset="BTC",
            quote_asset="USDT",
            side="BUY",
            price="50000",
        ),
        build_leg(
            exchange="BINANCE",
            symbol="BTCETH",
            base_asset="BTC",
            quote_asset="ETH",
            side="SELL",
            price="20",
        ),
        build_leg(
            exchange="BINANCE",
            symbol="ETHUSDT",
            base_asset="ETH",
            quote_asset="USDT",
            side="SELL",
            price="2600",
        ),
    ]
    with pytest.raises(
        ValidationError
    ) as exc_info:
        ArbitrageEvaluationRequest(
            opportunity_type=(
                "CROSS_EXCHANGE"
            ),
            starting_asset="USDT",
            starting_amount=D("1000"),
            legs=legs,
        )
    assert (
        "must contain exactly two legs"
        in str(exc_info.value)
    )
def test_leg_rejects_costs_that_consume_output():
    request = ArbitrageEvaluationRequest(
        opportunity_type="CROSS_EXCHANGE",
        starting_asset="USDT",
        starting_amount=D("10"),
        legs=[
            build_leg(
                exchange="BYBIT",
                symbol="BTCUSDT",
                base_asset="BTC",
                quote_asset="USDT",
                side="BUY",
                price="50000",
                fixed_cost="1",
            ),
            build_leg(
                exchange="BINANCE",
                symbol="BTCUSDT",
                base_asset="BTC",
                quote_asset="USDT",
                side="SELL",
                price="51000",
            ),
        ],
    )
    with pytest.raises(
        ValueError
    ) as exc_info:
        ArbitrageProfitService.evaluate(
            request
        )
    assert (
        "costs consume the entire output"
        in str(exc_info.value)
    )
