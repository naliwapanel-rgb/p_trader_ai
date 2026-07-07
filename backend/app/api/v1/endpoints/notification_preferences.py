from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.notification_preference import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdateRequest,
)
from app.services.notification_preference_service import (
    NotificationPreferenceService,
)
from app.utils.responses import success_response

router = APIRouter(
    prefix="/notification-preferences",
    tags=["Notification Preferences"],
)


@router.get("")
async def get_my_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preference = NotificationPreferenceService(db).get_or_create_preferences(
        current_user
    )

    return success_response(
        message="Notification preferences retrieved successfully",
        data=NotificationPreferenceResponse.model_validate(preference).model_dump(),
    )


@router.put("")
async def update_my_notification_preferences(
    data: NotificationPreferenceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preference = NotificationPreferenceService(db).update_preferences(
        current_user=current_user,
        data=data,
    )

    return success_response(
        message="Notification preferences updated successfully",
        data=NotificationPreferenceResponse.model_validate(preference).model_dump(),
    )