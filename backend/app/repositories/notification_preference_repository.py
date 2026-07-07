from sqlalchemy.orm import Session

from app.models.notification_preference import NotificationPreference


class NotificationPreferenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(
        self,
        user_id: int,
    ) -> NotificationPreference | None:
        return (
            self.db.query(NotificationPreference)
            .filter(NotificationPreference.user_id == user_id)
            .first()
        )

    def create_default(
        self,
        user_id: int,
    ) -> NotificationPreference:
        preference = NotificationPreference(user_id=user_id)

        self.db.add(preference)
        self.db.commit()
        self.db.refresh(preference)

        return preference

    def update(
        self,
        preference: NotificationPreference,
        **fields,
    ) -> NotificationPreference:
        for key, value in fields.items():
            if value is not None:
                setattr(preference, key, value)

        self.db.commit()
        self.db.refresh(preference)

        return preference