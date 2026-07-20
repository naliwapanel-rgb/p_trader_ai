from fastapi import APIRouter, Depends
from app.api.dependencies import (
    get_current_user,
)
from app.models.user import User
from app.schemas.arbitrage import (
    ArbitrageEvaluationRequest,
    CrossExchangeScanRequest,
    TriangularScanRequest,
)
from app.services.arbitrage_profit_service import (
    ArbitrageProfitService,
)
from app.services.cross_exchange_arbitrage_service import (
    CrossExchangeArbitrageService,
)
from app.services.triangular_arbitrage_service import (
    TriangularArbitrageService,
)
from app.utils.responses import success_response
router = APIRouter(
    prefix="/arbitrage",
    tags=["Arbitrage"],
)
def get_arbitrage_profit_service(
    current_user: User = Depends(
        get_current_user
    ),
) -> ArbitrageProfitService:
    return ArbitrageProfitService()
def get_cross_exchange_arbitrage_service(
    current_user: User = Depends(
        get_current_user
    ),
) -> CrossExchangeArbitrageService:
    return CrossExchangeArbitrageService()
def get_triangular_arbitrage_service(
    current_user: User = Depends(
        get_current_user
    ),
) -> TriangularArbitrageService:
    return TriangularArbitrageService()
@router.post("/evaluate")
async def evaluate_arbitrage_opportunity(
    data: ArbitrageEvaluationRequest,
    service: ArbitrageProfitService = Depends(
        get_arbitrage_profit_service
    ),
):
    result = service.evaluate(data)
    return success_response(
        message=(
            "Arbitrage opportunity evaluated "
            "successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
@router.post("/cross-exchange/scan")
async def scan_cross_exchange_opportunities(
    data: CrossExchangeScanRequest,
    service: CrossExchangeArbitrageService = (
        Depends(
            get_cross_exchange_arbitrage_service
        )
    ),
):
    result = service.scan(data)
    return success_response(
        message=(
            "Cross-exchange arbitrage scan "
            "completed successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
@router.post("/triangular/scan")
async def scan_triangular_opportunities(
    data: TriangularScanRequest,
    service: TriangularArbitrageService = (
        Depends(
            get_triangular_arbitrage_service
        )
    ),
):
    result = service.scan(data)
    return success_response(
        message=(
            "Triangular arbitrage scan "
            "completed successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
