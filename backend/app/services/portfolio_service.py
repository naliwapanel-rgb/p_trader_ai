from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.portfolio_repository import PortfolioRepository
from app.schemas.portfolio import PortfolioCreateRequest


class PortfolioService:
    def __init__(self, db: Session):
        self.portfolio_repository = PortfolioRepository(db)

    def list_portfolios(self, current_user: User):
        return self.portfolio_repository.list_by_user(
            user_id=current_user.id,
        )

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