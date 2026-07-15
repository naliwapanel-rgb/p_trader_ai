import hashlib
import hmac

from app.exchanges.bybit.auth import BybitAuth


def test_bybit_auth_signs_get_query_string():
    auth = BybitAuth(
        api_key="test_key",
        api_secret="test_secret",
        recv_window=5000,
    )

    timestamp = "1710000000000"
    query_string = "category=linear&symbol=BTCUSDT"

    expected_payload = (
        timestamp
        + "test_key"
        + "5000"
        + query_string
    )

    expected_signature = hmac.new(
        b"test_secret",
        expected_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    assert auth.sign(timestamp, query_string) == expected_signature


def test_bybit_auth_signs_exact_post_json_body():
    auth = BybitAuth(
        api_key="test_key",
        api_secret="test_secret",
        recv_window=5000,
    )

    timestamp = "1710000000000"
    body_string = (
        '{"category":"linear","symbol":"BTCUSDT",'
        '"side":"Buy","orderType":"Market","qty":"0.001"}'
    )

    expected_payload = (
        timestamp
        + "test_key"
        + "5000"
        + body_string
    )

    expected_signature = hmac.new(
        b"test_secret",
        expected_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    assert auth.sign(timestamp, body_string) == expected_signature
    assert len(expected_signature) == 64