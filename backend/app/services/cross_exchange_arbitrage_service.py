import time
from collections import defaultdict
from collections.abc import Callable
from decimal import Decimal
from itertools import permutations
from app.schemas.arbitrage import (
    ArbitrageEvaluationRequest,
    ArbitrageLegRequest,
    ArbitrageMarketQuote,
    CrossExchangeOpportunity,
    CrossExchangeScanRequest,
    CrossExchangeScanResult,
)
from app.services.arbitrage_profit_service import (
    ArbitrageProfitService,
)
ONE_HUNDRED = Decimal("100")
class CrossExchangeArbitrageService:
    def __init__(
        self,
        clock_ms: Callable[[], int] | None = None,
    ):
        self.clock_ms = (
            clock_ms
            or (
                lambda:
                int(time.time() * 1000)
            )
        )
    @staticmethod
    def _pair_key(
        quote: ArbitrageMarketQuote,
    ) -> tuple[str, str]:
        return (
            quote.base_asset,
            quote.quote_asset,
        )
    @staticmethod
    def _quote_is_fresh(
        *,
        quote: ArbitrageMarketQuote,
        now_ms: int,
        maximum_quote_age_ms: int | None,
    ) -> bool:
        if maximum_quote_age_ms is None:
            return True
        if quote.observed_at_ms <= 0:
            return False
        age_ms = max(
            now_ms - quote.observed_at_ms,
            0,
        )
        return age_ms <= maximum_quote_age_ms
    @staticmethod
    def _quote_time_skew_ms(
        *,
        buy_quote: ArbitrageMarketQuote,
        sell_quote: ArbitrageMarketQuote,
    ) -> int:
        if (
            buy_quote.observed_at_ms <= 0
            or sell_quote.observed_at_ms <= 0
        ):
            return 0
        return abs(
            buy_quote.observed_at_ms
            - sell_quote.observed_at_ms
        )
    @staticmethod
    def _maximum_starting_amount(
        *,
        buy_quote: ArbitrageMarketQuote,
        sell_quote: ArbitrageMarketQuote,
    ) -> Decimal:
        buy_capacity = (
            buy_quote.ask_size
            * buy_quote.ask_price
        )
        sell_capacity = (
            sell_quote.bid_size
            * buy_quote.ask_price
        )
        return min(
            buy_capacity,
            sell_capacity,
        )
    @staticmethod
    def _gross_spread_percent(
        *,
        buy_quote: ArbitrageMarketQuote,
        sell_quote: ArbitrageMarketQuote,
    ) -> Decimal:
        return (
            (
                sell_quote.bid_price
                - buy_quote.ask_price
            )
            / buy_quote.ask_price
            * ONE_HUNDRED
        )
    @staticmethod
    def _build_evaluation_request(
        *,
        data: CrossExchangeScanRequest,
        starting_amount: Decimal,
        buy_quote: ArbitrageMarketQuote,
        sell_quote: ArbitrageMarketQuote,
    ) -> ArbitrageEvaluationRequest:
        return ArbitrageEvaluationRequest(
            opportunity_type=(
                "CROSS_EXCHANGE"
            ),
            starting_asset=(
                data.starting_asset
            ),
            starting_amount=starting_amount,
            minimum_profit_percent=(
                data.minimum_profit_percent
            ),
            legs=[
                ArbitrageLegRequest(
                    exchange=(
                        buy_quote.exchange
                    ),
                    symbol=buy_quote.symbol,
                    base_asset=(
                        buy_quote.base_asset
                    ),
                    quote_asset=(
                        buy_quote.quote_asset
                    ),
                    side="BUY",
                    price=buy_quote.ask_price,
                    fee_rate_percent=(
                        buy_quote
                        .fee_rate_percent
                    ),
                    slippage_percent=(
                        buy_quote
                        .slippage_percent
                    ),
                    fixed_cost=(
                        buy_quote.fixed_buy_cost
                    ),
                ),
                ArbitrageLegRequest(
                    exchange=(
                        sell_quote.exchange
                    ),
                    symbol=sell_quote.symbol,
                    base_asset=(
                        sell_quote.base_asset
                    ),
                    quote_asset=(
                        sell_quote.quote_asset
                    ),
                    side="SELL",
                    price=sell_quote.bid_price,
                    fee_rate_percent=(
                        sell_quote
                        .fee_rate_percent
                    ),
                    slippage_percent=(
                        sell_quote
                        .slippage_percent
                    ),
                    fixed_cost=(
                        sell_quote
                        .fixed_sell_cost
                    ),
                ),
            ],
        )
    @staticmethod
    def _sort_value(
        opportunity: CrossExchangeOpportunity,
        sort_by: str,
    ):
        if sort_by == "net_profit_percent":
            return (
                opportunity
                .evaluation
                .net_profit_percent
            )
        if sort_by == "net_profit_amount":
            return (
                opportunity
                .evaluation
                .net_profit_amount
            )
        return getattr(
            opportunity,
            sort_by,
        )
    def scan(
        self,
        data: CrossExchangeScanRequest,
    ) -> CrossExchangeScanResult:
        now_ms = self.clock_ms()
        eligible_quotes = [
            quote
            for quote in data.quotes
            if (
                quote.quote_asset
                == data.starting_asset
                and self._quote_is_fresh(
                    quote=quote,
                    now_ms=now_ms,
                    maximum_quote_age_ms=(
                        data.maximum_quote_age_ms
                    ),
                )
            )
        ]
        grouped_quotes: dict[
            tuple[str, str],
            list[ArbitrageMarketQuote],
        ] = defaultdict(list)
        for quote in eligible_quotes:
            grouped_quotes[
                self._pair_key(quote)
            ].append(quote)
        eligible_pairs = {
            key: quotes
            for key, quotes
            in grouped_quotes.items()
            if len(
                {
                    quote.exchange
                    for quote in quotes
                }
            )
            >= 2
        }
        total_routes_evaluated = 0
        profitable_count = 0
        matched: list[
            CrossExchangeOpportunity
        ] = []
        for (
            base_asset,
            quote_asset,
        ), quotes in eligible_pairs.items():
            for buy_quote, sell_quote in (
                permutations(quotes, 2)
            ):
                if (
                    buy_quote.exchange
                    == sell_quote.exchange
                ):
                    continue
                quote_time_skew_ms = (
                    self._quote_time_skew_ms(
                        buy_quote=buy_quote,
                        sell_quote=sell_quote,
                    )
                )
                if (
                    data.maximum_time_skew_ms
                    is not None
                    and quote_time_skew_ms
                    > data.maximum_time_skew_ms
                ):
                    continue
                maximum_starting_amount = (
                    self._maximum_starting_amount(
                        buy_quote=buy_quote,
                        sell_quote=sell_quote,
                    )
                )
                if maximum_starting_amount <= 0:
                    continue
                fully_liquid = (
                    maximum_starting_amount
                    >= data.starting_amount
                )
                if (
                    data.require_full_liquidity
                    and not fully_liquid
                ):
                    continue
                evaluated_starting_amount = min(
                    data.starting_amount,
                    maximum_starting_amount,
                )
                total_routes_evaluated += 1
                request = (
                    self._build_evaluation_request(
                        data=data,
                        starting_amount=(
                            evaluated_starting_amount
                        ),
                        buy_quote=buy_quote,
                        sell_quote=sell_quote,
                    )
                )
                evaluation = (
                    ArbitrageProfitService
                    .evaluate(request)
                )
                if evaluation.profitable:
                    profitable_count += 1
                if not evaluation.executable:
                    continue
                matched.append(
                    CrossExchangeOpportunity(
                        base_asset=base_asset,
                        quote_asset=quote_asset,
                        buy_exchange=(
                            buy_quote.exchange
                        ),
                        buy_symbol=(
                            buy_quote.symbol
                        ),
                        buy_ask_price=(
                            buy_quote.ask_price
                        ),
                        sell_exchange=(
                            sell_quote.exchange
                        ),
                        sell_symbol=(
                            sell_quote.symbol
                        ),
                        sell_bid_price=(
                            sell_quote.bid_price
                        ),
                        gross_spread_percent=(
                            self
                            ._gross_spread_percent(
                                buy_quote=(
                                    buy_quote
                                ),
                                sell_quote=(
                                    sell_quote
                                ),
                            )
                        ),
                        requested_starting_amount=(
                            data.starting_amount
                        ),
                        evaluated_starting_amount=(
                            evaluated_starting_amount
                        ),
                        maximum_starting_amount_by_liquidity=(
                            maximum_starting_amount
                        ),
                        fully_liquid=fully_liquid,
                        quote_time_skew_ms=(
                            quote_time_skew_ms
                        ),
                        evaluation=evaluation,
                    )
                )
        matched.sort(
            key=lambda opportunity: (
                opportunity.base_asset,
                opportunity.buy_exchange,
                opportunity.sell_exchange,
            )
        )
        matched.sort(
            key=lambda opportunity:
            self._sort_value(
                opportunity,
                data.sort_by,
            ),
            reverse=data.descending,
        )
        matched_count = len(matched)
        returned = matched[: data.limit]
        return CrossExchangeScanResult(
            starting_asset=data.starting_asset,
            requested_starting_amount=(
                data.starting_amount
            ),
            total_quotes=len(data.quotes),
            total_pairs=len(eligible_pairs),
            total_routes_evaluated=(
                total_routes_evaluated
            ),
            profitable_count=profitable_count,
            matched_count=matched_count,
            returned_count=len(returned),
            scanned_at_ms=now_ms,
            opportunities=returned,
        )
