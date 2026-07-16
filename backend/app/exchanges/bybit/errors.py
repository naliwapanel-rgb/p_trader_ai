from dataclasses import dataclass

from fastapi import status


@dataclass(frozen=True)
class BybitErrorInfo:
    code: int
    error_type: str
    message: str
    http_status: int


BYBIT_ERROR_MAP: dict[int, BybitErrorInfo] = {
    10001: BybitErrorInfo(
        code=10001,
        error_type="INVALID_REQUEST",
        message="Invalid Bybit request parameters.",
        http_status=status.HTTP_400_BAD_REQUEST,
    ),
    10002: BybitErrorInfo(
        code=10002,
        error_type="REQUEST_EXPIRED",
        message="The Bybit request timestamp is outside the allowed window.",
        http_status=status.HTTP_400_BAD_REQUEST,
    ),
    10003: BybitErrorInfo(
        code=10003,
        error_type="INVALID_API_KEY",
        message="The Bybit API key is invalid for this environment.",
        http_status=status.HTTP_401_UNAUTHORIZED,
    ),
    10004: BybitErrorInfo(
        code=10004,
        error_type="INVALID_SIGNATURE",
        message="Bybit rejected the request signature.",
        http_status=status.HTTP_401_UNAUTHORIZED,
    ),
    10005: BybitErrorInfo(
        code=10005,
        error_type="PERMISSION_DENIED",
        message="The Bybit API key lacks the required permission.",
        http_status=status.HTTP_403_FORBIDDEN,
    ),
    10006: BybitErrorInfo(
        code=10006,
        error_type="RATE_LIMITED",
        message="The Bybit API rate limit was exceeded.",
        http_status=status.HTTP_429_TOO_MANY_REQUESTS,
    ),
    110001: BybitErrorInfo(
        code=110001,
        error_type="ORDER_NOT_FOUND",
        message="The requested Bybit order does not exist.",
        http_status=status.HTTP_404_NOT_FOUND,
    ),
    110004: BybitErrorInfo(
        code=110004,
        error_type="INSUFFICIENT_BALANCE",
        message="The Bybit wallet balance is insufficient.",
        http_status=status.HTTP_400_BAD_REQUEST,
    ),
    110006: BybitErrorInfo(
        code=110006,
        error_type="INSUFFICIENT_MARGIN",
        message="The available margin is insufficient for this order.",
        http_status=status.HTTP_400_BAD_REQUEST,
    ),
    110007: BybitErrorInfo(
        code=110007,
        error_type="INSUFFICIENT_MARGIN",
        message="The available balance is insufficient for this order.",
        http_status=status.HTTP_400_BAD_REQUEST,
    ),
    110012: BybitErrorInfo(
        code=110012,
        error_type="INSUFFICIENT_MARGIN",
        message="The available balance cannot cover the required margin.",
        http_status=status.HTTP_400_BAD_REQUEST,
    ),
    110017: BybitErrorInfo(
        code=110017,
        error_type="REDUCE_ONLY_VIOLATION",
        message="The order violates Bybit reduce-only rules.",
        http_status=status.HTTP_400_BAD_REQUEST,
    ),
    110020: BybitErrorInfo(
        code=110020,
        error_type="ACTIVE_ORDER_LIMIT",
        message="The maximum number of active orders has been reached.",
        http_status=status.HTTP_400_BAD_REQUEST,
    ),
    110043: BybitErrorInfo(
        code=110043,
        error_type="LEVERAGE_UNCHANGED",
        message="The requested leverage is already configured.",
        http_status=status.HTTP_400_BAD_REQUEST,
    ),
    170136: BybitErrorInfo(
        code=170136,
        error_type="QUANTITY_TOO_LOW",
        message="The order quantity is below the Bybit minimum.",
        http_status=status.HTTP_400_BAD_REQUEST,
    ),
    170140: BybitErrorInfo(
        code=170140,
        error_type="NOTIONAL_TOO_LOW",
        message="The order value is below the Bybit minimum.",
        http_status=status.HTTP_400_BAD_REQUEST,
    ),
    170141: BybitErrorInfo(
        code=170141,
        error_type="DUPLICATE_CLIENT_ORDER_ID",
        message="The client order ID has already been used.",
        http_status=status.HTTP_409_CONFLICT,
    ),
    170142: BybitErrorInfo(
        code=170142,
        error_type="ORDER_ALREADY_CANCELLED",
        message="The order has already been cancelled.",
        http_status=status.HTTP_409_CONFLICT,
    ),
    170146: BybitErrorInfo(
        code=170146,
        error_type="ORDER_TIMEOUT",
        message="Bybit timed out while creating the order.",
        http_status=status.HTTP_504_GATEWAY_TIMEOUT,
    ),
    170149: BybitErrorInfo(
        code=170149,
        error_type="ORDER_CREATION_FAILED",
        message="Bybit could not create the order.",
        http_status=status.HTTP_400_BAD_REQUEST,
    ),
}


def get_bybit_error(
    code: int,
    exchange_message: str = "",
) -> BybitErrorInfo:
    known_error = BYBIT_ERROR_MAP.get(code)

    if known_error is not None:
        return known_error

    safe_message = (
        exchange_message.strip()
        if exchange_message.strip()
        else "Bybit rejected the request."
    )

    return BybitErrorInfo(
        code=code,
        error_type="BYBIT_API_ERROR",
        message=safe_message,
        http_status=status.HTTP_400_BAD_REQUEST,
    )