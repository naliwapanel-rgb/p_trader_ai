import json
import logging
from datetime import (
    datetime,
    timezone,
)
from logging.config import (
    dictConfig,
)

from app.core.config import (
    Settings,
)


class JsonLogFormatter(
    logging.Formatter
):
    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        timestamp = (
            datetime.now(
                timezone.utc
            )
            .isoformat(
                timespec="milliseconds"
            )
            .replace(
                "+00:00",
                "Z",
            )
        )

        payload = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if (
            record.exc_info
            and record.exc_info[0]
            is not None
        ):
            payload[
                "exception_type"
            ] = (
                record.exc_info[0]
                .__name__
            )

        return json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def configure_logging(
    settings: Settings,
) -> None:
    formatter_name = (
        "json"
        if settings.log_json_enabled
        else "standard"
    )

    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": (
                    "%(asctime)s "
                    "%(levelname)s "
                    "%(name)s "
                    "%(message)s"
                ),
            },
            "json": {
                "()": JsonLogFormatter,
            },
        },
        "handlers": {
            "console": {
                "class": (
                    "logging.StreamHandler"
                ),
                "formatter": (
                    formatter_name
                ),
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": settings.log_level,
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["console"],
                "level": settings.log_level,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console"],
                "level": settings.log_level,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": settings.log_level,
                "propagate": False,
            },
        },
    })
