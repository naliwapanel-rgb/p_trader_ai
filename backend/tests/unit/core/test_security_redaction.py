from pydantic import (
    SecretStr,
)
from app.core.security.redaction import (
    REDACTED,
    is_sensitive_key,
    redact_sensitive_data,
    redact_sensitive_text,
    sanitize_query_string,
)
def test_sensitive_key_variants():
    assert is_sensitive_key(
        "api_key"
    )
    assert is_sensitive_key(
        "API-SECRET"
    )
    assert is_sensitive_key(
        "currentPassword"
    )
    assert not is_sensitive_key(
        "symbol"
    )
def test_nested_sensitive_values_are_redacted():
    value = {
        "symbol": "BTCUSDT",
        "credentials": {
            "api_key": "key-value",
            "api_secret": "secret-value",
        },
        "password": "Password123",
    }
    result = redact_sensitive_data(
        value
    )
    assert result["symbol"] == (
        "BTCUSDT"
    )
    assert (
        result["credentials"]["api_key"]
        == REDACTED
    )
    assert (
        result["credentials"]["api_secret"]
        == REDACTED
    )
    assert result["password"] == (
        REDACTED
    )
def test_secret_objects_and_exceptions_are_safe():
    value = [
        SecretStr("hidden-value"),
        RuntimeError(
            "password=hidden-password"
        ),
    ]
    result = redact_sensitive_data(
        value
    )
    assert result[0] == REDACTED
    assert "hidden-password" not in (
        result[1]
    )
    assert REDACTED in result[1]
def test_bearer_token_is_redacted():
    value = (
        "Authorization: "
        "Bearer abc.def.secret"
    )
    result = redact_sensitive_text(
        value
    )
    assert "abc.def.secret" not in (
        result
    )
    assert (
        f"Bearer {REDACTED}"
        in result
    )
def test_non_bearer_authorization_is_redacted():
    value = (
        "Authorization: "
        "Basic encoded-credential"
    )
    result = redact_sensitive_text(
        value
    )
    assert (
        "encoded-credential"
        not in result
    )
    assert result == (
        "Authorization: REDACTED"
    )
def test_assignment_values_are_redacted():
    value = (
        'api_key="top-secret", '
        "password=Password123"
    )
    result = redact_sensitive_text(
        value
    )
    assert "top-secret" not in result
    assert "Password123" not in result
    assert result.count(
        REDACTED
    ) == 2
def test_query_string_redacts_only_secrets():
    result = sanitize_query_string(
        (
            "symbol=BTCUSDT"
            "&api_key=top-secret"
            "&token=abc123"
        )
    )
    assert "BTCUSDT" in result
    assert "top-secret" not in result
    assert "abc123" not in result
    assert (
        "api_key=REDACTED"
        in result
    )
