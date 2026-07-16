import pytest

from app.exchanges.bybit.client import BybitClient
from app.exchanges.bybit.errors import get_bybit_error
from app.exchanges.exceptions import ExchangeAPIException


def test_maps_known_bybit_error():
    error = get_bybit_error(
        code=10006,
        exchange_message="Too many visits!",
    )

    assert error.error_type == "RATE_LIMITED"
    assert error.http_status == 429
    assert "rate limit" in error.message.lower()


def test_maps_insufficient_margin():
    error = get_bybit_error(
        code=110006,
        exchange_message="The assets are estimated to be unable",
    )

    assert error.error_type == "INSUFFICIENT_MARGIN"
    assert error.http_status == 400


def test_unknown_error_preserves_safe_exchange_message():
    error = get_bybit_error(
        code=999999,
        exchange_message="Unknown test error",
    )

    assert error.error_type == "BYBIT_API_ERROR"
    assert error.message == "Unknown test error"


def test_validate_bybit_payload_accepts_success():
    BybitClient._validate_bybit_payload(
        {
            "retCode": 0,
            "retMsg": "OK",
        }
    )


def test_validate_bybit_payload_raises_structured_exception():
    with pytest.raises(ExchangeAPIException) as exc_info:
        BybitClient._validate_bybit_payload(
            {
                "retCode": 170141,
                "retMsg": "Duplicate clientOrderId",
            }
        )

    error = exc_info.value

    assert error.status_code == 409
    assert error.error_code == 170141
    assert error.error_type == "DUPLICATE_CLIENT_ORDER_ID"

    assert error.detail == {
        "exchange": "BYBIT",
        "error_code": 170141,
        "error_type": "DUPLICATE_CLIENT_ORDER_ID",
        "message": "The client order ID has already been used.",
    }