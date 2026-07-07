from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.notification_preference_repository import (
    NotificationPreferenceRepository,
)
from app.schemas.notification_preference import NotificationPreferenceUpdateRequest


class NotificationPreferenceService:
    def __init__(self, db: Session):
        self.preference_repository = NotificationPreferenceRepository(db)

    def get_or_create_preferences(self, current_user: User):
        preference = self.preference_repository.get_by_user_id(current_user.id)

        if preference is None:
            preference = self.preference_repository.create_default(current_user.id)

        return preference

    def update_preferences(
        self,
        current_user: User,
        data: NotificationPreferenceUpdateRequest,
    ):
        preference = self.get_or_create_preferences(current_user)

        return self.preference_repository.update(
            preference,
            **data.model_dump(),
        )