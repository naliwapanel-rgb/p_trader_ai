from decimal import Decimal
import pytest
from pydantic import ValidationError
from app.schemas.arbitrage import (
    ArbitrageMarketQuote,
    CrossExchangeScanRequest,
)
from app.services.cross_exchange_arbitrage_service import (
    CrossExchangeArbitrageService,
)
D = Decimal
def build_quote(
    *,
    exchange: str,
    symbol: str = "BTCUSDT",
    base_asset: str = "BTC",
    quote_asset: str = "USDT",
    bid_price: str,
    ask_price: str,
    bid_size: str = "1",
    ask_size: str = "1",
    fee_rate_percent: str = "0",
    slippage_percent: str = "0",
    fixed_buy_cost: str = "0",
    fixed_sell_cost: str = "0",
    observed_at_ms: int = 1000,
) -> ArbitrageMarketQuote:
    return ArbitrageMarketQuote(
        exchange=exchange,
        symbol=symbol,
        base_asset=base_asset,
        quote_asset=quote_asset,
        bid_price=D(bid_price),
        ask_price=D(ask_price),
        bid_size=D(bid_size),
        ask_size=D(ask_size),
        fee_rate_percent=D(
            fee_rate_percent
        ),
        slippage_percent=D(
            slippage_percent
        ),
        fixed_buy_cost=D(
            fixed_buy_cost
        ),
        fixed_sell_cost=D(
            fixed_sell_cost
        ),
        observed_at_ms=observed_at_ms,
    )
def test_detects_profitable_cross_exchange_route():
    request = CrossExchangeScanRequest(
        starting_amount=D("1000"),
        minimum_profit_percent=D("1"),
        quotes=[
            build_quote(
                exchange="BYBIT",
                bid_price="49990",
                ask_price="50000",
            ),
            build_quote(
                exchange="BINANCE",
                bid_price="51000",
                ask_price="51010",
            ),
        ],
    )
    result = (
        CrossExchangeArbitrageService(
            clock_ms=lambda: 1000
        ).scan(request)
    )
    assert result.total_quotes == 2
    assert result.total_pairs == 1
    assert result.total_routes_evaluated == 2
    assert result.profitable_count == 1
    assert result.matched_count == 1
    assert result.returned_count == 1
    opportunity = result.opportunities[0]
    assert opportunity.buy_exchange == "BYBIT"
    assert (
        opportunity.sell_exchange
        == "BINANCE"
    )
    assert (
        opportunity.gross_spread_percent
        == D("2")
    )
    assert (
        opportunity
        .evaluation
        .net_profit_amount
        == D("20")
    )
    assert (
        opportunity
        .evaluation
        .net_profit_percent
        == D("2")
    )
def test_costs_remove_unprofitable_route():
    request = CrossExchangeScanRequest(
        starting_amount=D("1000"),
        quotes=[
            build_quote(
                exchange="BYBIT",
                bid_price="49990",
                ask_price="50000",
                fee_rate_percent="0.1",
                slippage_percent="0.2",
            ),
            build_quote(
                exchange="BINANCE",
                bid_price="50200",
                ask_price="50210",
                fee_rate_percent="0.1",
                slippage_percent="0.2",
            ),
        ],
    )
    result = (
        CrossExchangeArbitrageService(
            clock_ms=lambda: 1000
        ).scan(request)
    )
    assert result.total_routes_evaluated == 2
    assert result.profitable_count == 0
    assert result.matched_count == 0
    assert result.opportunities == []
def test_same_exchange_quotes_are_ignored():
    request = CrossExchangeScanRequest(
        starting_amount=D("1000"),
        quotes=[
            build_quote(
                exchange="BYBIT",
                symbol="BTCUSDT-A",
                bid_price="49990",
                ask_price="50000",
            ),
            build_quote(
                exchange="BYBIT",
                symbol="BTCUSDT-B",
                bid_price="51000",
                ask_price="51010",
            ),
        ],
    )
    result = (
        CrossExchangeArbitrageService(
            clock_ms=lambda: 1000
        ).scan(request)
    )
    assert result.total_pairs == 0
    assert result.total_routes_evaluated == 0
    assert result.opportunities == []
def test_full_liquidity_requirement_skips_route():
    request = CrossExchangeScanRequest(
        starting_amount=D("1000"),
        require_full_liquidity=True,
        quotes=[
            build_quote(
                exchange="BYBIT",
                bid_price="49990",
                ask_price="50000",
                ask_size="0.01",
            ),
            build_quote(
                exchange="BINANCE",
                bid_price="51000",
                ask_price="51010",
                bid_size="1",
            ),
        ],
    )
    result = (
        CrossExchangeArbitrageService(
            clock_ms=lambda: 1000
        ).scan(request)
    )
    assert result.total_routes_evaluated == 1
    assert result.matched_count == 0
def test_partial_liquidity_caps_starting_amount():
    request = CrossExchangeScanRequest(
        starting_amount=D("1000"),
        require_full_liquidity=False,
        quotes=[
            build_quote(
                exchange="BYBIT",
                bid_price="49990",
                ask_price="50000",
                ask_size="0.01",
            ),
            build_quote(
                exchange="BINANCE",
                bid_price="51000",
                ask_price="51010",
                bid_size="1",
            ),
        ],
    )
    result = (
        CrossExchangeArbitrageService(
            clock_ms=lambda: 1000
        ).scan(request)
    )
    opportunity = result.opportunities[0]
    assert (
        opportunity
        .maximum_starting_amount_by_liquidity
        == D("500.00")
    )
    assert (
        opportunity.evaluated_starting_amount
        == D("500.00")
    )
    assert opportunity.fully_liquid is False
    assert (
        opportunity
        .evaluation
        .net_profit_amount
        == D("10.00")
    )
def test_stale_quotes_are_excluded():
    request = CrossExchangeScanRequest(
        starting_amount=D("1000"),
        maximum_quote_age_ms=500,
        quotes=[
            build_quote(
                exchange="BYBIT",
                bid_price="49990",
                ask_price="50000",
                observed_at_ms=1000,
            ),
            build_quote(
                exchange="BINANCE",
                bid_price="51000",
                ask_price="51010",
                observed_at_ms=1900,
            ),
        ],
    )
    result = (
        CrossExchangeArbitrageService(
            clock_ms=lambda: 2000
        ).scan(request)
    )
    assert result.total_pairs == 0
    assert result.total_routes_evaluated == 0
def test_quote_time_skew_limit_is_enforced():
    request = CrossExchangeScanRequest(
        starting_amount=D("1000"),
        maximum_time_skew_ms=500,
        quotes=[
            build_quote(
                exchange="BYBIT",
                bid_price="49990",
                ask_price="50000",
                observed_at_ms=1000,
            ),
            build_quote(
                exchange="BINANCE",
                bid_price="51000",
                ask_price="51010",
                observed_at_ms=2000,
            ),
        ],
    )
    result = (
        CrossExchangeArbitrageService(
            clock_ms=lambda: 2000
        ).scan(request)
    )
    assert result.total_pairs == 1
    assert result.total_routes_evaluated == 0
    assert result.opportunities == []
def test_assets_group_quotes_with_different_symbols():
    request = CrossExchangeScanRequest(
        starting_amount=D("1000"),
        quotes=[
            build_quote(
                exchange=" bybit ",
                symbol=" btcusdt ",
                bid_price="49990",
                ask_price="50000",
            ),
            build_quote(
                exchange=" binance ",
                symbol=" btc-usdt ",
                bid_price="51000",
                ask_price="51010",
            ),
        ],
    )
    result = (
        CrossExchangeArbitrageService(
            clock_ms=lambda: 1000
        ).scan(request)
    )
    opportunity = result.opportunities[0]
    assert opportunity.buy_symbol == "BTCUSDT"
    assert opportunity.sell_symbol == "BTC-USDT"
def test_ranking_and_limit_are_deterministic():
    quotes = [
        build_quote(
            exchange="BYBIT",
            symbol="BTCUSDT",
            base_asset="BTC",
            bid_price="49990",
            ask_price="50000",
        ),
        build_quote(
            exchange="BINANCE",
            symbol="BTCUSDT",
            base_asset="BTC",
            bid_price="51000",
            ask_price="51010",
        ),
        build_quote(
            exchange="BYBIT",
            symbol="ETHUSDT",
            base_asset="ETH",
            bid_price="2490",
            ask_price="2500",
        ),
        build_quote(
            exchange="BINANCE",
            symbol="ETHUSDT",
            base_asset="ETH",
            bid_price="2600",
            ask_price="2610",
        ),
    ]
    request = CrossExchangeScanRequest(
        starting_amount=D("1000"),
        sort_by="net_profit_percent",
        descending=True,
        limit=1,
        quotes=quotes,
    )
    result = (
        CrossExchangeArbitrageService(
            clock_ms=lambda: 1000
        ).scan(request)
    )
    assert result.matched_count == 2
    assert result.returned_count == 1
    assert (
        result.opportunities[0].base_asset
        == "ETH"
    )
    assert (
        result.opportunities[0]
        .evaluation
        .net_profit_percent
        == D("4")
    )
def test_quote_rejects_crossed_local_market():
    with pytest.raises(
        ValidationError
    ) as exc_info:
        build_quote(
            exchange="BYBIT",
            bid_price="51000",
            ask_price="50000",
        )
    assert (
        "ask_price cannot be below bid_price"
        in str(exc_info.value)
    )
