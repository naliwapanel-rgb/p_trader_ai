from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.market_scanner import (
    MarketCategory,
    MarketScanRequest,
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
