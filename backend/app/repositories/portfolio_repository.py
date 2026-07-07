from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio


class PortfolioRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_user(self, user_id: int) -> list[Portfolio]:
        return self.db.query(Portfolio).filter(Portfolio.user_id == user_id).all()

    def get_by_id_and_user(
        self,
        portfolio_id: int,
        user_id: int,
    ) -> Portfolio | None:
        return (
            self.db.query(Portfolio)
            .filter(
                Portfolio.id == portfolio_id,
                Portfolio.user_id == user_id,
            )
            .first()
        )

    def create(
        self,
        user_id: int,
        name: str,
        base_currency: str,
    ) -> Portfolio:
        portfolio = Portfolio(
            user_id=user_id,
            name=name,
            base_currency=base_currency,
        )

        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)

        return portfolio

    def update(
        self,
        portfolio: Portfolio,
        name: str | None = None,
        base_currency: str | None = None,
        total_value: float | None = None,
        profit_loss: float | None = None,
    ) -> Portfolio:
        if name is not None:
            portfolio.name = name

        if base_currency is not None:
            portfolio.base_currency = base_currency

        if total_value is not None:
            portfolio.total_value = total_value

        if profit_loss is not None:
            portfolio.profit_loss = profit_loss

        self.db.commit()
        self.db.refresh(portfolio)

        return portfolio

    def delete(self, portfolio: Portfolio) -> None:
        self.db.delete(portfolio)
        self.db.commit()