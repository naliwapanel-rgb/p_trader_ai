from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.alert import AlertCreateRequest, AlertResponse, AlertUpdateRequest
from app.services.alert_service import AlertService
from app.utils.responses import success_response

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("")
async def list_my_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alerts = AlertService(db).list_alerts(current_user)

    data = [
        AlertResponse.model_validate(alert).model_dump()
        for alert in alerts
    ]

    return success_response(
        message="Alerts retrieved successfully",
        data=data,
    )


@router.get("/{alert_id}")
async def get_my_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = AlertService(db).get_alert(
        current_user=current_user,
        alert_id=alert_id,
    )

    return success_response(
        message="Alert retrieved successfully",
        data=AlertResponse.model_validate(alert).model_dump(),
    )


@router.post("")
async def create_my_alert(
    data: AlertCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = AlertService(db).create_alert(
        current_user=current_user,
        data=data,
    )

    return success_response(
        message="Alert created successfully",
        data=AlertResponse.model_validate(alert).model_dump(),
    )


@router.put("/{alert_id}")
async def update_my_alert(
    alert_id: int,
    data: AlertUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = AlertService(db).update_alert(
        current_user=current_user,
        alert_id=alert_id,
        data=data,
    )

    return success_response(
        message="Alert updated successfully",
        data=AlertResponse.model_validate(alert).model_dump(),
    )


@router.delete("/{alert_id}")
async def delete_my_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    AlertService(db).delete_alert(
        current_user=current_user,
        alert_id=alert_id,
    )

    return success_response(
        message="Alert deleted successfully",
    )