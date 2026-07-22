import pytest
from pydantic import (
    ValidationError,
)
from app.schemas.strategy_template import (
    StrategyTemplateBotCreateRequest,
    StrategyTemplateCreateRequest,
    StrategyTemplateUpdateRequest,
)
def test_create_normalizes_values():
    data = StrategyTemplateCreateRequest(
        name="  Momentum   Builder  ",
        description="  Reusable setup  ",
        strategy_type="RULE_BASED",
        symbol=" btcusdt ",
    )
    assert data.name == (
        "Momentum Builder"
    )
    assert data.description == (
        "Reusable setup"
    )
    assert data.symbol == "BTCUSDT"
    assert data.visibility == "PRIVATE"
    assert data.paper_trading is True
    assert data.dry_run is True
def test_create_rejects_live_execution():
    with pytest.raises(
        ValidationError,
        match=(
            "paper_trading or dry_run"
        ),
    ):
        StrategyTemplateCreateRequest(
            name="Unsafe Template",
            strategy_type="RULE_BASED",
            symbol="BTCUSDT",
            paper_trading=False,
            dry_run=False,
        )
def test_create_validates_risk_hierarchy():
    with pytest.raises(
        ValidationError,
        match=(
            "risk_per_trade_percent"
        ),
    ):
        StrategyTemplateCreateRequest(
            name="Unsafe Risk",
            strategy_type="RULE_BASED",
            symbol="BTCUSDT",
            risk_per_trade_percent=5,
            max_daily_loss_percent=3,
        )
def test_create_validates_drawdown_hierarchy():
    with pytest.raises(
        ValidationError,
        match=(
            "max_daily_loss_percent"
        ),
    ):
        StrategyTemplateCreateRequest(
            name="Unsafe Drawdown",
            strategy_type="RULE_BASED",
            symbol="BTCUSDT",
            max_daily_loss_percent=12,
            max_drawdown_percent=10,
        )
def test_update_requires_value():
    with pytest.raises(
        ValidationError,
        match="At least one",
    ):
        StrategyTemplateUpdateRequest()
def test_update_rejects_explicit_live_execution():
    with pytest.raises(
        ValidationError,
        match=(
            "paper_trading or dry_run"
        ),
    ):
        StrategyTemplateUpdateRequest(
            paper_trading=False,
            dry_run=False,
        )
def test_unknown_fields_are_rejected():
    with pytest.raises(
        ValidationError,
        match="Extra inputs",
    ):
        StrategyTemplateCreateRequest(
            name="Unknown Field",
            strategy_type="RULE_BASED",
            symbol="BTCUSDT",
            exchange_account_id=1,
        )
def test_bot_create_request_normalizes_values():
    data = (
        StrategyTemplateBotCreateRequest(
            exchange_account_id=5,
            name="  Copied   Momentum Bot ",
            description="  Safe copy  ",
        )
    )
    assert data.exchange_account_id == 5
    assert data.name == (
        "Copied Momentum Bot"
    )
    assert data.description == (
        "Safe copy"
    )
def test_bot_create_request_rejects_unknown_fields():
    with pytest.raises(
        ValidationError,
        match="Extra inputs",
    ):
        StrategyTemplateBotCreateRequest(
            name="Copied Bot",
            source_user_id=9,
        )
