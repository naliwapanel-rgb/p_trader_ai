from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.watchlist_repository import WatchlistRepository
from app.schemas.watchlist import WatchlistCreateRequest


class WatchlistService:
    def __init__(self, db: Session):
        self.watchlist_repository = WatchlistRepository(db)

    def list_items(self, current_user: User):
        return self.watchlist_repository.list_by_user(
            user_id=current_user.id,
        )

    def create_item(
        self,
        current_user: User,
        data: WatchlistCreateRequest,
    ):
        symbol = data.symbol.upper()
        exchange = data.exchange.upper()

        existing_item = self.watchlist_repository.get_by_symbol_exchange(
            user_id=current_user.id,
            symbol=symbol,
            exchange=exchange,
        )

        if existing_item:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Symbol already exists in watchlist",
            )

        return self.watchlist_repository.create(
            user_id=current_user.id,
            symbol=symbol,
            exchange=exchange,
        )

    def delete_item(
        self,
        current_user: User,
        item_id: int,
    ) -> None:
        item = self.watchlist_repository.get_by_id_and_user(
            item_id=item_id,
            user_id=current_user.id,
        )

        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Watchlist item not found",
            )

        self.watchlist_repository.delete(item)