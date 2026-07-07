from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.portfolio_repository import PortfolioRepository
from app.schemas.portfolio import PortfolioCreateRequest, PortfolioUpdateRequest


class PortfolioService:
    def __init__(self, db: Session):
        self.portfolio_repository = PortfolioRepository(db)

    def list_portfolios(self, current_user: User):
        return self.portfolio_repository.list_by_user(
            user_id=current_user.id,
        )

    def get_portfolio(
        self,
        current_user: User,
        portfolio_id: int,
    ):
        portfolio = self.portfolio_repository.get_by_id_and_user(
            portfolio_id=portfolio_id,
            user_id=current_user.id,
        )

        if portfolio is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found",
            )

        return portfolio

    def create_portfolio(
        self,
        current_user: User,
        data: PortfolioCreateRequest,
    ):
        return self.portfolio_repository.create(
            user_id=current_user.id,
            name=data.name,
            base_currency=data.base_currency.upper(),
        )

    def update_portfolio(
        self,
        current_user: User,
        portfolio_id: int,
        data: PortfolioUpdateRequest,
    ):
        portfolio = self.get_portfolio(
            current_user=current_user,
            portfolio_id=portfolio_id,
        )

        return self.portfolio_repository.update(
            portfolio=portfolio,
            name=data.name,
            base_currency=data.base_currency.upper()
            if data.base_currency is not None
            else None,
            total_value=data.total_value,
            profit_loss=data.profit_loss,
        )

    def delete_portfolio(
        self,
        current_user: User,
        portfolio_id: int,
    ) -> None:
        portfolio = self.get_portfolio(
            current_user=current_user,
            portfolio_id=portfolio_id,
        )

        self.portfolio_repository.delete(portfolio)