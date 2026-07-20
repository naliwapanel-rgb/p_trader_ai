import asyncio
from decimal import Decimal
from types import SimpleNamespace
from app.api.v1.endpoints.arbitrage import (
    evaluate_arbitrage_opportunity,
    get_arbitrage_profit_service,
    get_cross_exchange_arbitrage_service,
    get_triangular_arbitrage_service,
    scan_cross_exchange_opportunities,
    scan_triangular_opportunities,
)
from app.main import app
from app.schemas.arbitrage import (
    ArbitrageEvaluationRequest,
    ArbitrageLegRequest,
    ArbitrageMarketQuote,
    CrossExchangeScanRequest,
    TriangularScanRequest,
)
from app.services.arbitrage_profit_service import (
    ArbitrageProfitService,
)
from app.services.cross_exchange_arbitrage_service import (
    CrossExchangeArbitrageService,
)
from app.services.triangular_arbitrage_service import (
    TriangularArbitrageService,
)
D = Decimal
ARBITRAGE_PATHS = {
    "/api/v1/arbitrage/evaluate",
    (
        "/api/v1/arbitrage/"
        "cross-exchange/scan"
    ),
    (
        "/api/v1/arbitrage/"
        "triangular/scan"
    ),
}
def build_leg(
    *,
    exchange: str,
    symbol: str,
    base_asset: str,
    quote_asset: str,
    side: str,
    price: str,
) -> ArbitrageLegRequest:
    return ArbitrageLegRequest(
        exchange=exchange,
        symbol=symbol,
        base_asset=base_asset,
        quote_asset=quote_asset,
        side=side,
        price=D(price),
    )
def build_evaluation_request(
    *,
    sell_price: str = "51000",
) -> ArbitrageEvaluationRequest:
    return ArbitrageEvaluationRequest(
        opportunity_type=(
            "CROSS_EXCHANGE"
        ),
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
                price=sell_price,
            ),
        ],
    )
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
        observed_at_ms=observed_at_ms,
    )
def build_cross_exchange_request(
) -> CrossExchangeScanRequest:
    return CrossExchangeScanRequest(
        starting_asset="USDT",
        starting_amount=D("1000"),
        minimum_profit_percent=D("1"),
        quotes=[
            build_quote(
                exchange="BYBIT",
                symbol="BTCUSDT",
                base_asset="BTC",
                quote_asset="USDT",
                bid_price="49990",
                ask_price="50000",
                bid_size="1",
                ask_size="1",
            ),
            build_quote(
                exchange="BINANCE",
                symbol="BTCUSDT",
                base_asset="BTC",
                quote_asset="USDT",
                bid_price="51000",
                ask_price="51010",
                bid_size="1",
                ask_size="1",
            ),
        ],
    )
def build_triangular_request(
) -> TriangularScanRequest:
    return TriangularScanRequest(
        exchange="BYBIT",
        starting_asset="USDT",
        starting_amount=D("1000"),
        minimum_profit_percent=D("3"),
        quotes=[
            build_quote(
                symbol="BTCUSDT",
                base_asset="BTC",
                quote_asset="USDT",
                bid_price="49990",
                ask_price="50000",
                bid_size="1",
                ask_size="1",
            ),
            build_quote(
                symbol="BTCETH",
                base_asset="BTC",
                quote_asset="ETH",
                bid_price="20",
                ask_price="20.1",
                bid_size="1",
                ask_size="1",
            ),
            build_quote(
                symbol="ETHUSDT",
                base_asset="ETH",
                quote_asset="USDT",
                bid_price="2600",
                ask_price="2601",
                bid_size="100",
                ask_size="100",
            ),
        ],
    )
def test_arbitrage_routes_are_registered():
    paths = app.openapi()["paths"]
    assert ARBITRAGE_PATHS.issubset(
        paths
    )
def test_arbitrage_routes_use_post():
    paths = app.openapi()["paths"]
    for path in ARBITRAGE_PATHS:
        assert set(paths[path]) == {
            "post"
        }
def test_arbitrage_routes_require_authentication():
    paths = app.openapi()["paths"]
    for path in ARBITRAGE_PATHS:
        operation = paths[path]["post"]
        assert operation.get("security")
def test_profit_service_dependency():
    service = get_arbitrage_profit_service(
        current_user=SimpleNamespace(id=1)
    )
    assert isinstance(
        service,
        ArbitrageProfitService,
    )
def test_cross_exchange_service_dependency():
    service = (
        get_cross_exchange_arbitrage_service(
            current_user=(
                SimpleNamespace(id=1)
            )
        )
    )
    assert isinstance(
        service,
        CrossExchangeArbitrageService,
    )
def test_triangular_service_dependency():
    service = (
        get_triangular_arbitrage_service(
            current_user=(
                SimpleNamespace(id=1)
            )
        )
    )
    assert isinstance(
        service,
        TriangularArbitrageService,
    )
def test_evaluate_endpoint_returns_profit():
    response = asyncio.run(
        evaluate_arbitrage_opportunity(
            data=build_evaluation_request(),
            service=(
                ArbitrageProfitService()
            ),
        )
    )
    data = response["data"]
    assert response["success"] is True
    assert response["message"] == (
        "Arbitrage opportunity evaluated "
        "successfully"
    )
    assert D(
        data["net_profit_amount"]
    ) == D("20")
    assert D(
        data["net_profit_percent"]
    ) == D("2")
    assert data["executable"] is True
def test_evaluate_endpoint_returns_rejection():
    response = asyncio.run(
        evaluate_arbitrage_opportunity(
            data=build_evaluation_request(
                sell_price="49900"
            ),
            service=(
                ArbitrageProfitService()
            ),
        )
    )
    data = response["data"]
    assert response["success"] is True
    assert D(
        data["net_profit_amount"]
    ) < D("0")
    assert data["profitable"] is False
    assert data["executable"] is False
def test_cross_exchange_scan_endpoint():
    response = asyncio.run(
        scan_cross_exchange_opportunities(
            data=(
                build_cross_exchange_request()
            ),
            service=(
                CrossExchangeArbitrageService(
                    clock_ms=lambda: 1000
                )
            ),
        )
    )
    data = response["data"]
    assert response["success"] is True
    assert data["scanned_at_ms"] == 1000
    assert data["matched_count"] == 1
    assert data["returned_count"] == 1
    opportunity = data[
        "opportunities"
    ][0]
    assert (
        opportunity["buy_exchange"]
        == "BYBIT"
    )
    assert (
        opportunity["sell_exchange"]
        == "BINANCE"
    )
    assert D(
        opportunity[
            "evaluation"
        ][
            "net_profit_amount"
        ]
    ) == D("20")
def test_triangular_scan_endpoint():
    response = asyncio.run(
        scan_triangular_opportunities(
            data=build_triangular_request(),
            service=(
                TriangularArbitrageService(
                    clock_ms=lambda: 1000
                )
            ),
        )
    )
    data = response["data"]
    assert response["success"] is True
    assert data["scanned_at_ms"] == 1000
    assert data["matched_count"] == 1
    assert data["returned_count"] == 1
    opportunity = data[
        "opportunities"
    ][0]
    assert opportunity[
        "route_assets"
    ] == [
        "USDT",
        "BTC",
        "ETH",
        "USDT",
    ]
    assert D(
        opportunity[
            "evaluation"
        ][
            "net_profit_amount"
        ]
    ) == D("40")
