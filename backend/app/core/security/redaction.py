import re
from collections.abc import (
    Mapping,
    Sequence,
)
from typing import (
    Any,
)
from urllib.parse import (
    parse_qsl,
    quote_plus,
)
from pydantic import (
    SecretStr,
)
REDACTED = "REDACTED"
_SENSITIVE_KEYS = frozenset({
    "authorization",
    "proxyauthorization",
    "apikey",
    "apisecret",
    "secret",
    "clientsecret",
    "privatekey",
    "password",
    "currentpassword",
    "newpassword",
    "hashedpassword",
    "token",
    "accesstoken",
    "refreshtoken",
    "cookie",
    "setcookie",
    "encryptedapikey",
    "encryptedapisecret",
})
_BEARER_PATTERN = re.compile(
    (
        r"\bBearer\s+"
        r"[A-Za-z0-9._~+/=-]+"
    ),
    re.IGNORECASE,
)
_AUTHORIZATION_PATTERN = re.compile(
    (
        r"\b("
        r"authorization|"
        r"proxy[_-]?authorization"
        r")\b"
        r"(\s*[:=]\s*)"
        r"(?:"
        r"([\"'])(.*?)\3"
        r"|"
        r"([^\r\n,;&]+)"
        r")"
    ),
    re.IGNORECASE,
)
_ASSIGNMENT_PATTERN = re.compile(
    (
        r"\b("
        r"api[_-]?key|"
        r"api[_-]?secret|"
        r"client[_-]?secret|"
        r"private[_-]?key|"
        r"password|"
        r"current[_-]?password|"
        r"new[_-]?password|"
        r"access[_-]?token|"
        r"refresh[_-]?token|"
        r"token|"
        r"secret"
        r")\b"
        r"(\s*[:=]\s*)"
        r"(?:"
        r"([\"'])(.*?)\3"
        r"|"
        r"([^\s,;&]+)"
        r")"
    ),
    re.IGNORECASE,
)
def normalize_sensitive_key(
    key: object,
) -> str:
    return re.sub(
        r"[^a-z0-9]",
        "",
        str(key).strip().lower(),
    )
def is_sensitive_key(
    key: object,
) -> bool:
    return (
        normalize_sensitive_key(key)
        in _SENSITIVE_KEYS
    )
def redact_sensitive_text(
    value: str,
) -> str:
    def replace_authorization(
        match: re.Match,
    ) -> str:
        key = match.group(1)
        separator = match.group(2)
        quoted_value = match.group(4)
        unquoted_value = match.group(5)
        raw_value = (
            quoted_value
            if quoted_value is not None
            else unquoted_value
        )
        normalized_value = (
            raw_value or ""
        ).strip()
        if normalized_value.lower().startswith(
            "bearer "
        ):
            return (
                f"{key}{separator}"
                f"Bearer {REDACTED}"
            )
        return (
            f"{key}{separator}"
            f"{REDACTED}"
        )
    redacted = (
        _AUTHORIZATION_PATTERN.sub(
            replace_authorization,
            value,
        )
    )
    redacted = _BEARER_PATTERN.sub(
        f"Bearer {REDACTED}",
        redacted,
    )
    def replace_assignment(
        match: re.Match,
    ) -> str:
        key = match.group(1)
        separator = match.group(2)
        quote = match.group(3)
        if quote:
            return (
                f"{key}{separator}"
                f"{quote}{REDACTED}{quote}"
            )
        return (
            f"{key}{separator}"
            f"{REDACTED}"
        )
    return _ASSIGNMENT_PATTERN.sub(
        replace_assignment,
        redacted,
    )
def redact_sensitive_data(
    value: Any,
    *,
    field_name: object | None = None,
) -> Any:
    if (
        field_name is not None
        and is_sensitive_key(field_name)
    ):
        return REDACTED
    if isinstance(
        value,
        SecretStr,
    ):
        return REDACTED
    if isinstance(
        value,
        BaseException,
    ):
        return redact_sensitive_text(
            str(value)
        )
    if isinstance(
        value,
        Mapping,
    ):
        return {
            str(key): redact_sensitive_data(
                item,
                field_name=key,
            )
            for key, item in value.items()
        }
    if isinstance(
        value,
        Sequence,
    ) and not isinstance(
        value,
        (
            str,
            bytes,
            bytearray,
        ),
    ):
        return [
            redact_sensitive_data(item)
            for item in value
        ]
    if isinstance(
        value,
        str,
    ):
        return redact_sensitive_text(
            value
        )
    return value
def sanitize_query_string(
    query_string: str,
) -> str:
    if not query_string:
        return ""
    sanitized_pairs = []
    for key, value in parse_qsl(
        query_string,
        keep_blank_values=True,
    ):
        if is_sensitive_key(key):
            safe_value = REDACTED
        else:
            safe_value = (
                redact_sensitive_text(
                    value
                )
            )
        sanitized_pairs.append(
            (
                key,
                safe_value,
            )
        )
    return "&".join(
        (
            f"{quote_plus(key)}="
            f"{quote_plus(value)}"
        )
        for key, value
        in sanitized_pairs
    )
def sanitize_request_target(
    path: str,
    query_string: str,
) -> str:
    safe_path = redact_sensitive_text(
        path
    )
    safe_query = sanitize_query_string(
        query_string
    )
    if not safe_query:
        return safe_path
    return (
        f"{safe_path}?{safe_query}"
    )
