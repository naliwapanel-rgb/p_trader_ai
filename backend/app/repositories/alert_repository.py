from sqlalchemy.orm import Session

from app.models.alert import Alert


class AlertRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_user(self, user_id: int) -> list[Alert]:
        return self.db.query(Alert).filter(Alert.user_id == user_id).all()

    def get_by_id_and_user(
        self,
        alert_id: int,
        user_id: int,
    ) -> Alert | None:
        return (
            self.db.query(Alert)
            .filter(
                Alert.id == alert_id,
                Alert.user_id == user_id,
            )
            .first()
        )

    def create(
        self,
        user_id: int,
        symbol: str,
        exchange: str,
        alert_type: str,
        target_value: float,
    ) -> Alert:
        alert = Alert(
            user_id=user_id,
            symbol=symbol,
            exchange=exchange,
            alert_type=alert_type,
            target_value=target_value,
        )

        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        return alert

    def update(
        self,
        alert: Alert,
        symbol: str | None = None,
        exchange: str | None = None,
        alert_type: str | None = None,
        target_value: float | None = None,
        is_enabled: bool | None = None,
        triggered: bool | None = None,
    ) -> Alert:
        if symbol is not None:
            alert.symbol = symbol

        if exchange is not None:
            alert.exchange = exchange

        if alert_type is not None:
            alert.alert_type = alert_type

        if target_value is not None:
            alert.target_value = target_value

        if is_enabled is not None:
            alert.is_enabled = is_enabled

        if triggered is not None:
            alert.triggered = triggered

        self.db.commit()
        self.db.refresh(alert)

        return alert

    def delete(self, alert: Alert) -> None:
        self.db.delete(alert)
        self.db.commit()