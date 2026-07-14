from unittest.mock import AsyncMock

import pytest

from app.exchanges.bybit.client import BybitClient


@pytest.mark.asyncio
async def test_get_account_balance_normalizes_bybit_response():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client._private_get = AsyncMock(
        return_value={
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "list": [
                    {
                        "accountType": "UNIFIED",
                        "totalEquity": "1250.50",
                        "totalWalletBalance": "1200.25",
                        "totalAvailableBalance": "950.00",
                        "totalPerpUPL": "50.25",
                        "coin": [
                            {
                                "coin": "USDT",
                                "equity": "1000.00",
                                "walletBalance": "950.00",
                                "availableToWithdraw": "900.00",
                                "locked": "50.00",
                                "usdValue": "1000.00",
                                "unrealisedPnl": "50.00",
                            },
                            {
                                "coin": "BTC",
                                "equity": "0.0025",
                                "walletBalance": "0.0025",
                                "availableToWithdraw": "0.0020",
                                "locked": "0.0005",
                                "usdValue": "250.50",
                                "unrealisedPnl": "0.25",
                            },
                        ],
                    }
                ]
            },
        }
    )

    result = await client.get_account_balance()

    assert result["exchange"] == "BYBIT"
    assert result["account_type"] == "UNIFIED"

    assert result["total_equity_usd"] == 1250.50
    assert result["total_wallet_balance_usd"] == 1200.25
    assert result["total_available_balance_usd"] == 950.00
    assert result["total_unrealized_pnl_usd"] == 50.25

    assert len(result["coins"]) == 2

    usdt = result["coins"][0]

    assert usdt["coin"] == "USDT"
    assert usdt["wallet_balance"] == 950.00
    assert usdt["available_balance"] == 900.00
    assert usdt["locked_balance"] == 50.00


@pytest.mark.asyncio
async def test_get_account_balance_handles_empty_account_list():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client._private_get = AsyncMock(
        return_value={
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "list": [],
            },
        }
    )

    result = await client.get_account_balance()

    assert result["exchange"] == "BYBIT"
    assert result["account_type"] == "UNIFIED"
    assert result["total_equity_usd"] == 0.0
    assert result["coins"] == []