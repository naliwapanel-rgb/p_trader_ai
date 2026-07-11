import hashlib
import hmac
import time


class BybitAuth:
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        recv_window: int = 5000,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.recv_window = recv_window

    def timestamp(self) -> str:
        return str(int(time.time() * 1000))

    def sign(
        self,
        timestamp: str,
        query: str = "",
    ) -> str:
        payload = timestamp + self.api_key + str(self.recv_window) + query

        return hmac.new(
            self.api_secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

    def headers(
        self,
        query: str = "",
    ) -> dict[str, str]:
        ts = self.timestamp()

        return {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-TIMESTAMP": ts,
            "X-BAPI-RECV-WINDOW": str(self.recv_window),
            "X-BAPI-SIGN": self.sign(ts, query),
        }