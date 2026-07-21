import pytest
from pydantic import ValidationError
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
from app.schemas.risk_management import (
    PreTradeRiskResult,
)
def _risk_result() -> PreTradeRiskResult:
    return PreTradeRiskResult(
        accepted=True,
        side="BUY",
        risk_reward_ratio=2.0,
        projected_total_exposure_percent=25.0,
        current_daily_loss_percent=0.5,
        current_drawdown_percent=1.0,
        checks=[],
        rejection_reasons=[],
        warnings=[],
        summary="Trade passed risk validation.",
    )
def _trade_plan() -> AITradePlan:
    return AITradePlan(
        symbol="btcusdt",
        side="BUY",
        thesis="Momentum remains positive.",
        entry_conditions=[
            "Price holds above support.",
        ],
        stop_loss_reasoning=(
            "The stop is below invalidation."
        ),
        take_profit_reasoning=(
            "The target preserves reward."
        ),
        invalidation_conditions=[
            "Support breaks.",
        ],
        risk_warnings=[
            "Volatility may increase.",
        ],
        estimated_risk_reward_ratio=2.0,
    )
def test_assistant_request_normalizes_question_and_symbols():
    request = AIAssistantRequest(
        question="  Analyze my BTC position.  ",
        analysis_type="PORTFOLIO",
        symbols=[
            " btcusdt ",
            "BTCUSDT",
            "ethusdt",
        ],
    )
    assert (
        request.question
        == "Analyze my BTC position."
    )
    assert request.symbols == [
        "BTCUSDT",
        "ETHUSDT",
    ]
def test_assistant_request_rejects_blank_question():
    with pytest.raises(ValidationError):
        AIAssistantRequest(
            question="   "
        )
def test_market_request_requires_symbols():
    with pytest.raises(ValidationError):
        AIMarketAnalysisRequest(
            question="Analyze the market.",
            symbols=[],
        )
def test_portfolio_request_rejects_invalid_identifier():
    with pytest.raises(ValidationError):
        AIPortfolioAnalysisRequest(
            question="Review my portfolio.",
            portfolio_id=0,
        )
def test_risk_request_accepts_engine_result():
    request = AIRiskExplanationRequest(
        question=(
            "Explain why this trade passed."
        ),
        risk_result=_risk_result(),
    )
    assert request.risk_result.accepted is True
    assert (
        request.risk_result
        .risk_reward_ratio
        == 2.0
    )
def test_trade_plan_request_normalizes_symbol():
    request = AITradePlanRequest(
        question="Create a BTC plan.",
        symbol=" btcusdt ",
        side="BUY",
    )
    assert request.symbol == "BTCUSDT"
def test_trade_plan_request_requires_reference_for_levels():
    with pytest.raises(
        ValidationError,
        match="reference_entry_price",
    ):
        AITradePlanRequest(
            question="Create a BTC plan.",
            symbol="BTCUSDT",
            side="BUY",
            reference_stop_loss_price=95,
        )
def test_trade_plan_request_rejects_invalid_buy_levels():
    with pytest.raises(
        ValidationError,
        match="BUY reference stop-loss",
    ):
        AITradePlanRequest(
            question="Create a BTC plan.",
            symbol="BTCUSDT",
            side="BUY",
            reference_entry_price=100,
            reference_stop_loss_price=105,
            reference_take_profit_price=120,
        )
def test_trade_plan_request_rejects_invalid_sell_levels():
    with pytest.raises(
        ValidationError,
        match="SELL reference take-profit",
    ):
        AITradePlanRequest(
            question="Create a BTC plan.",
            symbol="BTCUSDT",
            side="SELL",
            reference_entry_price=100,
            reference_stop_loss_price=110,
            reference_take_profit_price=105,
        )
def test_arbitrage_request_rejects_empty_opportunity():
    with pytest.raises(
        ValidationError,
        match="opportunity cannot be empty",
    ):
        AIArbitrageExplanationRequest(
            question=(
                "Explain this opportunity."
            ),
            opportunity_type=(
                "CROSS_EXCHANGE"
            ),
            opportunity={},
        )
def test_warning_normalizes_code():
    warning = AIAnalysisWarning(
        code="high volatility",
        severity="WARNING",
        message="  Volatility is elevated. ",
    )
    assert warning.code == "HIGH_VOLATILITY"
    assert (
        warning.message
        == "Volatility is elevated."
    )
def test_section_normalizes_bullet_points():
    section = AIAnalysisSection(
        title=" Market Direction ",
        summary=" Momentum is positive. ",
        bullet_points=[
            " Higher highs ",
            "Higher highs",
            "Volume expanded",
        ],
    )
    assert section.title == "Market Direction"
    assert (
        section.summary
        == "Momentum is positive."
    )
    assert section.bullet_points == [
        "Higher highs",
        "Volume expanded",
    ]
def test_metadata_normalizes_sources_and_enforces_safety():
    metadata = AIAnalysisMetadata(
        analysis_type="MARKET",
        data_sources=[
            "USER_QUERY",
            "MARKET_SCANNER",
            "MARKET_SCANNER",
        ],
        provider=" deterministic ",
    )
    assert metadata.data_sources == [
        "USER_QUERY",
        "MARKET_SCANNER",
    ]
    assert metadata.provider == "DETERMINISTIC"
    assert metadata.advisory_only is True
    assert metadata.execution_enabled is False
    with pytest.raises(ValidationError):
        AIAnalysisMetadata(
            analysis_type="MARKET",
            execution_enabled=True,
        )
def test_trade_plan_enforces_advisory_only():
    plan = _trade_plan()
    assert plan.symbol == "BTCUSDT"
    assert plan.advisory_only is True
    assert plan.execution_enabled is False
    with pytest.raises(ValidationError):
        AITradePlan(
            symbol="BTCUSDT",
            side="BUY",
            thesis="Momentum is positive.",
            stop_loss_reasoning=(
                "Below invalidation."
            ),
            take_profit_reasoning=(
                "Above resistance."
            ),
            advisory_only=False,
        )
def test_response_requires_trade_plan_analysis_type():
    with pytest.raises(
        ValidationError,
        match=(
            "trade_plan requires metadata "
            "analysis_type TRADE_PLAN"
        ),
    ):
        AIAnalysisResponse(
            status="SUCCESS",
            answer="A trade plan was prepared.",
            metadata=AIAnalysisMetadata(
                analysis_type="MARKET",
            ),
            trade_plan=_trade_plan(),
        )
def test_response_accepts_safe_trade_plan():
    response = AIAnalysisResponse(
        status="SUCCESS",
        answer="A safe advisory plan was prepared.",
        sections=[
            AIAnalysisSection(
                title="Market Thesis",
                summary=(
                    "Momentum remains positive."
                ),
            ),
        ],
        warnings=[
            AIAnalysisWarning(
                code="ADVISORY_ONLY",
                severity="INFO",
                message=(
                    "This plan cannot execute "
                    "an order."
                ),
            ),
        ],
        metadata=AIAnalysisMetadata(
            analysis_type="TRADE_PLAN",
            confidence_score=0.75,
            data_sources=[
                "USER_QUERY",
                "MARKET_SCANNER",
                "RISK_ENGINE",
            ],
        ),
        trade_plan=_trade_plan(),
    )
    assert response.status == "SUCCESS"
    assert response.execution_allowed is False
    assert response.trade_plan is not None
    assert (
        response.trade_plan.execution_enabled
        is False
    )
