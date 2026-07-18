from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.portfolio import (
    PortfolioCreateRequest,
    PortfolioResponse,
    PortfolioUpdateRequest,
)
from app.schemas.portfolio_sync import (
    PortfolioSyncRequest,
    PortfolioSyncSnapshotResponse,
)
from app.services.portfolio_service import (
    PortfolioService,
)
from app.services.portfolio_sync_service import (
    PortfolioSyncService,
)
from app.utils.responses import success_response
router = APIRouter(
    prefix="/portfolios",
    tags=["Portfolios"],
)
@router.get("")
async def list_my_portfolios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolios = PortfolioService(
        db
    ).list_portfolios(current_user)
    data = [
        PortfolioResponse.model_validate(
            portfolio
        ).model_dump()
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
    portfolio = PortfolioService(
        db
    ).create_portfolio(
        current_user=current_user,
        data=data,
    )
    return success_response(
        message="Portfolio created successfully",
        data=(
            PortfolioResponse.model_validate(
                portfolio
            ).model_dump()
        ),
    )
@router.post("/{portfolio_id}/sync")
async def synchronize_my_portfolio(
    portfolio_id: int,
    data: PortfolioSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = await PortfolioSyncService(
        db
    ).synchronize(
        current_user=current_user,
        portfolio_id=portfolio_id,
        exchange_account_id=(
            data.exchange_account_id
        ),
        category=data.category,
        settle_coin=data.settle_coin,
    )
    return success_response(
        message=(
            "Portfolio synchronization "
            "completed successfully"
        ),
        data=result.model_dump(mode="json"),
    )
@router.get("/{portfolio_id}/sync/latest")
async def get_latest_portfolio_sync(
    portfolio_id: int,
    exchange_account_id: int | None = Query(
        default=None,
        gt=0,
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    snapshot = PortfolioSyncService(
        db
    ).get_latest_snapshot(
        current_user=current_user,
        portfolio_id=portfolio_id,
        exchange_account_id=(
            exchange_account_id
        ),
    )
    data = (
        PortfolioSyncSnapshotResponse
        .model_validate(snapshot)
        .model_dump(mode="json")
    )
    return success_response(
        message=(
            "Latest portfolio synchronization "
            "snapshot retrieved successfully"
        ),
        data=data,
    )
@router.get("/{portfolio_id}/sync/history")
async def list_portfolio_sync_history(
    portfolio_id: int,
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    snapshots = PortfolioSyncService(
        db
    ).list_snapshots(
        current_user=current_user,
        portfolio_id=portfolio_id,
        limit=limit,
    )
    data = [
        PortfolioSyncSnapshotResponse
        .model_validate(snapshot)
        .model_dump(mode="json")
        for snapshot in snapshots
    ]
    return success_response(
        message=(
            "Portfolio synchronization history "
            "retrieved successfully"
        ),
        data=data,
    )
@router.get(
    "/{portfolio_id}/sync/{snapshot_id}"
)
async def get_portfolio_sync_snapshot(
    portfolio_id: int,
    snapshot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    snapshot = PortfolioSyncService(
        db
    ).get_snapshot(
        current_user=current_user,
        portfolio_id=portfolio_id,
        snapshot_id=snapshot_id,
    )
    data = (
        PortfolioSyncSnapshotResponse
        .model_validate(snapshot)
        .model_dump(mode="json")
    )
    return success_response(
        message=(
            "Portfolio synchronization "
            "snapshot retrieved successfully"
        ),
        data=data,
    )
@router.get("/{portfolio_id}")
async def get_my_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = PortfolioService(
        db
    ).get_portfolio(
        current_user=current_user,
        portfolio_id=portfolio_id,
    )
    return success_response(
        message="Portfolio retrieved successfully",
        data=(
            PortfolioResponse.model_validate(
                portfolio
            ).model_dump()
        ),
    )
@router.put("/{portfolio_id}")
async def update_my_portfolio(
    portfolio_id: int,
    data: PortfolioUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = PortfolioService(
        db
    ).update_portfolio(
        current_user=current_user,
        portfolio_id=portfolio_id,
        data=data,
    )
    return success_response(
        message="Portfolio updated successfully",
        data=(
            PortfolioResponse.model_validate(
                portfolio
            ).model_dump()
        ),
    )
@router.delete("/{portfolio_id}")
async def delete_my_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    PortfolioService(db).delete_portfolio(
        current_user=current_user,
        portfolio_id=portfolio_id,
    )
    return success_response(
        message="Portfolio deleted successfully",
    )
