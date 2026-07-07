from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.alert_repository import AlertRepository
from app.schemas.alert import AlertCreateRequest, AlertUpdateRequest


class AlertService:
    def __init__(self, db: Session):
        self.alert_repository = AlertRepository(db)

    def list_alerts(self, current_user: User):
        return self.alert_repository.list_by_user(
            user_id=current_user.id,
        )

    def get_alert(
        self,
        current_user: User,
        alert_id: int,
    ):
        alert = self.alert_repository.get_by_id_and_user(
            alert_id=alert_id,
            user_id=current_user.id,
        )

        if alert is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found",
            )

        return alert

    def create_alert(
        self,
        current_user: User,
        data: AlertCreateRequest,
    ):
        return self.alert_repository.create(
            user_id=current_user.id,
            symbol=data.symbol.upper(),
            exchange=data.exchange.upper(),
            alert_type=data.alert_type.upper(),
            target_value=data.target_value,
        )

    def update_alert(
        self,
        current_user: User,
        alert_id: int,
        data: AlertUpdateRequest,
    ):
        alert = self.get_alert(
            current_user=current_user,
            alert_id=alert_id,
        )

        return self.alert_repository.update(
            alert=alert,
            symbol=data.symbol.upper() if data.symbol is not None else None,
            exchange=data.exchange.upper() if data.exchange is not None else None,
            alert_type=data.alert_type.upper() if data.alert_type is not None else None,
            target_value=data.target_value,
            is_enabled=data.is_enabled,
            triggered=data.triggered,
        )

    def delete_alert(
        self,
        current_user: User,
        alert_id: int,
    ) -> None:
        alert = self.get_alert(
            current_user=current_user,
            alert_id=alert_id,
        )

        self.alert_repository.delete(alert)