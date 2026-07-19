from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from app.api.dependencies import get_current_user
from app.api.websocket_dependencies import (
    get_current_websocket_user,
)
from app.exchanges.bybit.market_stream import (
    BybitTickerStreamClient,
)
from app.models.user import User
from app.schemas.market_scanner import (
    MarketCategory,
    MarketScanRequest,
    MarketTickerStreamSubscription,
)
from app.services.market_scanner_service import (
    MarketScannerService,
)
from app.utils.responses import success_response
router = APIRouter(
    prefix="/market-scanner",
    tags=["Market Scanner"],
)
def get_market_scanner_service(
    current_user: User = Depends(
        get_current_user
    ),
) -> MarketScannerService:
    return MarketScannerService()
def get_market_stream_client(
    is_testnet: bool = False,
) -> BybitTickerStreamClient:
    return BybitTickerStreamClient(
        is_testnet=is_testnet
    )
@router.get("/tickers")
async def list_market_tickers(
    category: MarketCategory = "spot",
    is_testnet: bool = False,
    service: MarketScannerService = Depends(
        get_market_scanner_service
    ),
):
    result = await service.get_tickers(
        category=category,
        is_testnet=is_testnet,
    )
    return success_response(
        message=(
            "Market ticker snapshots retrieved "
            "successfully"
        ),
        data=result.model_dump(mode="json"),
    )
@router.post("/scan")
async def scan_market(
    data: MarketScanRequest,
    service: MarketScannerService = Depends(
        get_market_scanner_service
    ),
):
    result = await service.scan(data)
    return success_response(
        message=(
            "Market scan completed successfully"
        ),
        data=result.model_dump(mode="json"),
    )
@router.websocket("/stream")
async def stream_market_tickers(
    websocket: WebSocket,
    symbols: str = Query(
        min_length=1,
    ),
    category: MarketCategory = "spot",
    is_testnet: bool = False,
    max_messages: int | None = Query(
        default=None,
        ge=1,
        le=10000,
    ),
    current_user: User = Depends(
        get_current_websocket_user
    ),
):
    raw_symbols = symbols.split(",")
    try:
        subscription = (
            MarketTickerStreamSubscription(
                category=category,
                is_testnet=is_testnet,
                symbols=raw_symbols,
                max_messages=max_messages,
            )
        )
    except ValueError as exc:
        await websocket.accept()
        await websocket.send_json(
            {
                "success": False,
                "message": (
                    "Invalid market stream "
                    "subscription"
                ),
                "data": None,
                "errors": {
                    "detail": str(exc),
                },
            }
        )
        await websocket.close(code=1008)
        return
    await websocket.accept()
    await websocket.send_json(
        {
            "success": True,
            "message": (
                "Market ticker stream connected"
            ),
            "data": {
                "user_id": current_user.id,
                "exchange": "BYBIT",
                "category": (
                    subscription.category
                ),
                "is_testnet": (
                    subscription.is_testnet
                ),
                "symbols": (
                    subscription.symbols
                ),
                "max_messages": (
                    subscription.max_messages
                ),
            },
            "errors": None,
        }
    )
    client = get_market_stream_client(
        is_testnet=subscription.is_testnet
    )
    try:
        async for event in client.stream_tickers(
            symbols=subscription.symbols,
            category=subscription.category,
            max_messages=(
                subscription.max_messages
            ),
        ):
            await websocket.send_json(
                {
                    "success": True,
                    "message": (
                        "Market ticker update"
                    ),
                    "data": event.model_dump(
                        mode="json"
                    ),
                    "errors": None,
                }
            )
    except WebSocketDisconnect:
        return
    except HTTPException as exc:
        try:
            await websocket.send_json(
                {
                    "success": False,
                    "message": (
                        "Market ticker stream failed"
                    ),
                    "data": None,
                    "errors": {
                        "status_code": (
                            exc.status_code
                        ),
                        "detail": exc.detail,
                    },
                }
            )
            await websocket.close(code=1011)
        except RuntimeError:
            return
    except Exception as exc:
        try:
            await websocket.send_json(
                {
                    "success": False,
                    "message": (
                        "Unexpected market stream "
                        "failure"
                    ),
                    "data": None,
                    "errors": {
                        "detail": str(exc),
                    },
                }
            )
            await websocket.close(code=1011)
        except RuntimeError:
            return
