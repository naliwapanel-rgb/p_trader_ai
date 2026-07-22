from decimal import (
    Decimal,
)
from typing import (
    Any,
)
from app.schemas.arbitrage import (
    CrossExchangeScanRequest,
    TriangularScanRequest,
)
from app.schemas.trading_bot_strategy import (
    ArbitrageStrategyConfig,
    TradingBotStrategyContext,
    TradingBotStrategyDecision,
)
from app.services.cross_exchange_arbitrage_service import (
    CrossExchangeArbitrageService,
)
from app.services.triangular_arbitrage_service import (
    TriangularArbitrageService,
)
class ArbitrageTradingStrategy:
    strategy_type = "ARBITRAGE"
    def __init__(
        self,
        *,
        cross_exchange_service: (
            CrossExchangeArbitrageService
            | None
        ) = None,
        triangular_service: (
            TriangularArbitrageService
            | None
        ) = None,
    ):
        self.cross_exchange_service = (
            cross_exchange_service
            or CrossExchangeArbitrageService()
        )
        self.triangular_service = (
            triangular_service
            or TriangularArbitrageService()
        )
    def validate_config(
        self,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        validated = (
            ArbitrageStrategyConfig
            .model_validate(config)
        )
        return validated.model_dump()
    @staticmethod
    def _filter_quotes(
        *,
        context: TradingBotStrategyContext,
        config: ArbitrageStrategyConfig,
    ):
        allowed_exchanges = set(
            config.exchanges
        )
        allowed_symbols = set(
            config.symbols
        )
        return [
            quote
            for quote
            in context.arbitrage_quotes
            if (
                quote.exchange
                in allowed_exchanges
                and (
                    not allowed_symbols
                    or quote.symbol
                    in allowed_symbols
                )
            )
        ]
    @staticmethod
    def _confidence(
        *,
        net_profit_percent: float,
        minimum_profit_percent: float,
    ) -> float:
        baseline = max(
            minimum_profit_percent,
            0.01,
        )
        return min(
            1.0,
            max(
                0.0,
                net_profit_percent
                / (
                    baseline * 2
                ),
            ),
        )
    @staticmethod
    def _decision(
        *,
        context: TradingBotStrategyContext,
        config: ArbitrageStrategyConfig,
        reason: str,
        confidence: float = 0.0,
        metadata: (
            dict[str, Any] | None
        ) = None,
    ) -> TradingBotStrategyDecision:
        decision_metadata = {
            "strategy_type": "ARBITRAGE",
            "opportunity_type": (
                config.opportunity_type
            ),
            "starting_asset": (
                config.starting_asset
            ),
            "starting_amount": (
                config.starting_amount
            ),
            "minimum_profit_percent": (
                config.minimum_profit_percent
            ),
            "exchanges": list(
                config.exchanges
            ),
            "symbols": list(
                config.symbols
            ),
            "evaluation_only": True,
        }
        if metadata:
            decision_metadata.update(
                metadata
            )
        return TradingBotStrategyDecision(
            action="HOLD",
            confidence=confidence,
            reason=reason,
            reference_price=(
                context.ticker.last_price
            ),
            evaluated_at=(
                context.evaluated_at
            ),
            metadata=decision_metadata,
        )
    async def evaluate(
        self,
        context: TradingBotStrategyContext,
    ) -> TradingBotStrategyDecision:
        config = (
            ArbitrageStrategyConfig
            .model_validate(
                context.config
            )
        )
        quotes = self._filter_quotes(
            context=context,
            config=config,
        )
        if not quotes:
            return self._decision(
                context=context,
                config=config,
                reason=(
                    "Arbitrage strategy is "
                    "waiting for matching "
                    "quote context"
                ),
                metadata={
                    "received_quote_count": len(
                        context.arbitrage_quotes
                    ),
                    "filtered_quote_count": 0,
                    "matched_count": 0,
                    "opportunity_detected": (
                        False
                    ),
                },
            )
        required_quote_count = (
            2
            if (
                config.opportunity_type
                == "CROSS_EXCHANGE"
            )
            else 3
        )
        if (
            len(quotes)
            < required_quote_count
        ):
            return self._decision(
                context=context,
                config=config,
                reason=(
                    "Arbitrage strategy is "
                    "waiting for sufficient "
                    "matching quote context"
                ),
                metadata={
                    "received_quote_count": len(
                        context.arbitrage_quotes
                    ),
                    "filtered_quote_count": len(
                        quotes
                    ),
                    "required_quote_count": (
                        required_quote_count
                    ),
                    "total_routes_evaluated": 0,
                    "profitable_count": 0,
                    "matched_count": 0,
                    "returned_count": 0,
                    "opportunity_detected": (
                        False
                    ),
                },
            )
        starting_amount = Decimal(
            str(config.starting_amount)
        )
        minimum_profit = Decimal(
            str(
                config
                .minimum_profit_percent
            )
        )
        if (
            config.opportunity_type
            == "CROSS_EXCHANGE"
        ):
            result = (
                self.cross_exchange_service
                .scan(
                    CrossExchangeScanRequest(
                        starting_asset=(
                            config
                            .starting_asset
                        ),
                        starting_amount=(
                            starting_amount
                        ),
                        minimum_profit_percent=(
                            minimum_profit
                        ),
                        maximum_quote_age_ms=(
                            config
                            .maximum_quote_age_ms
                        ),
                        maximum_time_skew_ms=(
                            config
                            .maximum_time_skew_ms
                        ),
                        require_full_liquidity=(
                            config
                            .require_full_liquidity
                        ),
                        sort_by=(
                            "net_profit_percent"
                        ),
                        descending=True,
                        limit=(
                            config
                            .maximum_opportunities
                        ),
                        quotes=quotes,
                    )
                )
            )
        else:
            result = (
                self.triangular_service
                .scan(
                    TriangularScanRequest(
                        exchange=(
                            config.exchanges[0]
                        ),
                        starting_asset=(
                            config
                            .starting_asset
                        ),
                        starting_amount=(
                            starting_amount
                        ),
                        minimum_profit_percent=(
                            minimum_profit
                        ),
                        maximum_quote_age_ms=(
                            config
                            .maximum_quote_age_ms
                        ),
                        maximum_time_skew_ms=(
                            config
                            .maximum_time_skew_ms
                        ),
                        require_full_liquidity=(
                            config
                            .require_full_liquidity
                        ),
                        sort_by=(
                            "net_profit_percent"
                        ),
                        descending=True,
                        limit=(
                            config
                            .maximum_opportunities
                        ),
                        quotes=quotes,
                    )
                )
            )
        metadata = {
            "received_quote_count": len(
                context.arbitrage_quotes
            ),
            "filtered_quote_count": len(
                quotes
            ),
            "total_routes_evaluated": (
                result.total_routes_evaluated
            ),
            "profitable_count": (
                result.profitable_count
            ),
            "matched_count": (
                result.matched_count
            ),
            "returned_count": (
                result.returned_count
            ),
            "scanned_at_ms": (
                result.scanned_at_ms
            ),
            "opportunity_detected": (
                bool(result.opportunities)
            ),
        }
        if not result.opportunities:
            return self._decision(
                context=context,
                config=config,
                reason=(
                    "No executable Arbitrage "
                    "opportunity met the "
                    "configured profitability, "
                    "liquidity and timing limits"
                ),
                metadata=metadata,
            )
        best_opportunity = (
            result.opportunities[0]
        )
        best_evaluation = (
            best_opportunity.evaluation
        )
        net_profit_percent = float(
            best_evaluation
            .net_profit_percent
        )
        confidence = self._confidence(
            net_profit_percent=(
                net_profit_percent
            ),
            minimum_profit_percent=(
                config
                .minimum_profit_percent
            ),
        )
        metadata.update({
            "best_net_profit_percent": (
                net_profit_percent
            ),
            "best_net_profit_amount": float(
                best_evaluation
                .net_profit_amount
            ),
            "best_gross_profit_percent": float(
                best_evaluation
                .gross_profit_percent
            ),
            "best_total_cost_impact": float(
                best_evaluation
                .total_cost_impact
            ),
            "best_evaluated_amount": float(
                best_opportunity
                .evaluated_starting_amount
            ),
            "best_fully_liquid": (
                best_opportunity
                .fully_liquid
            ),
            "best_quote_time_skew_ms": (
                best_opportunity
                .quote_time_skew_ms
            ),
            "best_opportunity": (
                best_opportunity
                .model_dump(
                    mode="json"
                )
            ),
        })
        return self._decision(
            context=context,
            config=config,
            confidence=confidence,
            reason=(
                "Executable Arbitrage "
                "opportunity detected in "
                "evaluation-only mode"
            ),
            metadata=metadata,
        )
