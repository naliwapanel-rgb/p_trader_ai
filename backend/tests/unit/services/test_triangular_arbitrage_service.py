from decimal import Decimal
from app.schemas.arbitrage import (
    ArbitrageMarketQuote,
    TriangularScanRequest,
)
from app.services.triangular_arbitrage_service import (
    TriangularArbitrageService,
)
D = Decimal
def build_quote(
    *,
    exchange: str = "BYBIT",
    symbol: str,
    base_asset: str,
    quote_asset: str,
    bid_price: str,
    ask_price: str,
    bid_size: str = "100",
    ask_size: str = "100",
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
def build_profitable_triangle(
    *,
    fee_rate_percent: str = "0",
    slippage_percent: str = "0",
    btc_ask_size: str = "1",
):
    return [
        build_quote(
            symbol="BTCUSDT",
            base_asset="BTC",
            quote_asset="USDT",
            bid_price="49990",
            ask_price="50000",
            bid_size="1",
            ask_size=btc_ask_size,
            fee_rate_percent=(
                fee_rate_percent
            ),
            slippage_percent=(
                slippage_percent
            ),
        ),
        build_quote(
            symbol="BTCETH",
            base_asset="BTC",
            quote_asset="ETH",
            bid_price="20",
            ask_price="20.1",
            bid_size="1",
            ask_size="1",
            fee_rate_percent=(
                fee_rate_percent
            ),
            slippage_percent=(
                slippage_percent
            ),
        ),
        build_quote(
            symbol="ETHUSDT",
            base_asset="ETH",
            quote_asset="USDT",
            bid_price="2600",
            ask_price="2601",
            bid_size="100",
            ask_size="100",
            fee_rate_percent=(
                fee_rate_percent
            ),
            slippage_percent=(
                slippage_percent
            ),
        ),
    ]
def test_detects_profitable_triangular_route():
    request = TriangularScanRequest(
        exchange="BYBIT",
        starting_asset="USDT",
        starting_amount=D("1000"),
        minimum_profit_percent=D("3"),
        quotes=build_profitable_triangle(),
    )
    result = (
        TriangularArbitrageService(
            clock_ms=lambda: 1000
        ).scan(request)
    )
    assert result.total_quotes == 3
    assert result.eligible_quotes == 3
    assert result.total_directed_edges == 6
    assert result.total_cycles_discovered == 2
    assert result.total_routes_evaluated == 2
    assert result.profitable_count == 1
    assert result.matched_count == 1
    assert result.returned_count == 1
    opportunity = result.opportunities[0]
    assert opportunity.route_assets == [
        "USDT",
        "BTC",
        "ETH",
        "USDT",
    ]
    assert opportunity.route_symbols == [
        "BTCUSDT",
        "BTCETH",
        "ETHUSDT",
    ]
    assert opportunity.route_sides == [
        "BUY",
        "SELL",
        "SELL",
    ]
    assert (
        opportunity
        .evaluation
        .net_profit_amount
        == D("40")
    )
    assert (
        opportunity
        .evaluation
        .net_profit_percent
        == D("4")
    )
def test_costs_can_remove_triangle():
    request = TriangularScanRequest(
        exchange="BYBIT",
        starting_asset="USDT",
        starting_amount=D("1000"),
        quotes=build_profitable_triangle(
            fee_rate_percent="0.5",
            slippage_percent="1",
        ),
    )
    result = (
        TriangularArbitrageService(
            clock_ms=lambda: 1000
        ).scan(request)
    )
    assert result.total_routes_evaluated == 2
    assert result.profitable_count == 0
    assert result.matched_count == 0
def test_quotes_from_other_exchange_are_excluded():
    quotes = build_profitable_triangle()
    quotes[1] = build_quote(
        exchange="BINANCE",
        symbol="BTCETH",
        base_asset="BTC",
        quote_asset="ETH",
        bid_price="20",
        ask_price="20.1",
    )
    request = TriangularScanRequest(
        exchange="BYBIT",
        starting_amount=D("1000"),
        quotes=quotes,
    )
    result = (
        TriangularArbitrageService(
            clock_ms=lambda: 1000
        ).scan(request)
    )
    assert result.eligible_quotes == 2
    assert result.total_cycles_discovered == 0
    assert result.matched_count == 0
def test_stale_quote_breaks_triangle():
    quotes = build_profitable_triangle()
    quotes[0] = build_quote(
        symbol="BTCUSDT",
        base_asset="BTC",
        quote_asset="USDT",
        bid_price="49990",
        ask_price="50000",
        observed_at_ms=1000,
    )
    quotes[1] = build_quote(
        symbol="BTCETH",
        base_asset="BTC",
        quote_asset="ETH",
        bid_price="20",
        ask_price="20.1",
        observed_at_ms=1900,
    )
    quotes[2] = build_quote(
        symbol="ETHUSDT",
        base_asset="ETH",
        quote_asset="USDT",
        bid_price="2600",
        ask_price="2601",
        observed_at_ms=1900,
    )
    request = TriangularScanRequest(
        exchange="BYBIT",
        starting_amount=D("1000"),
        maximum_quote_age_ms=500,
        quotes=quotes,
    )
    result = (
        TriangularArbitrageService(
            clock_ms=lambda: 2000
        ).scan(request)
    )
    assert result.eligible_quotes == 2
    assert result.total_cycles_discovered == 0
def test_quote_time_skew_is_enforced():
    quotes = build_profitable_triangle()
    quotes[0].observed_at_ms = 1000
    quotes[1].observed_at_ms = 1300
    quotes[2].observed_at_ms = 2000
    request = TriangularScanRequest(
        exchange="BYBIT",
        starting_amount=D("1000"),
        maximum_time_skew_ms=500,
        quotes=quotes,
    )
    result = (
        TriangularArbitrageService(
            clock_ms=lambda: 2000
        ).scan(request)
    )
    assert result.total_cycles_discovered == 2
    assert result.total_routes_evaluated == 0
    assert result.matched_count == 0
def test_full_liquidity_requirement_skips_route():
    request = TriangularScanRequest(
        exchange="BYBIT",
        starting_amount=D("1000"),
        require_full_liquidity=True,
        quotes=build_profitable_triangle(
            btc_ask_size="0.01"
        ),
    )
    result = (
        TriangularArbitrageService(
            clock_ms=lambda: 1000
        ).scan(request)
    )
    assert result.matched_count == 0
def test_partial_liquidity_caps_starting_amount():
    request = TriangularScanRequest(
        exchange="BYBIT",
        starting_amount=D("1000"),
        require_full_liquidity=False,
        quotes=build_profitable_triangle(
            btc_ask_size="0.01"
        ),
    )
    result = (
        TriangularArbitrageService(
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
        == D("20.00")
    )
def test_disconnected_markets_produce_no_cycle():
    quotes = [
        build_quote(
            symbol="BTCUSDT",
            base_asset="BTC",
            quote_asset="USDT",
            bid_price="49990",
            ask_price="50000",
        ),
        build_quote(
            symbol="ETHUSDC",
            base_asset="ETH",
            quote_asset="USDC",
            bid_price="2500",
            ask_price="2501",
        ),
        build_quote(
            symbol="SOLBTC",
            base_asset="SOL",
            quote_asset="BTC",
            bid_price="0.002",
            ask_price="0.0021",
        ),
    ]
    request = TriangularScanRequest(
        exchange="BYBIT",
        starting_amount=D("1000"),
        quotes=quotes,
    )
    result = (
        TriangularArbitrageService(
            clock_ms=lambda: 1000
        ).scan(request)
    )
    assert result.total_cycles_discovered == 0
    assert result.total_routes_evaluated == 0
    assert result.opportunities == []
def test_ranking_and_limit_are_deterministic():
    quotes = build_profitable_triangle()
    quotes.extend(
        [
            build_quote(
                symbol="ADAUSDT",
                base_asset="ADA",
                quote_asset="USDT",
                bid_price="0.99",
                ask_price="1",
                bid_size="10000",
                ask_size="10000",
            ),
            build_quote(
                symbol="ADASOL",
                base_asset="ADA",
                quote_asset="SOL",
                bid_price="0.01",
                ask_price="0.0101",
                bid_size="10000",
                ask_size="10000",
            ),
            build_quote(
                symbol="SOLUSDT",
                base_asset="SOL",
                quote_asset="USDT",
                bid_price="110",
                ask_price="111",
                bid_size="10000",
                ask_size="10000",
            ),
        ]
    )
    request = TriangularScanRequest(
        exchange="BYBIT",
        starting_amount=D("1000"),
        sort_by="net_profit_percent",
        descending=True,
        limit=1,
        quotes=quotes,
    )
    result = (
        TriangularArbitrageService(
            clock_ms=lambda: 1000
        ).scan(request)
    )
    assert result.matched_count == 2
    assert result.returned_count == 1
    opportunity = result.opportunities[0]
    assert opportunity.route_assets == [
        "USDT",
        "ADA",
        "SOL",
        "USDT",
    ]
    assert (
        opportunity
        .evaluation
        .net_profit_percent
        == D("10")
    )
def test_request_identifiers_are_normalized():
    request = TriangularScanRequest(
        exchange=" bybit ",
        starting_asset=" usdt ",
        starting_amount=D("1000"),
        quotes=build_profitable_triangle(),
    )
    assert request.exchange == "BYBIT"
    assert request.starting_asset == "USDT"
