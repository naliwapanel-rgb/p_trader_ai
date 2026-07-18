from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import HTTPException
from app.api.v1.endpoints.exchange_connections import (
    get_exchange_position_leverage,
)
@pytest.fixture
def current_user():
    user = MagicMock()
    user.id = 1
    return user
@pytest.fixture
def db():
    return MagicMock()
@pytest.mark.asyncio
async def test_get_exchange_position_leverage_success(
    current_user,
    db,
):
    account = MagicMock()
    leverage_result = {
        "exchange": "BYBIT",
        "symbol": "BTCUSDT",
        "category": "linear",
        "positions": [
            {
                "position_side": "LONG",
                "leverage": 10.0,
            }
        ],
    }
    client = MagicMock()
    client.get_position_leverage = AsyncMock(
        return_value=leverage_result
    )
    with patch(
        "app.api.v1.endpoints.exchange_connections."
        "ExchangeAccountService"
    ) as service_class, patch(
        "app.api.v1.endpoints.exchange_connections."
        "ExchangeFactory.create_client",
        return_value=client,
    ):
        service_class.return_value.get_account.return_value = account
        result = await get_exchange_position_leverage(
            account_id=1,
            symbol="BTCUSDT",
            category="linear",
            current_user=current_user,
            db=db,
        )
    service_class.assert_called_once_with(db)
    service_class.return_value.get_account.assert_called_once_with(
        current_user=current_user,
        account_id=1,
    )
    client.get_position_leverage.assert_awaited_once_with(
        symbol="BTCUSDT",
        category="linear",
    )
    assert result["success"] is True
    assert result["message"] == (
        "Position leverage retrieved successfully"
    )
    assert result["data"] == leverage_result
@pytest.mark.asyncio
async def test_get_exchange_position_leverage_unsupported_exchange(
    current_user,
    db,
):
    account = MagicMock()
    client = MagicMock(spec=[])
    with patch(
        "app.api.v1.endpoints.exchange_connections."
        "ExchangeAccountService"
    ) as service_class, patch(
        "app.api.v1.endpoints.exchange_connections."
        "ExchangeFactory.create_client",
        return_value=client,
    ):
        service_class.return_value.get_account.return_value = account
        with pytest.raises(HTTPException) as exc_info:
            await get_exchange_position_leverage(
                account_id=1,
                symbol="BTCUSDT",
                category="linear",
                current_user=current_user,
                db=db,
            )
    assert exc_info.value.status_code == 501
    assert exc_info.value.detail == (
        "Position leverage retrieval is not "
        "supported for this exchange"
    )
@pytest.mark.asyncio
async def test_get_exchange_position_leverage_preserves_account_error(
    current_user,
    db,
):
    account_error = HTTPException(
        status_code=404,
        detail="Exchange account not found",
    )
    with patch(
        "app.api.v1.endpoints.exchange_connections."
        "ExchangeAccountService"
    ) as service_class:
        service_class.return_value.get_account.side_effect = (
            account_error
        )
        with pytest.raises(HTTPException) as exc_info:
            await get_exchange_position_leverage(
                account_id=999,
                symbol="BTCUSDT",
                category="linear",
                current_user=current_user,
                db=db,
            )
    assert exc_info.value is account_error
@pytest.mark.asyncio
async def test_get_exchange_position_leverage_forwards_parameters(
    current_user,
    db,
):
    account = MagicMock()
    client = MagicMock()
    client.get_position_leverage = AsyncMock(
        return_value={
            "exchange": "BYBIT",
            "symbol": "ETHUSD",
            "category": "inverse",
            "positions": [],
        }
    )
    with patch(
        "app.api.v1.endpoints.exchange_connections."
        "ExchangeAccountService"
    ) as service_class, patch(
        "app.api.v1.endpoints.exchange_connections."
        "ExchangeFactory.create_client",
        return_value=client,
    ):
        service_class.return_value.get_account.return_value = account
        await get_exchange_position_leverage(
            account_id=7,
            symbol="ETHUSD",
            category="inverse",
            current_user=current_user,
            db=db,
        )
    client.get_position_leverage.assert_awaited_once_with(
        symbol="ETHUSD",
        category="inverse",
    )
