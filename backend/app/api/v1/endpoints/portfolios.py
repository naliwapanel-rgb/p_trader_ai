from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.portfolio import PortfolioCreateRequest, PortfolioResponse
from app.services.portfolio_service import PortfolioService
from app.utils.responses import success_response

router = APIRouter(prefix="/portfolios", tags=["Portfolios"])


@router.get("")
async def list_my_portfolios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolios = PortfolioService(db).list_portfolios(current_user)

    data = [
        PortfolioResponse.model_validate(portfolio).model_dump()
        for portfolio in portfolios
    ]

    return success_response(
        message="Portfolios retrieved successfully",
        data=data,
    )


@router.post("")
async def create_my_portfolio(
    data: PortfolioCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = PortfolioService(db).create_portfolio(
        current_user=current_user,
        data=data,
    )

    response_data = PortfolioResponse.model_validate(portfolio).model_dump()

    return success_response(
        message="Portfolio created successfully",
        data=response_data,
    )