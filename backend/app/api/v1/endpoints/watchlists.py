from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.watchlist import WatchlistCreateRequest, WatchlistResponse
from app.services.watchlist_service import WatchlistService
from app.utils.responses import success_response

router = APIRouter(prefix="/watchlists", tags=["Watchlists"])


@router.get("")
async def list_my_watchlist_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = WatchlistService(db).list_items(current_user)

    data = [
        WatchlistResponse.model_validate(item).model_dump()
        for item in items
    ]

    return success_response(
        message="Watchlist items retrieved successfully",
        data=data,
    )


@router.post("")
async def create_my_watchlist_item(
    data: WatchlistCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = WatchlistService(db).create_item(
        current_user=current_user,
        data=data,
    )

    return success_response(
        message="Watchlist item created successfully",
        data=WatchlistResponse.model_validate(item).model_dump(),
    )


@router.delete("/{item_id}")
async def delete_my_watchlist_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    WatchlistService(db).delete_item(
        current_user=current_user,
        item_id=item_id,
    )

    return success_response(
        message="Watchlist item deleted successfully",
    )