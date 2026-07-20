import time
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from app.schemas.arbitrage import (
    ArbitrageEvaluationRequest,
    ArbitrageLegRequest,
    ArbitrageMarketQuote,
    TriangularOpportunity,
    TriangularScanRequest,
    TriangularScanResult,
)
from app.services.arbitrage_profit_service import (
    ArbitrageProfitService,
)
@dataclass(frozen=True)
class _DirectedMarketEdge:
    quote_index: int
    quote: ArbitrageMarketQuote
    side: str
    input_asset: str
    output_asset: str
    price: Decimal
    input_capacity: Decimal
class TriangularArbitrageService:
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
    def _build_edges(
        quotes: list[ArbitrageMarketQuote],
    ) -> list[_DirectedMarketEdge]:
        edges: list[_DirectedMarketEdge] = []
        for quote_index, quote in enumerate(
            quotes
        ):
            edges.append(
                _DirectedMarketEdge(
                    quote_index=quote_index,
                    quote=quote,
                    side="BUY",
                    input_asset=(
                        quote.quote_asset
                    ),
                    output_asset=(
                        quote.base_asset
                    ),
                    price=quote.ask_price,
                    input_capacity=(
                        quote.ask_size
                        * quote.ask_price
                    ),
                )
            )
            edges.append(
                _DirectedMarketEdge(
                    quote_index=quote_index,
                    quote=quote,
                    side="SELL",
                    input_asset=(
                        quote.base_asset
                    ),
                    output_asset=(
                        quote.quote_asset
                    ),
                    price=quote.bid_price,
                    input_capacity=(
                        quote.bid_size
                    ),
                )
            )
        return edges
    @staticmethod
    def _find_cycles(
        *,
        starting_asset: str,
        edges: list[_DirectedMarketEdge],
    ) -> list[
        tuple[
            _DirectedMarketEdge,
            _DirectedMarketEdge,
            _DirectedMarketEdge,
        ]
    ]:
        cycles = []
        first_edges = [
            edge
            for edge in edges
            if (
                edge.input_asset
                == starting_asset
                and edge.output_asset
                != starting_asset
            )
        ]
        for first in first_edges:
            second_edges = [
                edge
                for edge in edges
                if (
                    edge.input_asset
                    == first.output_asset
                    and edge.quote_index
                    != first.quote_index
                    and edge.output_asset
                    not in {
                        starting_asset,
                        first.output_asset,
                    }
                )
            ]
            for second in second_edges:
                third_edges = [
                    edge
                    for edge in edges
                    if (
                        edge.input_asset
                        == second.output_asset
                        and edge.output_asset
                        == starting_asset
                        and edge.quote_index
                        not in {
                            first.quote_index,
                            second.quote_index,
                        }
                    )
                ]
                for third in third_edges:
                    cycles.append(
                        (
                            first,
                            second,
                            third,
                        )
                    )
        return cycles
    @staticmethod
    def _conversion_ratio(
        edge: _DirectedMarketEdge,
    ) -> Decimal:
        if edge.side == "BUY":
            return (
                Decimal("1")
                / edge.price
            )
        return edge.price
    @classmethod
    def _maximum_starting_amount(
        cls,
        cycle: tuple[
            _DirectedMarketEdge,
            _DirectedMarketEdge,
            _DirectedMarketEdge,
        ],
    ) -> Decimal:
        conversion_multiplier = Decimal("1")
        maximum_starting_amount: (
            Decimal | None
        ) = None
        for edge in cycle:
            capacity_in_starting_asset = (
                edge.input_capacity
                / conversion_multiplier
            )
            if maximum_starting_amount is None:
                maximum_starting_amount = (
                    capacity_in_starting_asset
                )
            else:
                maximum_starting_amount = min(
                    maximum_starting_amount,
                    capacity_in_starting_asset,
                )
            conversion_multiplier *= (
                cls._conversion_ratio(edge)
            )
        return (
            maximum_starting_amount
            or Decimal("0")
        )
    @staticmethod
    def _quote_time_skew_ms(
        cycle: tuple[
            _DirectedMarketEdge,
            _DirectedMarketEdge,
            _DirectedMarketEdge,
        ],
    ) -> int:
        timestamps = [
            edge.quote.observed_at_ms
            for edge in cycle
        ]
        if any(
            timestamp <= 0
            for timestamp in timestamps
        ):
            return 0
        return max(timestamps) - min(timestamps)
    @staticmethod
    def _build_evaluation_request(
        *,
        data: TriangularScanRequest,
        starting_amount: Decimal,
        cycle: tuple[
            _DirectedMarketEdge,
            _DirectedMarketEdge,
            _DirectedMarketEdge,
        ],
    ) -> ArbitrageEvaluationRequest:
        legs = []
        for edge in cycle:
            quote = edge.quote
            fixed_cost = (
                quote.fixed_buy_cost
                if edge.side == "BUY"
                else quote.fixed_sell_cost
            )
            legs.append(
                ArbitrageLegRequest(
                    exchange=quote.exchange,
                    symbol=quote.symbol,
                    base_asset=(
                        quote.base_asset
                    ),
                    quote_asset=(
                        quote.quote_asset
                    ),
                    side=edge.side,
                    price=edge.price,
                    fee_rate_percent=(
                        quote.fee_rate_percent
                    ),
                    slippage_percent=(
                        quote.slippage_percent
                    ),
                    fixed_cost=fixed_cost,
                )
            )
        return ArbitrageEvaluationRequest(
            opportunity_type="TRIANGULAR",
            starting_asset=(
                data.starting_asset
            ),
            starting_amount=starting_amount,
            minimum_profit_percent=(
                data.minimum_profit_percent
            ),
            legs=legs,
        )
    @staticmethod
    def _sort_value(
        opportunity: TriangularOpportunity,
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
        if sort_by == "gross_profit_percent":
            return (
                opportunity
                .evaluation
                .gross_profit_percent
            )
        return getattr(
            opportunity,
            sort_by,
        )
    def scan(
        self,
        data: TriangularScanRequest,
    ) -> TriangularScanResult:
        now_ms = self.clock_ms()
        eligible_quotes = [
            quote
            for quote in data.quotes
            if (
                quote.exchange == data.exchange
                and self._quote_is_fresh(
                    quote=quote,
                    now_ms=now_ms,
                    maximum_quote_age_ms=(
                        data.maximum_quote_age_ms
                    ),
                )
            )
        ]
        edges = self._build_edges(
            eligible_quotes
        )
        cycles = self._find_cycles(
            starting_asset=(
                data.starting_asset
            ),
            edges=edges,
        )
        total_routes_evaluated = 0
        profitable_count = 0
        matched: list[
            TriangularOpportunity
        ] = []
        for cycle in cycles:
            quote_time_skew_ms = (
                self._quote_time_skew_ms(
                    cycle
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
                    cycle
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
                    cycle=cycle,
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
            route_assets = [
                cycle[0].input_asset,
                cycle[0].output_asset,
                cycle[1].output_asset,
                cycle[2].output_asset,
            ]
            matched.append(
                TriangularOpportunity(
                    exchange=data.exchange,
                    route_assets=route_assets,
                    route_symbols=[
                        edge.quote.symbol
                        for edge in cycle
                    ],
                    route_sides=[
                        edge.side
                        for edge in cycle
                    ],
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
                opportunity.route_assets,
                opportunity.route_symbols,
                opportunity.route_sides,
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
        return TriangularScanResult(
            exchange=data.exchange,
            starting_asset=(
                data.starting_asset
            ),
            requested_starting_amount=(
                data.starting_amount
            ),
            total_quotes=len(data.quotes),
            eligible_quotes=len(
                eligible_quotes
            ),
            total_directed_edges=len(edges),
            total_cycles_discovered=len(cycles),
            total_routes_evaluated=(
                total_routes_evaluated
            ),
            profitable_count=(
                profitable_count
            ),
            matched_count=matched_count,
            returned_count=len(returned),
            scanned_at_ms=now_ms,
            opportunities=returned,
        )
