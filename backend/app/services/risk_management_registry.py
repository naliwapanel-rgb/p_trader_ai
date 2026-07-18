from app.services.risk_management_service import (
    RiskManagementService,
)
_risk_management_services: dict[
    int,
    RiskManagementService,
] = {}
def get_user_risk_management_service(
    user_id: int,
) -> RiskManagementService:
    service = _risk_management_services.get(user_id)
    if service is None:
        service = RiskManagementService()
        _risk_management_services[user_id] = service
    return service
def clear_risk_management_services() -> None:
    _risk_management_services.clear()
