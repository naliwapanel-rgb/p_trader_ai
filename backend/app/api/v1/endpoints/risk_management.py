from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.risk_management import (
    PositionSizeRequest,
    PreTradeRiskRequest,
    RiskConfigurationUpdate,
)
from app.services.risk_management_service import (
    PositionSizeCalculator,
    RiskManagementService,
)
from app.utils.responses import success_response
router = APIRouter(
    prefix="/risk-management",
    tags=["Risk Management"],
)
_risk_management_services: dict[
    int,
    RiskManagementService,
] = {}
def get_risk_management_service(
    current_user: User = Depends(get_current_user),
) -> RiskManagementService:
    service = _risk_management_services.get(
        current_user.id
    )
    if service is None:
        service = RiskManagementService()
        _risk_management_services[current_user.id] = (
            service
        )
    return service
@router.get("/configuration")
async def get_risk_configuration(
    service: RiskManagementService = Depends(
        get_risk_management_service
    ),
):
    configuration = service.get_configuration()
    return success_response(
        message=(
            "Risk configuration retrieved "
            "successfully"
        ),
        data=configuration,
    )
@router.put("/configuration")
async def update_risk_configuration(
    data: RiskConfigurationUpdate,
    service: RiskManagementService = Depends(
        get_risk_management_service
    ),
):
    configuration = service.update_configuration(
        data
    )
    return success_response(
        message=(
            "Risk configuration updated "
            "successfully"
        ),
        data=configuration,
    )
@router.post("/configuration/reset")
async def reset_risk_configuration(
    service: RiskManagementService = Depends(
        get_risk_management_service
    ),
):
    configuration = service.restore_defaults()
    return success_response(
        message=(
            "Risk configuration restored to "
            "defaults successfully"
        ),
        data=configuration,
    )
@router.post("/position-size")
async def calculate_position_size(
    data: PositionSizeRequest,
    service: RiskManagementService = Depends(
        get_risk_management_service
    ),
):
    configuration = service.get_configuration()
    effective_risk_percent = min(
        data.risk_percent,
        configuration.max_risk_per_trade_percent,
    )
    effective_request = data.model_copy(
        update={
            "risk_percent": effective_risk_percent,
            "leverage": min(
                data.leverage,
                configuration.max_leverage,
            ),
        }
    )
    result = PositionSizeCalculator.calculate(
        effective_request
    )
    return success_response(
        message="Position size calculated successfully",
        data=result,
    )
@router.post("/pre-trade-validation")
async def validate_pre_trade_risk(
    data: PreTradeRiskRequest,
    service: RiskManagementService = Depends(
        get_risk_management_service
    ),
):
    result = service.validate_pre_trade(data)
    return success_response(
        message=(
            "Pre-trade risk validation completed "
            "successfully"
        ),
        data=result,
    )
