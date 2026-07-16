from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.exchanges.bybit.client import BybitClient


def valid_linear_rules() -> dict:
    return {
        "exchange": "BYBIT",
        "category": "linear",
        "symbol": "BTCUSDT",
        "status": "Trading",
        "base_coin": "BTC",
        "quote_coin": "USDT",
        "settle_coin": "USDT",
        "min_price": "0.1",
        "max_price": "1000000",
        "tick_size": "0.1",
        "min_order_quantity": "0.001",
        "max_limit_order_quantity": "100",
        "max_market_order_quantity": "50",
        "quantity_step": "0.001",
        "min_notional_value": "5",
    }


@pytest.mark.asyncio
async def test_market_order_attaches_full_tpsl():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client.get_instrument_rules = AsyncMock(
        return_value=valid_linear_rules()
    )

    client._private_post = AsyncMock(
        return_value={
            "retCode": 0,
            "result": {
                "orderId": "market-tpsl-123",
                "orderLinkId": "ptrader-market-tpsl",
            },
        }
    )

    client.get_order_by_id = AsyncMock(
        return_value=None
    )

    result = await client.place_market_order(
        symbol="BTCUSDT",
        side="BUY",
        quantity=0.001,
        category="linear",
        time_in_force="IOC",
        take_profit=60000,
        stop_loss=45000,
        tp_trigger_by="MarkPrice",
        sl_trigger_by="MarkPrice",
        tpsl_mode="Full",
        client_order_id="ptrader-market-tpsl",
        dry_run=False,
    )

    client._private_post.assert_awaited_once_with(
        endpoint="/v5/order/create",
        body={
            "category": "linear",
            "symbol": "BTCUSDT",
            "side": "Buy",
            "orderType": "Market",
            "qty": "0.001",
            "timeInForce": "IOC",
            "reduceOnly": False,
            "closeOnTrigger": False,
            "orderLinkId": "ptrader-market-tpsl",
            "takeProfit": "60000",
            "tpTriggerBy": "MarkPrice",
            "stopLoss": "45000",
            "slTriggerBy": "MarkPrice",
            "tpslMode": "Full",
            "tpOrderType": "Market",
            "slOrderType": "Market",
        },
    )

    assert result["order_id"] == "market-tpsl-123"
    assert result["accepted"] is True


@pytest.mark.asyncio
async def test_limit_order_attaches_full_tpsl():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client.get_instrument_rules = AsyncMock(
        return_value=valid_linear_rules()
    )

    client._private_post = AsyncMock(
        return_value={
            "retCode": 0,
            "result": {
                "orderId": "limit-tpsl-456",
                "orderLinkId": "ptrader-limit-tpsl",
            },
        }
    )

    client.get_order_by_id = AsyncMock(
        return_value=None
    )

    result = await client.place_limit_order(
        symbol="BTCUSDT",
        side="BUY",
        quantity=0.001,
        price=50000,
        category="linear",
        time_in_force="GTC",
        take_profit=60000,
        stop_loss=45000,
        tp_trigger_by="LastPrice",
        sl_trigger_by="MarkPrice",
        tpsl_mode="Full",
        client_order_id="ptrader-limit-tpsl",
        dry_run=False,
    )

    call_body = client._private_post.await_args.kwargs[
        "body"
    ]

    assert call_body["takeProfit"] == "60000"
    assert call_body["stopLoss"] == "45000"
    assert call_body["tpslMode"] == "Full"
    assert call_body["tpOrderType"] == "Market"
    assert call_body["slOrderType"] == "Market"

    assert result["order_id"] == "limit-tpsl-456"
    assert result["accepted"] is True


@pytest.mark.asyncio
async def test_market_order_attaches_partial_limit_tpsl():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    client.get_instrument_rules = AsyncMock(
        return_value=valid_linear_rules()
    )

    client._private_post = AsyncMock(
        return_value={
            "retCode": 0,
            "result": {
                "orderId": "partial-tpsl-123",
                "orderLinkId": "ptrader-partial-tpsl",
            },
        }
    )

    client.get_order_by_id = AsyncMock(
        return_value=None
    )

    result = await client.place_market_order(
        symbol="BTCUSDT",
        side="BUY",
        quantity=0.001,
        category="linear",
        take_profit=60000,
        stop_loss=45000,
        tp_trigger_by="MarkPrice",
        sl_trigger_by="MarkPrice",
        tpsl_mode="Partial",
        tp_order_type="Limit",
        sl_order_type="Limit",
        tp_limit_price=59900,
        sl_limit_price=44900,
        client_order_id="ptrader-partial-tpsl",
        dry_run=False,
    )

    call_body = client._private_post.await_args.kwargs[
        "body"
    ]

    assert call_body["tpslMode"] == "Partial"
    assert call_body["tpOrderType"] == "Limit"
    assert call_body["slOrderType"] == "Limit"
    assert call_body["tpLimitPrice"] == "59900"
    assert call_body["slLimitPrice"] == "44900"

    assert result["order_id"] == "partial-tpsl-123"
    assert result["accepted"] is True


def test_full_mode_rejects_limit_tpsl():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    with pytest.raises(HTTPException) as exc_info:
        client._validate_attached_tpsl(
            take_profit=60000,
            stop_loss=45000,
            tp_trigger_by="LastPrice",
            sl_trigger_by="LastPrice",
            tpsl_mode="Full",
            tp_order_type="Limit",
            sl_order_type="Market",
            tp_limit_price=59900,
            sl_limit_price=None,
        )

    assert "Full TP/SL mode" in exc_info.value.detail


def test_limit_tp_requires_limit_price():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    with pytest.raises(HTTPException) as exc_info:
        client._validate_attached_tpsl(
            take_profit=60000,
            stop_loss=None,
            tp_trigger_by="LastPrice",
            sl_trigger_by="LastPrice",
            tpsl_mode="Partial",
            tp_order_type="Limit",
            sl_order_type="Market",
            tp_limit_price=None,
            sl_limit_price=None,
        )

    assert "tp_limit_price is required" in exc_info.value.detail


def test_market_tp_rejects_limit_price():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    with pytest.raises(HTTPException) as exc_info:
        client._validate_attached_tpsl(
            take_profit=60000,
            stop_loss=None,
            tp_trigger_by="LastPrice",
            sl_trigger_by="LastPrice",
            tpsl_mode="Partial",
            tp_order_type="Market",
            sl_order_type="Market",
            tp_limit_price=59900,
            sl_limit_price=None,
        )

    assert "tp_order_type=Limit" in exc_info.value.detail


def test_rejects_invalid_tp_trigger_type():
    client = BybitClient(
        api_key="test_key",
        api_secret="test_secret",
        is_testnet=False,
    )

    with pytest.raises(HTTPException) as exc_info:
        client._validate_attached_tpsl(
            take_profit=60000,
            stop_loss=None,
            tp_trigger_by="InvalidPrice",
            sl_trigger_by="LastPrice",
            tpsl_mode="Full",
        )

    assert "take-profit trigger type" in exc_info.value.detail