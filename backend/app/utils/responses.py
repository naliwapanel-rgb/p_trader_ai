from typing import Any


def success_response(
    message: str,
    data: Any | None = None,
) -> dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": data,
        "errors": None,
    }


def error_response(
    message: str,
    errors: Any | None = None,
) -> dict[str, Any]:
    return {
        "success": False,
        "message": message,
        "data": None,
        "errors": errors,
    }