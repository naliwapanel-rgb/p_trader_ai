from app.core.security.encryption import decrypt_value
from app.exchanges.base import BaseExchangeClient
from app.exchanges.binance.client import BinanceClient
from app.exchanges.bybit.client import BybitClient
from app.exchanges.gateio.client import GateIOClient
from app.exchanges.mexc.client import MEXCClient
from app.models.exchange_account import ExchangeAccount


class ExchangeFactory:
    @staticmethod
    def create_client(account: ExchangeAccount) -> BaseExchangeClient:
        api_key = decrypt_value(account.encrypted_api_key)
        api_secret = decrypt_value(account.encrypted_api_secret)

        exchange_name = account.exchange_name.upper()

        if exchange_name == "BYBIT":
            return BybitClient(api_key, api_secret, account.is_testnet)

        if exchange_name == "BINANCE":
            return BinanceClient(api_key, api_secret, account.is_testnet)

        if exchange_name == "MEXC":
            return MEXCClient(api_key, api_secret, account.is_testnet)

        if exchange_name == "GATEIO":
            return GateIOClient(api_key, api_secret, account.is_testnet)

        raise ValueError(f"Unsupported exchange: {account.exchange_name}")