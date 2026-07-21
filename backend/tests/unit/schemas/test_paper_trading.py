import pytest
from pydantic import (
    ValidationError,
)
from app.schemas.paper_trading import (
    PaperTradingEngineSettings,
)
def test_paper_engine_settings_defaults():
    settings = (
        PaperTradingEngineSettings()
    )
    assert (
        settings.initial_balance_usd
        == 10000
    )
    assert settings.currency == "USDT"
    assert settings.fee_rate == 0.0006
    assert settings.slippage_rate == 0.0001
def test_paper_engine_settings_normalize_currency():
    settings = (
        PaperTradingEngineSettings(
            currency=" usdt "
        )
    )
    assert settings.currency == "USDT"
def test_paper_engine_settings_reject_unknown_fields():
    with pytest.raises(
        ValidationError,
    ):
        PaperTradingEngineSettings(
            unsupported_setting=True
        )
