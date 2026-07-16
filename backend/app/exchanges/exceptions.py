from fastapi import HTTPException


class ExchangeAPIException(HTTPException):
    def __init__(
        self,
        *,
        status_code: int,
        exchange: str,
        error_code: int | str,
        error_type: str,
        message: str,
        exchange_message: str = "",
    ):
        self.exchange = exchange
        self.error_code = error_code
        self.error_type = error_type
        self.exchange_message = exchange_message

        super().__init__(
            status_code=status_code,
            detail={
                "exchange": exchange,
                "error_code": error_code,
                "error_type": error_type,
                "message": message,
            },
        )