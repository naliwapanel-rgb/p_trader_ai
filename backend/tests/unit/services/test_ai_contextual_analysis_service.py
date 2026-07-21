from datetime import (
    UTC,
    datetime,
)
from types import (
    SimpleNamespace,
)
from unittest.mock import (
    Mock,
)
from app.schemas.ai_assistant import (
    AIAnalysisMetadata,
    AIAnalysisResponse,
    AIAnalysisSection,
    AIAssistantRequest,
)
from app.schemas.ai_context import (
    AIAutomationContext,
    AIPortfolioSnapshotContext,
    AIUserContextResponse,
)
from app.schemas.alert import (
    AlertResponse,
)
from app.schemas.exchange_account import (
    ExchangeAccountResponse,
)
from app.schemas.risk_management import (
    RiskConfiguration,
)
from app.schemas.watchlist import (
    WatchlistResponse,
)
from app.services.ai_contextual_analysis_service import (
    AIContextAwareAnalysisService,
)
def _now():
    return datetime.now(UTC)
def _base_analysis_response(
    *,
    analysis_type="GENERAL",
):
    return AIAnalysisResponse(
        status="SUCCESS",
        answer="Base analysis.",
        sections=[
            AIAnalysisSection(
                title="Base Analysis",
                summary=(
                    "Deterministic base "
                    "analysis result."
                ),
            ),
        ],
        warnings=[],
        metadata=AIAnalysisMetadata(
            analysis_type=analysis_type,
            generated_at_ms=1,
            confidence_score=0.8,
            data_sources=[
                "USER_QUERY",
            ],
            provider="DETERMINISTIC",
            advisory_only=True,
            execution_enabled=False,
        ),
        execution_allowed=False,
    )
def _snapshot():
    return AIPortfolioSnapshotContext(
        id=60,
        user_id=7,
        portfolio_id=10,
        exchange_account_id=40,
        exchange_name="BYBIT",
        account_type="UNIFIED",
        category="linear",
        settle_coin="USDT",
        status="SUCCESS",
        total_equity_usd=1000,
        total_wallet_balance_usd=950,
        total_available_balance_usd=400,
        total_unrealized_pnl_usd=25,
        total_realized_pnl_usd=10,
        total_position_value_usd=500,
        coin_count=2,
        open_position_count=1,
        open_order_count=1,
        balance_payload={},
        positions_payload=[],
        orders_payload=[],
        error_message=None,
        synced_at=_now(),
        created_at=_now(),
    )
def _context(
    *,
    include_snapshot=False,
    include_watchlist=False,
    include_alert=False,
    include_account=False,
    account_active=True,
    trading_enabled=True,
    include_automation=False,
    automation_healthy=True,
):
    watchlist = []
    if include_watchlist:
        watchlist = [
            WatchlistResponse(
                id=20,
                user_id=7,
                symbol="BTCUSDT",
                exchange="BYBIT",
                created_at=_now(),
            ),
        ]
    alerts = []
    if include_alert:
        alerts = [
            AlertResponse(
                id=30,
                user_id=7,
                symbol="BTCUSDT",
                exchange="BYBIT",
                alert_type="ABOVE",
                target_value=100000,
                is_enabled=True,
                triggered=False,
                created_at=_now(),
            ),
        ]
    accounts = []
    if include_account:
        accounts = [
            ExchangeAccountResponse(
                id=40,
                user_id=7,
                exchange_name="BYBIT",
                account_name="Primary",
                is_testnet=True,
                is_active=account_active,
                created_at=_now(),
            ),
        ]
    automation = None
    if include_automation:
        automation = AIAutomationContext(
            available=True,
            healthy=automation_healthy,
            started=automation_healthy,
            handlers_registered=True,
            worker_running=(
                automation_healthy
            ),
            accepting_jobs=(
                automation_healthy
            ),
        )
    snapshot = (
        _snapshot()
        if include_snapshot
        else None
    )
    return AIUserContextResponse(
        user_id=7,
        generated_at_ms=123456789,
        portfolios=[],
        selected_portfolio=None,
        latest_portfolio_snapshot=(
            snapshot
        ),
        watchlist=watchlist,
        alerts=alerts,
        exchange_accounts=accounts,
        selected_exchange_account=None,
        notification_preferences=None,
        risk_configuration=(
            RiskConfiguration(
                trading_enabled=(
                    trading_enabled
                )
            )
        ),
        automation=automation,
        data_sources=[
            "RISK_ENGINE",
        ],
        portfolio_count=0,
        watchlist_count=len(watchlist),
        alert_count=len(alerts),
        exchange_account_count=(
            len(accounts)
        ),
        advisory_only=True,
        execution_enabled=False,
    )
def _service(context):
    context_builder = Mock()
    context_builder.build.return_value = (
        context
    )
    analysis_service = Mock()
    service = AIContextAwareAnalysisService(
        context_builder=context_builder,
        analysis_service=analysis_service,
    )
    return (
        service,
        context_builder,
        analysis_service,
    )
def test_context_can_be_disabled():
    service, context_builder, analysis = (
        _service(_context())
    )
    expected = _base_analysis_response()
    analysis.answer_general.return_value = (
        expected
    )
    request = AIAssistantRequest(
        question="Review my account.",
        include_user_context=False,
    )
    result = service.analyze(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=request,
    )
    assert result is expected
    context_builder.build.assert_not_called()
    analysis.answer_general.assert_called_once_with(
        request
    )
def test_general_query_uses_authenticated_context():
    service, context_builder, _ = (
        _service(
            _context(
                include_watchlist=True,
                include_alert=True,
                include_account=True,
                include_automation=True,
            )
        )
    )
    user = SimpleNamespace(id=7)
    result = service.analyze(
        current_user=user,
        request=AIAssistantRequest(
            question="Review my account."
        ),
    )
    assert result.status == "SUCCESS"
    assert result.execution_allowed is False
    assert (
        result.metadata.generated_at_ms
        == 123456789
    )
    context_builder.build.assert_called_once()
    call = (
        context_builder
        .build
        .call_args
        .kwargs
    )
    assert call["current_user"] is user
def test_portfolio_query_uses_snapshot_analysis():
    service, _, analysis = (
        _service(
            _context(
                include_snapshot=True,
                include_account=True,
            )
        )
    )
    analysis.analyze_portfolio.return_value = (
        _base_analysis_response(
            analysis_type="PORTFOLIO"
        )
    )
    result = service.analyze(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIAssistantRequest(
            question="Review my portfolio.",
            analysis_type="PORTFOLIO",
            portfolio_id=10,
            exchange_account_id=40,
        ),
    )
    assert result.status == "SUCCESS"
    assert (
        result.metadata.analysis_type
        == "PORTFOLIO"
    )
    assert (
        result.metadata.generated_at_ms
        == 123456789
    )
    analysis.analyze_portfolio.assert_called_once()
def test_portfolio_without_snapshot_is_partial():
    service, _, analysis = (
        _service(
            _context(
                include_account=True
            )
        )
    )
    result = service.analyze(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIAssistantRequest(
            question="Review my portfolio.",
            analysis_type="PORTFOLIO",
            portfolio_id=10,
        ),
    )
    warning_codes = {
        warning.code
        for warning in result.warnings
    }
    assert result.status == "PARTIAL"
    assert (
        "PORTFOLIO_SNAPSHOT_MISSING"
        in warning_codes
    )
    analysis.analyze_portfolio.assert_not_called()
def test_context_sources_are_mapped():
    service, _, _ = (
        _service(
            _context(
                include_snapshot=True,
                include_watchlist=True,
                include_alert=True,
                include_account=True,
                include_automation=True,
            )
        )
    )
    result = service.analyze(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIAssistantRequest(
            question="Review everything."
        ),
    )
    assert set(
        result.metadata.data_sources
    ) == {
        "USER_QUERY",
        "RISK_ENGINE",
        "PORTFOLIO",
        "WATCHLIST",
        "ALERTS",
        "AUTOMATION_RUNTIME",
    }
def test_no_active_account_adds_warning():
    service, _, _ = (
        _service(
            _context(
                include_account=True,
                account_active=False,
            )
        )
    )
    result = service.analyze(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIAssistantRequest(
            question="Review my account."
        ),
    )
    assert any(
        warning.code
        == "NO_ACTIVE_EXCHANGE_ACCOUNTS"
        for warning in result.warnings
    )
def test_trading_disabled_adds_critical_warning():
    service, _, _ = (
        _service(
            _context(
                trading_enabled=False
            )
        )
    )
    result = service.analyze(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIAssistantRequest(
            question="Review my account."
        ),
    )
    warning = next(
        warning
        for warning in result.warnings
        if warning.code
        == "TRADING_DISABLED"
    )
    assert warning.severity == "CRITICAL"
def test_unhealthy_automation_adds_warning():
    service, _, _ = (
        _service(
            _context(
                include_automation=True,
                automation_healthy=False,
            )
        )
    )
    result = service.analyze(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIAssistantRequest(
            question="Review automation."
        ),
    )
    assert any(
        warning.code
        == "AUTOMATION_RUNTIME_NOT_HEALTHY"
        for warning in result.warnings
    )
