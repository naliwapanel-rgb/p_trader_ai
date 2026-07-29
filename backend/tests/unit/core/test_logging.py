import json
import logging
import sys

from app.core.logging import (
    JsonLogFormatter,
)


def test_json_formatter_returns_structured_log():
    record = logging.LogRecord(
        name="app.request",
        level=logging.INFO,
        pathname=__file__,
        lineno=20,
        msg=(
            "request_completed "
            "status=%s"
        ),
        args=(200,),
        exc_info=None,
    )

    payload = json.loads(
        JsonLogFormatter().format(
            record
        )
    )

    assert payload["level"] == "INFO"
    assert payload[
        "logger"
    ] == "app.request"
    assert payload[
        "message"
    ] == (
        "request_completed "
        "status=200"
    )
    assert payload[
        "timestamp"
    ].endswith("Z")


def test_json_formatter_reports_exception_type_only():
    try:
        raise ValueError(
            "sensitive internal detail"
        )
    except ValueError:
        exception_info = sys.exc_info()

    record = logging.LogRecord(
        name="app.exceptions",
        level=logging.ERROR,
        pathname=__file__,
        lineno=55,
        msg="unhandled_exception",
        args=(),
        exc_info=exception_info,
    )

    payload = json.loads(
        JsonLogFormatter().format(
            record
        )
    )

    assert payload[
        "exception_type"
    ] == "ValueError"
    assert (
        "sensitive internal detail"
        not in json.dumps(payload)
    )
