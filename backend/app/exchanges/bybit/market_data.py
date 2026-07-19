import httpx
from fastapi import HTTPException, status
from app.exchanges.utils import to_float
from app.schemas.market_scanner import (
    MarketCategory,
    MarketTickerBatch,
    MarketTickerSnapshot,
)
class BybitMarketDataClient:
    SUPPORTED_CATEGORIES = {
        "spot",
        "linear",
        "inverse",
    }
    def __init__(
        self,
        is_testnet: bool = False,
    ):
        self.is_testnet = is_testnet
        self.base_url = (
            "https://api-testnet.bybit.com"
            if is_testnet
            else "https://api.bybit.com"
        )
    @staticmethod
    def _to_int(value) -> int:
        try:
            return int(float(value or 0))
        except (TypeError, ValueError):
            return 0
    @classmethod
    def _normalize_ticker(
        cls,
        *,
        raw_ticker: dict,
        category: MarketCategory,
        observed_at_ms: int,
    ) -> MarketTickerSnapshot:
        last_price = to_float(
            raw_ticker.get("lastPrice")
        )
        bid_price = to_float(
            raw_ticker.get("bid1Price")
        )
        ask_price = to_float(
            raw_ticker.get("ask1Price")
        )
        previous_price = to_float(
            raw_ticker.get("prevPrice24h")
        )
        spread = 0.0
        if bid_price > 0 and ask_price > 0:
            spread = max(
                ask_price - bid_price,
                0.0,
            )
        midpoint = (
            (bid_price + ask_price) / 2
            if bid_price > 0 and ask_price > 0
            else 0.0
        )
        spread_percent = (
            spread / midpoint * 100
            if midpoint > 0
            else 0.0
        )
        price_change = (
            last_price - previous_price
            if previous_price > 0
            else 0.0
        )
        return MarketTickerSnapshot(
            exchange="BYBIT",
            category=category,
            symbol=str(
                raw_ticker.get("symbol") or ""
            ).upper(),
            last_price=last_price,
            bid_price=bid_price,
            bid_size=to_float(
                raw_ticker.get("bid1Size")
            ),
            ask_price=ask_price,
            ask_size=to_float(
                raw_ticker.get("ask1Size")
            ),
            spread=spread,
            spread_percent=spread_percent,
            previous_price_24h=previous_price,
            price_change_24h=price_change,
            price_change_percent_24h=(
                to_float(
                    raw_ticker.get(
                        "price24hPcnt"
                    )
                )
                * 100
            ),
            high_24h=to_float(
                raw_ticker.get("highPrice24h")
            ),
            low_24h=to_float(
                raw_ticker.get("lowPrice24h")
            ),
            volume_24h=to_float(
                raw_ticker.get("volume24h")
            ),
            turnover_24h=to_float(
                raw_ticker.get("turnover24h")
            ),
            index_price=to_float(
                raw_ticker.get("indexPrice")
            ),
            mark_price=to_float(
                raw_ticker.get("markPrice")
            ),
            usd_index_price=to_float(
                raw_ticker.get("usdIndexPrice")
            ),
            open_interest=to_float(
                raw_ticker.get("openInterest")
            ),
            open_interest_value=to_float(
                raw_ticker.get(
                    "openInterestValue"
                )
            ),
            funding_rate=to_float(
                raw_ticker.get("fundingRate")
            ),
            next_funding_time_ms=cls._to_int(
                raw_ticker.get(
                    "nextFundingTime"
                )
            ),
            observed_at_ms=observed_at_ms,
        )
    async def _request_tickers(
        self,
        *,
        category: MarketCategory,
    ) -> dict:
        try:
            async with httpx.AsyncClient(
                timeout=15
            ) as client:
                response = await client.get(
                    (
                        f"{self.base_url}"
                        "/v5/market/tickers"
                    ),
                    params={
                        "category": category,
                    },
                )
            response.raise_for_status()
            payload = response.json()
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_504_GATEWAY_TIMEOUT
                ),
                detail=(
                    "Bybit market request timed out"
                ),
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_502_BAD_GATEWAY
                ),
                detail=(
                    "Bybit market request failed "
                    f"with status "
                    f"{exc.response.status_code}"
                ),
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_502_BAD_GATEWAY
                ),
                detail=(
                    "Unable to connect to Bybit: "
                    f"{exc}"
                ),
            ) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_502_BAD_GATEWAY
                ),
                detail=(
                    "Bybit returned invalid "
                    "market data"
                ),
            ) from exc
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=(
                    status.HTTP_502_BAD_GATEWAY
                ),
                detail=(
                    "Bybit returned invalid "
                    "market data"
                ),
            )
        return payload
    async def get_tickers(
        self,
        category: str = "spot",
    ) -> dict:
        normalized_category = (
            category.strip().lower()
        )
        if (
            normalized_category
            not in self.SUPPORTED_CATEGORIES
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "category must be spot, "
                    "linear or inverse"
                ),
            )
        payload = await self._request_tickers(
            category=normalized_category,
        )
        try:
            ret_code = int(
                payload.get("retCode") or 0
            )
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_502_BAD_GATEWAY
                ),
                detail=(
                    "Bybit returned invalid "
                    "market data"
                ),
            ) from exc
        if ret_code != 0:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "Bybit API error: "
                    f"{payload.get(
                        'retMsg',
                        'Unknown error',
                    )}"
                ),
            )
        result = payload.get("result")
        if not isinstance(result, dict):
            raise HTTPException(
                status_code=(
                    status.HTTP_502_BAD_GATEWAY
                ),
                detail=(
                    "Bybit returned invalid "
                    "ticker data"
                ),
            )
        raw_tickers = result.get("list")
        if not isinstance(raw_tickers, list):
            raise HTTPException(
                status_code=(
                    status.HTTP_502_BAD_GATEWAY
                ),
                detail=(
                    "Bybit returned invalid "
                    "ticker data"
                ),
            )
        if any(
            not isinstance(item, dict)
            or not item.get("symbol")
            for item in raw_tickers
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_502_BAD_GATEWAY
                ),
                detail=(
                    "Bybit returned malformed "
                    "ticker entries"
                ),
            )
        observed_at_ms = self._to_int(
            payload.get("time")
        )
        tickers = [
            self._normalize_ticker(
                raw_ticker=item,
                category=normalized_category,
                observed_at_ms=observed_at_ms,
            )
            for item in raw_tickers
        ]
        return MarketTickerBatch(
            exchange="BYBIT",
            category=normalized_category,
            observed_at_ms=observed_at_ms,
            count=len(tickers),
            tickers=tickers,
        ).model_dump()
