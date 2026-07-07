from sqlalchemy.orm import Session

from app.models.watchlist import WatchlistItem


class WatchlistRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_user(self, user_id: int) -> list[WatchlistItem]:
        return (
            self.db.query(WatchlistItem)
            .filter(WatchlistItem.user_id == user_id)
            .all()
        )

    def get_by_id_and_user(
        self,
        item_id: int,
        user_id: int,
    ) -> WatchlistItem | None:
        return (
            self.db.query(WatchlistItem)
            .filter(
                WatchlistItem.id == item_id,
                WatchlistItem.user_id == user_id,
            )
            .first()
        )

    def get_by_symbol_exchange(
        self,
        user_id: int,
        symbol: str,
        exchange: str,
    ) -> WatchlistItem | None:
        return (
            self.db.query(WatchlistItem)
            .filter(
                WatchlistItem.user_id == user_id,
                WatchlistItem.symbol == symbol,
                WatchlistItem.exchange == exchange,
            )
            .first()
        )

    def create(
        self,
        user_id: int,
        symbol: str,
        exchange: str,
    ) -> WatchlistItem:
        item = WatchlistItem(
            user_id=user_id,
            symbol=symbol,
            exchange=exchange,
        )

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        return item

    def delete(self, item: WatchlistItem) -> None:
        self.db.delete(item)
        self.db.commit()