from typing import Any
from app.models.user import User
from app.schemas.ai_assistant import (
    AIAnalysisMetadata,
    AIAnalysisResponse,
    AIAnalysisSection,
    AIAnalysisWarning,
    AIDataSource,
    AIAssistantRequest,
    AIPortfolioAnalysisRequest,
)
from app.schemas.ai_context import (
    AIContextRequest,
    AIUserContextResponse,
)
from app.services.ai_analysis_service import (
    DeterministicAIAnalysisService,
)
from app.services.ai_context_service import (
    AIContextBuilderService,
)
class AIContextAwareAnalysisService:
    """
    Combine authenticated user context with the
    deterministic AI analysis foundation.
    The service is advisory only. It cannot submit
    automation jobs or execute exchange orders.
    """
    def __init__(
        self,
        *,
        context_builder: AIContextBuilderService,
        analysis_service: (
            DeterministicAIAnalysisService
            | None
        ) = None,
    ):
        self.context_builder = context_builder
        self.analysis_service = (
            analysis_service
            or DeterministicAIAnalysisService()
        )
    @staticmethod
    def _append_unique(
        values: list[Any],
        value: Any,
    ) -> None:
        if value not in values:
            values.append(value)
    def _data_sources(
        self,
        context: AIUserContextResponse,
    ) -> list[AIDataSource]:
        sources: list[AIDataSource] = [
            "USER_QUERY",
            "RISK_ENGINE",
        ]
        if (
            context.portfolios
            or context.latest_portfolio_snapshot
            is not None
        ):
            self._append_unique(
                sources,
                "PORTFOLIO",
            )
        if context.watchlist:
            self._append_unique(
                sources,
                "WATCHLIST",
            )
        if context.alerts:
            self._append_unique(
                sources,
                "ALERTS",
            )
        if context.automation is not None:
            self._append_unique(
                sources,
                "AUTOMATION_RUNTIME",
            )
        return sources
    @staticmethod
    def _merge_warnings(
        first: list[AIAnalysisWarning],
        second: list[AIAnalysisWarning],
    ) -> list[AIAnalysisWarning]:
        merged: list[AIAnalysisWarning] = []
        identities: set[
            tuple[str, str]
        ] = set()
        for warning in [
            *first,
            *second,
        ]:
            identity = (
                warning.code,
                warning.message,
            )
            if identity in identities:
                continue
            identities.add(identity)
            merged.append(warning)
        return merged
    @staticmethod
    def _context_warnings(
        context: AIUserContextResponse,
        request: AIAssistantRequest,
    ) -> list[AIAnalysisWarning]:
        warnings = [
            AIAnalysisWarning(
                code="ADVISORY_ONLY",
                severity="INFO",
                message=(
                    "Context-aware analysis is "
                    "advisory only and cannot "
                    "execute a trade."
                ),
            ),
        ]
        if context.portfolio_count == 0:
            warnings.append(
                AIAnalysisWarning(
                    code="NO_PORTFOLIOS",
                    severity="INFO",
                    message=(
                        "The authenticated user "
                        "does not currently have "
                        "a portfolio."
                    ),
                )
            )
        if (
            request.portfolio_id is not None
            and context
            .latest_portfolio_snapshot
            is None
        ):
            warnings.append(
                AIAnalysisWarning(
                    code=(
                        "PORTFOLIO_SNAPSHOT_"
                        "MISSING"
                    ),
                    severity="WARNING",
                    message=(
                        "No synchronization "
                        "snapshot is available "
                        "for the selected portfolio."
                    ),
                )
            )
        active_accounts = [
            account
            for account in (
                context.exchange_accounts
            )
            if account.is_active
        ]
        if not active_accounts:
            warnings.append(
                AIAnalysisWarning(
                    code=(
                        "NO_ACTIVE_EXCHANGE_"
                        "ACCOUNTS"
                    ),
                    severity="INFO",
                    message=(
                        "No active exchange account "
                        "is available in the current "
                        "user context."
                    ),
                )
            )
        if (
            not context
            .risk_configuration
            .trading_enabled
        ):
            warnings.append(
                AIAnalysisWarning(
                    code="TRADING_DISABLED",
                    severity="CRITICAL",
                    message=(
                        "Trading is disabled by the "
                        "authenticated user's risk "
                        "configuration."
                    ),
                )
            )
        if (
            context.automation is not None
            and not context.automation.healthy
        ):
            warnings.append(
                AIAnalysisWarning(
                    code=(
                        "AUTOMATION_RUNTIME_"
                        "NOT_HEALTHY"
                    ),
                    severity="WARNING",
                    message=(
                        "The automation runtime "
                        "is not currently healthy."
                    ),
                )
            )
        return warnings
    @staticmethod
    def _context_sections(
        context: AIUserContextResponse,
    ) -> list[AIAnalysisSection]:
        active_accounts = [
            account
            for account in (
                context.exchange_accounts
            )
            if account.is_active
        ]
        sections = [
            AIAnalysisSection(
                title="Authenticated Context",
                summary=(
                    "Summary of the resources "
                    "available to the authenticated "
                    "user."
                ),
                metrics={
                    "user_id": context.user_id,
                    "portfolio_count": (
                        context.portfolio_count
                    ),
                    "watchlist_count": (
                        context.watchlist_count
                    ),
                    "alert_count": (
                        context.alert_count
                    ),
                    (
                        "exchange_account_"
                        "count"
                    ): (
                        context
                        .exchange_account_count
                    ),
                    (
                        "active_exchange_"
                        "account_count"
                    ): len(active_accounts),
                    "selected_portfolio_id": (
                        context
                        .selected_portfolio.id
                        if context
                        .selected_portfolio
                        is not None
                        else None
                    ),
                    (
                        "selected_exchange_"
                        "account_id"
                    ): (
                        context
                        .selected_exchange_account
                        .id
                        if context
                        .selected_exchange_account
                        is not None
                        else None
                    ),
                },
            ),
            AIAnalysisSection(
                title="Risk Configuration",
                summary=(
                    "Current authenticated-user "
                    "risk limits."
                ),
                metrics=(
                    context
                    .risk_configuration
                    .model_dump(
                        mode="json"
                    )
                ),
            ),
        ]
        snapshot = (
            context
            .latest_portfolio_snapshot
        )
        if snapshot is not None:
            sections.append(
                AIAnalysisSection(
                    title="Portfolio Snapshot",
                    summary=(
                        "Latest synchronized "
                        "portfolio position and "
                        "balance summary."
                    ),
                    metrics={
                        "portfolio_id": (
                            snapshot.portfolio_id
                        ),
                        (
                            "exchange_account_"
                            "id"
                        ): (
                            snapshot
                            .exchange_account_id
                        ),
                        "status": snapshot.status,
                        "total_equity_usd": (
                            snapshot
                            .total_equity_usd
                        ),
                        (
                            "total_available_"
                            "balance_usd"
                        ): (
                            snapshot
                            .total_available_balance_usd
                        ),
                        (
                            "total_position_"
                            "value_usd"
                        ): (
                            snapshot
                            .total_position_value_usd
                        ),
                        (
                            "total_unrealized_"
                            "pnl_usd"
                        ): (
                            snapshot
                            .total_unrealized_pnl_usd
                        ),
                        (
                            "open_position_"
                            "count"
                        ): (
                            snapshot
                            .open_position_count
                        ),
                        "open_order_count": (
                            snapshot
                            .open_order_count
                        ),
                    },
                )
            )
        if context.watchlist:
            sections.append(
                AIAnalysisSection(
                    title="Watchlist Context",
                    summary=(
                        "Symbols currently being "
                        "followed by the user."
                    ),
                    bullet_points=[
                        (
                            f"{item.exchange}: "
                            f"{item.symbol}"
                        )
                        for item in (
                            context.watchlist[:50]
                        )
                    ],
                    metrics={
                        "watchlist_count": (
                            context
                            .watchlist_count
                        ),
                    },
                )
            )
        if context.alerts:
            enabled_alerts = [
                alert
                for alert in context.alerts
                if alert.is_enabled
            ]
            triggered_alerts = [
                alert
                for alert in context.alerts
                if alert.triggered
            ]
            sections.append(
                AIAnalysisSection(
                    title="Alert Context",
                    summary=(
                        "Configured price and "
                        "market alert status."
                    ),
                    bullet_points=[
                        (
                            f"{alert.exchange} "
                            f"{alert.symbol}: "
                            f"{alert.alert_type} "
                            f"{alert.target_value}"
                        )
                        for alert in (
                            context.alerts[:50]
                        )
                    ],
                    metrics={
                        "alert_count": (
                            context.alert_count
                        ),
                        (
                            "enabled_alert_"
                            "count"
                        ): len(enabled_alerts),
                        (
                            "triggered_alert_"
                            "count"
                        ): len(
                            triggered_alerts
                        ),
                    },
                )
            )
        if context.automation is not None:
            sections.append(
                AIAnalysisSection(
                    title="Automation Runtime",
                    summary=(
                        "Read-only automation "
                        "runtime health summary."
                    ),
                    metrics={
                        "healthy": (
                            context
                            .automation.healthy
                        ),
                        "started": (
                            context
                            .automation.started
                        ),
                        (
                            "handlers_"
                            "registered"
                        ): (
                            context
                            .automation
                            .handlers_registered
                        ),
                        (
                            "worker_running"
                        ): (
                            context
                            .automation
                            .worker_running
                        ),
                        (
                            "accepting_jobs"
                        ): (
                            context
                            .automation
                            .accepting_jobs
                        ),
                    },
                )
            )
        return sections
    @staticmethod
    def _answer_for_type(
        analysis_type: str,
    ) -> str:
        answers = {
            "GENERAL": (
                "The authenticated user context "
                "was reviewed successfully. "
                "No trade or automation job "
                "was created."
            ),
            "MARKET": (
                "Authenticated account context "
                "is available, but current ticker "
                "data is required for a complete "
                "market analysis."
            ),
            "PORTFOLIO": (
                "Portfolio context is available, "
                "but a synchronized portfolio "
                "snapshot is required for a "
                "complete portfolio analysis."
            ),
            "RISK": (
                "The user's configured risk limits "
                "are available, but a specific "
                "pre-trade risk result is required "
                "for a complete explanation."
            ),
            "TRADE_PLAN": (
                "Authenticated context is "
                "available, but a validated symbol, "
                "side, and reference levels are "
                "required for a trade plan."
            ),
            "ARBITRAGE": (
                "Authenticated context is "
                "available, but a normalized "
                "arbitrage opportunity is required "
                "for complete analysis."
            ),
        }
        return answers[analysis_type]
    def analyze(
        self,
        *,
        current_user: User,
        request: AIAssistantRequest,
    ) -> AIAnalysisResponse:
        if not request.include_user_context:
            return (
                self.analysis_service
                .answer_general(request)
            )
        context = self.context_builder.build(
            current_user=current_user,
            request=AIContextRequest(
                portfolio_id=(
                    request.portfolio_id
                ),
                exchange_account_id=(
                    request
                    .exchange_account_id
                ),
                include_automation=True,
            ),
        )
        context_sections = (
            self._context_sections(
                context
            )
        )
        context_warnings = (
            self._context_warnings(
                context,
                request,
            )
        )
        sources = self._data_sources(
            context
        )
        if (
            request.analysis_type
            == "PORTFOLIO"
            and context
            .latest_portfolio_snapshot
            is not None
        ):
            portfolio_request = (
                AIPortfolioAnalysisRequest(
                    question=request.question,
                    portfolio_id=(
                        request.portfolio_id
                    ),
                    exchange_account_id=(
                        request
                        .exchange_account_id
                    ),
                )
            )
            base_response = (
                self.analysis_service
                .analyze_portfolio(
                    data=portfolio_request,
                    snapshot=(
                        context
                        .latest_portfolio_snapshot
                    ),
                )
            )
            metadata = (
                base_response.metadata
                .model_copy(
                    update={
                        "generated_at_ms": (
                            context
                            .generated_at_ms
                        ),
                        "confidence_score": min(
                            1.0,
                            (
                                base_response
                                .metadata
                                .confidence_score
                                + 0.05
                            ),
                        ),
                        "data_sources": sources,
                    }
                )
            )
            return base_response.model_copy(
                update={
                    "sections": [
                        *base_response.sections,
                        *context_sections,
                    ],
                    "warnings": (
                        self._merge_warnings(
                            base_response.warnings,
                            context_warnings,
                        )
                    ),
                    "metadata": metadata,
                    "execution_allowed": False,
                }
            )
        warnings = list(
            context_warnings
        )
        if request.analysis_type != "GENERAL":
            warnings.append(
                AIAnalysisWarning(
                    code=(
                        "DOMAIN_DATA_REQUIRED"
                    ),
                    severity="INFO",
                    message=(
                        "Use the dedicated domain "
                        "analysis endpoint with its "
                        "validated market, risk, "
                        "trade-plan, or arbitrage "
                        "payload."
                    ),
                )
            )
        return AIAnalysisResponse(
            status=(
                "SUCCESS"
                if request.analysis_type
                == "GENERAL"
                else "PARTIAL"
            ),
            answer=self._answer_for_type(
                request.analysis_type
            ),
            sections=context_sections,
            warnings=warnings,
            metadata=AIAnalysisMetadata(
                analysis_type=(
                    request.analysis_type
                ),
                generated_at_ms=(
                    context.generated_at_ms
                ),
                confidence_score=(
                    0.8
                    if request.analysis_type
                    == "GENERAL"
                    else 0.55
                ),
                data_sources=sources,
                provider="DETERMINISTIC",
                model_name=None,
                advisory_only=True,
                execution_enabled=False,
            ),
            execution_allowed=False,
        )
