import time
from collections.abc import (
    Callable,
    Mapping,
)
from typing import Any
from app.schemas.ai_assistant import (
    AIAnalysisMetadata,
    AIAnalysisResponse,
    AIAnalysisSection,
    AIAnalysisWarning,
    AIArbitrageExplanationRequest,
    AIAssistantRequest,
    AIMarketAnalysisRequest,
    AIPortfolioAnalysisRequest,
    AIRiskExplanationRequest,
    AITradePlan,
    AITradePlanRequest,
)
from app.schemas.portfolio_sync import (
    PortfolioSyncSnapshotResponse,
)
class DeterministicAIAnalysisService:
    """
    Deterministic advisory analysis foundation.
    This service does not call an external AI provider,
    submit automation jobs, or execute exchange orders.
    """
    def __init__(
        self,
        *,
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
    def _to_mapping(
        value: Any,
    ) -> dict[str, Any]:
        model_dump = getattr(
            value,
            "model_dump",
            None,
        )
        if callable(model_dump):
            return dict(
                model_dump(
                    mode="python"
                )
            )
        if isinstance(value, Mapping):
            return dict(value)
        raise TypeError(
            "Analysis input must be a mapping "
            "or Pydantic model"
        )
    @staticmethod
    def _number(
        value: Any,
        default: float = 0.0,
    ) -> float:
        if value is None:
            return default
        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return default
    @staticmethod
    def _first_number(
        data: Mapping[str, Any],
        *keys: str,
    ) -> float | None:
        for key in keys:
            value = data.get(key)
            if value is None:
                continue
            try:
                return float(value)
            except (
                TypeError,
                ValueError,
            ):
                continue
        return None
    def _metadata(
        self,
        *,
        analysis_type: str,
        data_sources: list[str],
        confidence_score: float,
    ) -> AIAnalysisMetadata:
        return AIAnalysisMetadata(
            analysis_type=analysis_type,
            generated_at_ms=self.clock_ms(),
            confidence_score=(
                confidence_score
            ),
            data_sources=data_sources,
            provider="DETERMINISTIC",
            model_name=None,
            advisory_only=True,
            execution_enabled=False,
        )
    @staticmethod
    def _advisory_warning() -> (
        AIAnalysisWarning
    ):
        return AIAnalysisWarning(
            code="ADVISORY_ONLY",
            severity="INFO",
            message=(
                "This analysis is advisory only "
                "and cannot execute a trade."
            ),
        )
    def answer_general(
        self,
        data: AIAssistantRequest,
    ) -> AIAnalysisResponse:
        symbols_text = (
            ", ".join(data.symbols)
            if data.symbols
            else "No symbols were supplied"
        )
        return AIAnalysisResponse(
            status="PARTIAL",
            answer=(
                "The deterministic assistant "
                "foundation is available, but "
                "additional market, portfolio, "
                "risk, or arbitrage context is "
                "required for a domain-specific "
                "analysis."
            ),
            sections=[
                AIAnalysisSection(
                    title="User Request",
                    summary=data.question,
                    metrics={
                        "analysis_type": (
                            data.analysis_type
                        ),
                        "symbols": data.symbols,
                        "portfolio_id": (
                            data.portfolio_id
                        ),
                        "exchange_account_id": (
                            data
                            .exchange_account_id
                        ),
                    },
                ),
                AIAnalysisSection(
                    title="Context Status",
                    summary=symbols_text,
                    bullet_points=[
                        (
                            "No external AI provider "
                            "was called."
                        ),
                        (
                            "No automation job or "
                            "exchange order was created."
                        ),
                    ],
                ),
            ],
            warnings=[
                AIAnalysisWarning(
                    code="CONTEXT_REQUIRED",
                    severity="INFO",
                    message=(
                        "Use a market, portfolio, "
                        "risk, trade-plan, or "
                        "arbitrage analysis method "
                        "with validated domain data."
                    ),
                ),
                self._advisory_warning(),
            ],
            metadata=self._metadata(
                analysis_type=(
                    data.analysis_type
                ),
                data_sources=[
                    "USER_QUERY",
                ],
                confidence_score=0.25,
            ),
            execution_allowed=False,
        )
    def analyze_market(
        self,
        *,
        data: AIMarketAnalysisRequest,
        tickers: list[Any],
    ) -> AIAnalysisResponse:
        requested_symbols = set(
            data.symbols
        )
        normalized: list[
            dict[str, Any]
        ] = []
        for ticker in tickers:
            item = self._to_mapping(
                ticker
            )
            symbol = str(
                item.get(
                    "symbol",
                    "",
                )
            ).strip().upper()
            if (
                not symbol
                or (
                    requested_symbols
                    and symbol
                    not in requested_symbols
                )
            ):
                continue
            normalized.append({
                "symbol": symbol,
                "last_price": self._number(
                    item.get("last_price")
                ),
                (
                    "price_change_"
                    "percent_24h"
                ): self._number(
                    item.get(
                        (
                            "price_change_"
                            "percent_24h"
                        )
                    )
                ),
                "volume_24h": self._number(
                    item.get("volume_24h")
                ),
                "turnover_24h": self._number(
                    item.get(
                        "turnover_24h"
                    )
                ),
            })
        if not normalized:
            return AIAnalysisResponse(
                status="UNAVAILABLE",
                answer=(
                    "No matching market ticker "
                    "data was available for the "
                    "requested symbols."
                ),
                warnings=[
                    AIAnalysisWarning(
                        code="MARKET_DATA_MISSING",
                        severity="WARNING",
                        message=(
                            "Market analysis requires "
                            "at least one matching "
                            "ticker snapshot."
                        ),
                    ),
                    self._advisory_warning(),
                ],
                metadata=self._metadata(
                    analysis_type="MARKET",
                    data_sources=[
                        "USER_QUERY",
                        "MARKET_SCANNER",
                    ],
                    confidence_score=0.0,
                ),
                execution_allowed=False,
            )
        strongest = max(
            normalized,
            key=lambda item: item[
                (
                    "price_change_"
                    "percent_24h"
                )
            ],
        )
        weakest = min(
            normalized,
            key=lambda item: item[
                (
                    "price_change_"
                    "percent_24h"
                )
            ],
        )
        most_active = max(
            normalized,
            key=lambda item: item[
                "turnover_24h"
            ],
        )
        changes = [
            item[
                (
                    "price_change_"
                    "percent_24h"
                )
            ]
            for item in normalized
        ]
        average_change = (
            sum(changes)
            / len(changes)
        )
        if average_change > 1:
            direction = "BULLISH"
            direction_text = (
                "The selected market basket "
                "has positive 24-hour momentum."
            )
        elif average_change < -1:
            direction = "BEARISH"
            direction_text = (
                "The selected market basket "
                "has negative 24-hour momentum."
            )
        else:
            direction = "MIXED"
            direction_text = (
                "The selected market basket "
                "has mixed or neutral momentum."
            )
        warnings = [
            self._advisory_warning(),
        ]
        dispersion = (
            strongest[
                (
                    "price_change_"
                    "percent_24h"
                )
            ]
            - weakest[
                (
                    "price_change_"
                    "percent_24h"
                )
            ]
        )
        if dispersion >= 10:
            warnings.append(
                AIAnalysisWarning(
                    code="HIGH_MARKET_DISPERSION",
                    severity="WARNING",
                    message=(
                        "Performance varies widely "
                        "between the strongest and "
                        "weakest requested assets."
                    ),
                )
            )
        if any(
            abs(change) >= 10
            for change in changes
        ):
            warnings.append(
                AIAnalysisWarning(
                    code="HIGH_VOLATILITY",
                    severity="WARNING",
                    message=(
                        "At least one requested asset "
                        "moved 10 percent or more "
                        "during the measured period."
                    ),
                )
            )
        return AIAnalysisResponse(
            status="SUCCESS",
            answer=direction_text,
            sections=[
                AIAnalysisSection(
                    title="Market Direction",
                    summary=direction_text,
                    bullet_points=[
                        (
                            f"Strongest asset: "
                            f"{strongest['symbol']} "
                            f"at "
                            f"{strongest['price_change_percent_24h']:.2f}%."
                        ),
                        (
                            f"Weakest asset: "
                            f"{weakest['symbol']} "
                            f"at "
                            f"{weakest['price_change_percent_24h']:.2f}%."
                        ),
                        (
                            f"Highest turnover: "
                            f"{most_active['symbol']}."
                        ),
                    ],
                    metrics={
                        "direction": direction,
                        "ticker_count": (
                            len(normalized)
                        ),
                        (
                            "average_change_"
                            "percent_24h"
                        ): round(
                            average_change,
                            6,
                        ),
                        (
                            "performance_"
                            "dispersion_percent"
                        ): round(
                            dispersion,
                            6,
                        ),
                    },
                ),
                AIAnalysisSection(
                    title="Market Leaders",
                    summary=(
                        "Leadership is based on "
                        "24-hour price change and "
                        "turnover from the supplied "
                        "ticker snapshots."
                    ),
                    metrics={
                        "strongest": strongest,
                        "weakest": weakest,
                        "most_active": (
                            most_active
                        ),
                    },
                ),
            ],
            warnings=warnings,
            metadata=self._metadata(
                analysis_type="MARKET",
                data_sources=[
                    "USER_QUERY",
                    "MARKET_SCANNER",
                ],
                confidence_score=0.8,
            ),
            execution_allowed=False,
        )
    def analyze_portfolio(
        self,
        *,
        data: AIPortfolioAnalysisRequest,
        snapshot: (
            PortfolioSyncSnapshotResponse
        ),
    ) -> AIAnalysisResponse:
        equity = snapshot.total_equity_usd
        available = (
            snapshot
            .total_available_balance_usd
        )
        position_value = (
            snapshot
            .total_position_value_usd
        )
        unrealized_pnl = (
            snapshot
            .total_unrealized_pnl_usd
        )
        realized_pnl = (
            snapshot
            .total_realized_pnl_usd
        )
        if equity > 0:
            exposure_percent = (
                position_value
                / equity
                * 100
            )
            available_percent = (
                available
                / equity
                * 100
            )
        else:
            exposure_percent = 0.0
            available_percent = 0.0
        warnings = [
            self._advisory_warning(),
        ]
        if snapshot.status != "SUCCESS":
            warnings.append(
                AIAnalysisWarning(
                    code=(
                        "PORTFOLIO_SYNC_"
                        f"{snapshot.status}"
                    ),
                    severity="WARNING",
                    message=(
                        "The portfolio snapshot was "
                        "not completed with full "
                        "success."
                    ),
                )
            )
        if unrealized_pnl < 0:
            warnings.append(
                AIAnalysisWarning(
                    code="NEGATIVE_UNREALIZED_PNL",
                    severity="WARNING",
                    message=(
                        "Open positions currently "
                        "show a negative unrealized "
                        "profit and loss."
                    ),
                )
            )
        if exposure_percent >= 80:
            warnings.append(
                AIAnalysisWarning(
                    code="HIGH_PORTFOLIO_EXPOSURE",
                    severity="CRITICAL",
                    message=(
                        "Position value is at least "
                        "80 percent of total equity."
                    ),
                )
            )
        if (
            equity > 0
            and available_percent <= 10
        ):
            warnings.append(
                AIAnalysisWarning(
                    code="LOW_AVAILABLE_BALANCE",
                    severity="WARNING",
                    message=(
                        "Available balance is 10 "
                        "percent or less of equity."
                    ),
                )
            )
        status = (
            "SUCCESS"
            if snapshot.status == "SUCCESS"
            else "PARTIAL"
        )
        return AIAnalysisResponse(
            status=status,
            answer=(
                "The portfolio contains "
                f"{snapshot.open_position_count} "
                "open position(s), "
                f"{snapshot.open_order_count} "
                "open order(s), and estimated "
                f"position exposure of "
                f"{exposure_percent:.2f}%."
            ),
            sections=[
                AIAnalysisSection(
                    title="Portfolio Value",
                    summary=(
                        "Current portfolio value "
                        "and liquidity summary."
                    ),
                    metrics={
                        "total_equity_usd": equity,
                        (
                            "total_wallet_"
                            "balance_usd"
                        ): (
                            snapshot
                            .total_wallet_balance_usd
                        ),
                        (
                            "total_available_"
                            "balance_usd"
                        ): available,
                        (
                            "available_balance_"
                            "percent"
                        ): round(
                            available_percent,
                            6,
                        ),
                    },
                ),
                AIAnalysisSection(
                    title="Portfolio Exposure",
                    summary=(
                        "Open-position value and "
                        "profit-and-loss summary."
                    ),
                    metrics={
                        (
                            "total_position_"
                            "value_usd"
                        ): position_value,
                        (
                            "position_exposure_"
                            "percent"
                        ): round(
                            exposure_percent,
                            6,
                        ),
                        (
                            "unrealized_pnl_usd"
                        ): unrealized_pnl,
                        "realized_pnl_usd": (
                            realized_pnl
                        ),
                        "open_positions": (
                            snapshot
                            .open_position_count
                        ),
                        "open_orders": (
                            snapshot
                            .open_order_count
                        ),
                    },
                ),
            ],
            warnings=warnings,
            metadata=self._metadata(
                analysis_type="PORTFOLIO",
                data_sources=[
                    "USER_QUERY",
                    "PORTFOLIO",
                ],
                confidence_score=(
                    0.9
                    if snapshot.status
                    == "SUCCESS"
                    else 0.6
                ),
            ),
            execution_allowed=False,
        )
    def explain_risk(
        self,
        data: AIRiskExplanationRequest,
    ) -> AIAnalysisResponse:
        risk_result = data.risk_result
        check_points = [
            (
                f"{'PASS' if check.passed else 'FAIL'}: "
                f"{check.rule} - {check.message}"
            )
            for check in risk_result.checks
        ]
        warnings = [
            self._advisory_warning(),
        ]
        for warning in risk_result.warnings:
            warnings.append(
                AIAnalysisWarning(
                    code="RISK_ENGINE_WARNING",
                    severity="WARNING",
                    message=warning,
                )
            )
        for reason in (
            risk_result
            .rejection_reasons
        ):
            warnings.append(
                AIAnalysisWarning(
                    code="RISK_CHECK_FAILED",
                    severity="CRITICAL",
                    message=reason,
                )
            )
        if risk_result.accepted:
            answer = (
                "The trade passed the configured "
                "pre-trade risk checks."
            )
        else:
            answer = (
                "The trade was rejected by the "
                "configured risk-management rules."
            )
        return AIAnalysisResponse(
            status="SUCCESS",
            answer=answer,
            sections=[
                AIAnalysisSection(
                    title="Risk Decision",
                    summary=risk_result.summary,
                    bullet_points=check_points,
                    metrics={
                        "accepted": (
                            risk_result.accepted
                        ),
                        "side": risk_result.side,
                        (
                            "risk_reward_ratio"
                        ): (
                            risk_result
                            .risk_reward_ratio
                        ),
                        (
                            "projected_total_"
                            "exposure_percent"
                        ): (
                            risk_result
                            .projected_total_exposure_percent
                        ),
                        (
                            "current_daily_"
                            "loss_percent"
                        ): (
                            risk_result
                            .current_daily_loss_percent
                        ),
                        (
                            "current_drawdown_"
                            "percent"
                        ): (
                            risk_result
                            .current_drawdown_percent
                        ),
                    },
                ),
            ],
            warnings=warnings,
            metadata=self._metadata(
                analysis_type="RISK",
                data_sources=[
                    "USER_QUERY",
                    "RISK_ENGINE",
                ],
                confidence_score=1.0,
            ),
            execution_allowed=False,
        )
    def build_trade_plan(
        self,
        data: AITradePlanRequest,
    ) -> AIAnalysisResponse:
        entry = (
            data.reference_entry_price
        )
        stop = (
            data
            .reference_stop_loss_price
        )
        target = (
            data
            .reference_take_profit_price
        )
        risk_reward_ratio = None
        if (
            entry is not None
            and stop is not None
            and target is not None
        ):
            risk_distance = abs(
                entry - stop
            )
            reward_distance = abs(
                target - entry
            )
            if risk_distance > 0:
                risk_reward_ratio = (
                    reward_distance
                    / risk_distance
                )
        if data.side == "BUY":
            thesis = (
                f"A BUY plan for {data.symbol} "
                "requires bullish confirmation "
                "and price holding above its "
                "invalidation level."
            )
            direction_condition = (
                "Confirm buyers remain in control "
                "before considering an entry."
            )
        else:
            thesis = (
                f"A SELL plan for {data.symbol} "
                "requires bearish confirmation "
                "and price remaining below its "
                "invalidation level."
            )
            direction_condition = (
                "Confirm sellers remain in control "
                "before considering an entry."
            )
        entry_conditions = [
            direction_condition,
            (
                "Check current volatility and "
                "liquidity before entry."
            ),
            (
                "Revalidate the plan with the "
                "risk engine before any order."
            ),
        ]
        if entry is not None:
            entry_conditions.append(
                (
                    "Observe price behavior near "
                    f"the reference entry "
                    f"{entry}."
                )
            )
        risk_warnings = [
            (
                "This plan is advisory only and "
                "cannot execute an order."
            ),
            (
                "Market conditions can change "
                "after the plan is generated."
            ),
        ]
        if (
            data.maximum_risk_percent
            is not None
        ):
            risk_warnings.append(
                (
                    "Requested maximum risk is "
                    f"{data.maximum_risk_percent}%."
                )
            )
        warnings = [
            self._advisory_warning(),
        ]
        levels_complete = all(
            value is not None
            for value in (
                entry,
                stop,
                target,
            )
        )
        if not levels_complete:
            warnings.append(
                AIAnalysisWarning(
                    code=(
                        "REFERENCE_LEVELS_"
                        "INCOMPLETE"
                    ),
                    severity="WARNING",
                    message=(
                        "A complete entry, stop-loss, "
                        "and take-profit set was not "
                        "provided."
                    ),
                )
            )
        trade_plan = AITradePlan(
            symbol=data.symbol,
            side=data.side,
            category=data.category,
            thesis=thesis,
            entry_conditions=(
                entry_conditions
            ),
            stop_loss_reasoning=(
                "The stop-loss should define "
                "the point where the trade "
                "thesis is no longer valid."
            ),
            take_profit_reasoning=(
                "The take-profit should provide "
                "adequate reward relative to "
                "the defined stop distance."
            ),
            invalidation_conditions=[
                (
                    "The required directional "
                    "confirmation disappears."
                ),
                (
                    "The risk engine rejects the "
                    "proposed trade."
                ),
                (
                    "Volatility or liquidity "
                    "changes materially."
                ),
            ],
            risk_warnings=risk_warnings,
            reference_entry_price=entry,
            reference_stop_loss_price=stop,
            reference_take_profit_price=(
                target
            ),
            estimated_risk_reward_ratio=(
                risk_reward_ratio
            ),
            advisory_only=True,
            execution_enabled=False,
        )
        return AIAnalysisResponse(
            status=(
                "SUCCESS"
                if levels_complete
                else "PARTIAL"
            ),
            answer=(
                f"An advisory {data.side} "
                f"trade plan was prepared for "
                f"{data.symbol}."
            ),
            sections=[
                AIAnalysisSection(
                    title="Trade Thesis",
                    summary=thesis,
                    bullet_points=(
                        entry_conditions
                    ),
                    metrics={
                        "symbol": data.symbol,
                        "side": data.side,
                        "category": (
                            data.category
                        ),
                        "reference_entry": entry,
                        "reference_stop": stop,
                        "reference_target": (
                            target
                        ),
                        (
                            "estimated_risk_"
                            "reward_ratio"
                        ): risk_reward_ratio,
                    },
                ),
            ],
            warnings=warnings,
            metadata=self._metadata(
                analysis_type="TRADE_PLAN",
                data_sources=[
                    "USER_QUERY",
                    "RISK_ENGINE",
                ],
                confidence_score=(
                    0.75
                    if levels_complete
                    else 0.45
                ),
            ),
            trade_plan=trade_plan,
            execution_allowed=False,
        )
    def explain_arbitrage(
        self,
        data: AIArbitrageExplanationRequest,
    ) -> AIAnalysisResponse:
        opportunity = (
            self._to_mapping(
                data.opportunity
            )
        )
        gross_spread_percent = (
            self._first_number(
                opportunity,
                "gross_spread_percent",
                "raw_spread_percent",
                "spread_percent",
            )
        )
        net_profit = self._first_number(
            opportunity,
            "net_profit",
            "estimated_net_profit",
            "profit",
        )
        net_profit_percent = (
            self._first_number(
                opportunity,
                "net_profit_percent",
                "profit_percent",
                "net_return_percent",
            )
        )
        estimated_fees = (
            self._first_number(
                opportunity,
                "estimated_fees",
                "total_fees",
                "fees",
            )
        )
        estimated_slippage = (
            self._first_number(
                opportunity,
                "estimated_slippage",
                "slippage",
                "slippage_cost",
            )
        )
        network_cost = (
            self._first_number(
                opportunity,
                "network_cost",
                "estimated_network_cost",
            )
        )
        warnings = [
            self._advisory_warning(),
            AIAnalysisWarning(
                code="EXECUTION_RISK",
                severity="WARNING",
                message=(
                    "Arbitrage profitability may "
                    "change before all legs are "
                    "executed."
                ),
            ),
        ]
        if net_profit_percent is None:
            status = "PARTIAL"
            answer = (
                "The opportunity was received, "
                "but a normalized net-profit "
                "percentage was not available."
            )
            warnings.append(
                AIAnalysisWarning(
                    code=(
                        "NET_PROFITABILITY_"
                        "MISSING"
                    ),
                    severity="WARNING",
                    message=(
                        "The opportunity should "
                        "include fee-adjusted net "
                        "profitability."
                    ),
                )
            )
        elif net_profit_percent > 0:
            status = "SUCCESS"
            answer = (
                "The supplied opportunity has "
                "positive estimated net "
                "profitability."
            )
        else:
            status = "SUCCESS"
            answer = (
                "The supplied opportunity is "
                "not profitable after the "
                "reported adjustments."
            )
            warnings.append(
                AIAnalysisWarning(
                    code="NOT_PROFITABLE",
                    severity="CRITICAL",
                    message=(
                        "Estimated net profitability "
                        "is zero or negative."
                    ),
                )
            )
        metrics = {
            "opportunity_type": (
                data.opportunity_type
            ),
            "gross_spread_percent": (
                gross_spread_percent
            ),
            "net_profit": net_profit,
            "net_profit_percent": (
                net_profit_percent
            ),
            "estimated_fees": (
                estimated_fees
            ),
            "estimated_slippage": (
                estimated_slippage
            ),
            "network_cost": network_cost,
        }
        return AIAnalysisResponse(
            status=status,
            answer=answer,
            sections=[
                AIAnalysisSection(
                    title="Arbitrage Economics",
                    summary=(
                        "The opportunity is assessed "
                        "using the supplied spread, "
                        "cost, and net-profit fields."
                    ),
                    metrics=metrics,
                ),
                AIAnalysisSection(
                    title="Execution Considerations",
                    summary=(
                        "Execution timing, liquidity, "
                        "fees, slippage, and leg risk "
                        "can change the final result."
                    ),
                    bullet_points=[
                        (
                            "Confirm prices are still "
                            "available before execution."
                        ),
                        (
                            "Confirm all fees and "
                            "network costs."
                        ),
                        (
                            "Do not treat gross spread "
                            "as final profit."
                        ),
                    ],
                ),
            ],
            warnings=warnings,
            metadata=self._metadata(
                analysis_type="ARBITRAGE",
                data_sources=[
                    "USER_QUERY",
                    "ARBITRAGE_ENGINE",
                ],
                confidence_score=(
                    0.8
                    if net_profit_percent
                    is not None
                    else 0.4
                ),
            ),
            execution_allowed=False,
        )
