import pytest
from pydantic import (
    ValidationError,
)
from app.schemas.copy_trading_subscription import (
    CopyTradingSubscriptionCreateRequest,
)
def test_create_request_accepts_identifiers():
    data = (
        CopyTradingSubscriptionCreateRequest(
            source_template_id=5,
            follower_bot_id=8,
        )
    )
    assert data.source_template_id == 5
    assert data.follower_bot_id == 8
def test_create_request_rejects_invalid_ids():
    with pytest.raises(
        ValidationError,
    ):
        CopyTradingSubscriptionCreateRequest(
            source_template_id=0,
            follower_bot_id=-1,
        )
def test_create_request_rejects_unknown_fields():
    with pytest.raises(
        ValidationError,
        match="Extra inputs",
    ):
        CopyTradingSubscriptionCreateRequest(
            source_template_id=5,
            follower_bot_id=8,
            leader_api_key="secret",
        )
