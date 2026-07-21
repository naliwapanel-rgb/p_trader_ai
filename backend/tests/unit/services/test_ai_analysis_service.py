from datetime import (
    UTC,
    datetime,
)
from app.schemas.ai_assistant import (
    AIArbitrageExplanationRequest,
    AIAssistantRequest,
    AIMarketAnalysisRequest,
    AIPortfolioAnalysisRequest,
    AIRiskExplanationRequest,
    AITradePlanRequest,
)
from app.schemas.portfolio_sync import (
    PortfolioSyncSnapshotResponse,
)
from app.schemas.risk_management import (
    PreTradeRiskResult,
    RiskLimitCheck,
)
from app.services.ai_analysis_service import (
    DeterministicAIAnalysisService,
)
def _service():
    return DeterministicAIAnalysisService(
        clock_ms=lambda: 123456789
    )
def _snapshot(
    *,
    status="SUCCESS",
    equity=1000.0,
    available=400.0,
    position_value=500.0,
    unrealized_pnl=25.0,
):
    now = datetime.now(UTC)
    return PortfolioSyncSnapshotResponse(
        id=1,
        user_id=7,
        portfolio_id=2,
        exchange_account_id=3,
        exchange_name="BYBIT",
        account_type="UNIFIED",
        category="linear",
        settle_coin="USDT",
        status=status,
        fingerprint="a" * 64,
        sync_version=1,
        total_equity_usd=equity,
        total_wallet_balance_usd=950.0,
        total_available_balance_usd=(
            available
        ),
        total_unrealized_pnl_usd=(
            unrealized_pnl
        ),
        total_realized_pnl_usd=10.0,
        total_position_value_usd=(
            position_value
        ),
        coin_count=2,
        open_position_count=2,
        open_order_count=1,
        balance_payload={},
        positions_payload=[],
        orders_payload=[],
        error_message=None,
        synced_at=now,
        created_at=now,
    )
def _accepted_risk_result():
    return PreTradeRiskResult(
        accepted=True,
        side="BUY",
        risk_reward_ratio=2.0,
        projected_total_exposure_percent=35.0,
        current_daily_loss_percent=1.0,
        current_drawdown_percent=2.0,
        checks=[
            RiskLimitCheck(
                rule="MAX_LEVERAGE",
                passed=True,
                actual_value=3.0,
                limit_value=10.0,
                message=(
                    "Leverage is within the "
                    "configured limit"
                ),
            ),
        ],
        rejection_reasons=[],
        warnings=[],
        summary=(
            "Trade passed all configured "
            "pre-trade risk checks"
        ),
    )
def _rejected_risk_result():
    return PreTradeRiskResult(
        accepted=False,
        side="SELL",
        risk_reward_ratio=0.5,
        projected_total_exposure_percent=120.0,
        current_daily_loss_percent=6.0,
        current_drawdown_percent=10.0,
        checks=[
            RiskLimitCheck(
                rule="MINIMUM_RISK_REWARD",
                passed=False,
                actual_value=0.5,
                limit_value=1.5,
                message=(
                    "Risk/reward ratio is below "
                    "the configured minimum"
                ),
            ),
        ],
        rejection_reasons=[
            (
                "Risk/reward ratio is below "
                "the configured minimum"
            ),
        ],
        warnings=[
            "Exposure is near its maximum.",
        ],
        summary=(
            "Trade rejected by 1 risk check"
        ),
    )
def test_general_answer_is_partial_and_safe():
    response = _service().answer_general(
        AIAssistantRequest(
            question=(
                "What should I review?"
            ),
            symbols=["BTCUSDT"],
        )
    )
    assert response.status == "PARTIAL"
    assert (
        response.execution_allowed
        is False
    )
    assert (
        response.metadata
        .execution_enabled
        is False
    )
def test_metadata_uses_injected_clock():
    response = _service().answer_general(
        AIAssistantRequest(
            question="Review the market."
        )
    )
    assert (
        response.metadata
        .generated_at_ms
        == 123456789
    )
def test_market_analysis_finds_leaders():
    response = _service().analyze_market(
        data=AIMarketAnalysisRequest(
            question="Analyze these assets.",
            symbols=[
                "BTCUSDT",
                "ETHUSDT",
                "SOLUSDT",
            ],
        ),
        tickers=[
            {
                "symbol": "BTCUSDT",
                "last_price": 100,
                (
                    "price_change_"
                    "percent_24h"
                ): 2.5,
                "volume_24h": 1000,
                "turnover_24h": 5000,
            },
            {
                "symbol": "ETHUSDT",
                "last_price": 50,
                (
                    "price_change_"
                    "percent_24h"
                ): -1.0,
                "volume_24h": 1200,
                "turnover_24h": 4000,
            },
            {
                "symbol": "SOLUSDT",
                "last_price": 20,
                (
                    "price_change_"
                    "percent_24h"
                ): 5.0,
                "volume_24h": 1500,
                "turnover_24h": 3000,
            },
        ],
    )
    metrics = response.sections[1].metrics
    assert response.status == "SUCCESS"
    assert (
        metrics["strongest"]["symbol"]
        == "SOLUSDT"
    )
    assert (
        metrics["weakest"]["symbol"]
        == "ETHUSDT"
    )
    assert (
        metrics["most_active"]["symbol"]
        == "BTCUSDT"
    )
def test_market_analysis_filters_unrequested_symbols():
    response = _service().analyze_market(
        data=AIMarketAnalysisRequest(
            question="Analyze BTC.",
            symbols=["BTCUSDT"],
        ),
        tickers=[
            {
                "symbol": "BTCUSDT",
                "last_price": 100,
                (
                    "price_change_"
                    "percent_24h"
                ): 1.0,
                "turnover_24h": 1000,
            },
            {
                "symbol": "ETHUSDT",
                "last_price": 50,
                (
                    "price_change_"
                    "percent_24h"
                ): 20.0,
                "turnover_24h": 5000,
            },
        ],
    )
    assert (
        response.sections[0]
        .metrics["ticker_count"]
        == 1
    )
    assert (
        response.sections[1]
        .metrics["strongest"]["symbol"]
        == "BTCUSDT"
    )
def test_market_analysis_handles_missing_data():
    response = _service().analyze_market(
        data=AIMarketAnalysisRequest(
            question="Analyze BTC.",
            symbols=["BTCUSDT"],
        ),
        tickers=[],
    )
    assert response.status == "UNAVAILABLE"
    assert (
        response.warnings[0].code
        == "MARKET_DATA_MISSING"
    )
def test_portfolio_analysis_calculates_exposure():
    response = _service().analyze_portfolio(
        data=AIPortfolioAnalysisRequest(
            question="Review my portfolio.",
            portfolio_id=2,
        ),
        snapshot=_snapshot(),
    )
    metrics = response.sections[1].metrics
    assert response.status == "SUCCESS"
    assert (
        metrics[
            "position_exposure_percent"
        ]
        == 50.0
    )
def test_portfolio_analysis_warns_on_high_exposure():
    response = _service().analyze_portfolio(
        data=AIPortfolioAnalysisRequest(
            question="Review my portfolio."
        ),
        snapshot=_snapshot(
            equity=1000,
            available=50,
            position_value=900,
            unrealized_pnl=-30,
        ),
    )
    warning_codes = {
        warning.code
        for warning in response.warnings
    }
    assert (
        "HIGH_PORTFOLIO_EXPOSURE"
        in warning_codes
    )
    assert (
        "LOW_AVAILABLE_BALANCE"
        in warning_codes
    )
    assert (
        "NEGATIVE_UNREALIZED_PNL"
        in warning_codes
    )
def test_portfolio_partial_snapshot_is_partial():
    response = _service().analyze_portfolio(
        data=AIPortfolioAnalysisRequest(
            question="Review my portfolio."
        ),
        snapshot=_snapshot(
            status="PARTIAL"
        ),
    )
    assert response.status == "PARTIAL"
    assert any(
        warning.code
        == "PORTFOLIO_SYNC_PARTIAL"
        for warning in response.warnings
    )
def test_risk_explanation_handles_accepted_trade():
    response = _service().explain_risk(
        AIRiskExplanationRequest(
            question=(
                "Why did this trade pass?"
            ),
            risk_result=(
                _accepted_risk_result()
            ),
        )
    )
    assert response.status == "SUCCESS"
    assert (
        response.sections[0]
        .metrics["accepted"]
        is True
    )
    assert (
        response.metadata
        .confidence_score
        == 1.0
    )
def test_risk_explanation_handles_rejected_trade():
    response = _service().explain_risk(
        AIRiskExplanationRequest(
            question=(
                "Why was this rejected?"
            ),
            risk_result=(
                _rejected_risk_result()
            ),
        )
    )
    warning_codes = {
        warning.code
        for warning in response.warnings
    }
    assert (
        "RISK_CHECK_FAILED"
        in warning_codes
    )
    assert (
        response.sections[0]
        .metrics["accepted"]
        is False
    )
def test_trade_plan_calculates_risk_reward():
    response = _service().build_trade_plan(
        AITradePlanRequest(
            question="Create a BTC plan.",
            symbol="BTCUSDT",
            side="BUY",
            reference_entry_price=100,
            reference_stop_loss_price=95,
            reference_take_profit_price=110,
            maximum_risk_percent=1,
        )
    )
    assert response.status == "SUCCESS"
    assert response.trade_plan is not None
    assert (
        response.trade_plan
        .estimated_risk_reward_ratio
        == 2.0
    )
    assert (
        response.trade_plan
        .execution_enabled
        is False
    )
def test_trade_plan_without_levels_is_partial():
    response = _service().build_trade_plan(
        AITradePlanRequest(
            question="Create a BTC plan.",
            symbol="BTCUSDT",
            side="SELL",
        )
    )
    assert response.status == "PARTIAL"
    assert response.trade_plan is not None
    assert any(
        warning.code
        == "REFERENCE_LEVELS_INCOMPLETE"
        for warning in response.warnings
    )
def test_arbitrage_explanation_reads_profitability():
    response = _service().explain_arbitrage(
        AIArbitrageExplanationRequest(
            question=(
                "Explain this opportunity."
            ),
            opportunity_type=(
                "CROSS_EXCHANGE"
            ),
            opportunity={
                "gross_spread_percent": 2.0,
                "net_profit": 5.0,
                "net_profit_percent": 1.2,
                "estimated_fees": 1.0,
                "estimated_slippage": 0.2,
            },
        )
    )
    assert response.status == "SUCCESS"
    assert (
        response.sections[0]
        .metrics["net_profit_percent"]
        == 1.2
    )
    assert (
        response.metadata
        .execution_enabled
        is False
    )
def test_arbitrage_missing_net_profit_is_partial():
    response = _service().explain_arbitrage(
        AIArbitrageExplanationRequest(
            question=(
                "Explain this opportunity."
            ),
            opportunity_type="TRIANGULAR",
            opportunity={
                "gross_spread_percent": 1.5,
            },
        )
    )
    assert response.status == "PARTIAL"
    assert any(
        warning.code
        == "NET_PROFITABILITY_MISSING"
        for warning in response.warnings
    )
