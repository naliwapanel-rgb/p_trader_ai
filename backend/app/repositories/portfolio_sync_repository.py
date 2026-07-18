from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.portfolio_sync_snapshot import (
    PortfolioSyncSnapshot,
)
from app.schemas.portfolio_sync import (
    PortfolioSyncSnapshotCreate,
)
class PortfolioSyncRepository:
    def __init__(self, db: Session):
        self.db = db
    def get_by_id_and_user(
        self,
        snapshot_id: int,
        user_id: int,
    ) -> PortfolioSyncSnapshot | None:
        return (
            self.db.query(PortfolioSyncSnapshot)
            .filter(
                PortfolioSyncSnapshot.id
                == snapshot_id,
                PortfolioSyncSnapshot.user_id
                == user_id,
            )
            .first()
        )
    def get_by_fingerprint(
        self,
        portfolio_id: int,
        exchange_account_id: int,
        fingerprint: str,
    ) -> PortfolioSyncSnapshot | None:
        return (
            self.db.query(PortfolioSyncSnapshot)
            .filter(
                PortfolioSyncSnapshot.portfolio_id
                == portfolio_id,
                PortfolioSyncSnapshot
                .exchange_account_id
                == exchange_account_id,
                PortfolioSyncSnapshot.fingerprint
                == fingerprint,
            )
            .first()
        )
    def get_latest(
        self,
        user_id: int,
        portfolio_id: int,
        exchange_account_id: int | None = None,
    ) -> PortfolioSyncSnapshot | None:
        query = (
            self.db.query(PortfolioSyncSnapshot)
            .filter(
                PortfolioSyncSnapshot.user_id
                == user_id,
                PortfolioSyncSnapshot.portfolio_id
                == portfolio_id,
            )
        )
        if exchange_account_id is not None:
            query = query.filter(
                PortfolioSyncSnapshot
                .exchange_account_id
                == exchange_account_id
            )
        return (
            query.order_by(
                PortfolioSyncSnapshot.synced_at.desc(),
                PortfolioSyncSnapshot.id.desc(),
            )
            .first()
        )
    def list_by_portfolio(
        self,
        user_id: int,
        portfolio_id: int,
        limit: int = 50,
    ) -> list[PortfolioSyncSnapshot]:
        return (
            self.db.query(PortfolioSyncSnapshot)
            .filter(
                PortfolioSyncSnapshot.user_id
                == user_id,
                PortfolioSyncSnapshot.portfolio_id
                == portfolio_id,
            )
            .order_by(
                PortfolioSyncSnapshot.synced_at.desc(),
                PortfolioSyncSnapshot.id.desc(),
            )
            .limit(limit)
            .all()
        )
    def create_or_get(
        self,
        data: PortfolioSyncSnapshotCreate,
    ) -> tuple[PortfolioSyncSnapshot, bool]:
        existing = self.get_by_fingerprint(
            portfolio_id=data.portfolio_id,
            exchange_account_id=(
                data.exchange_account_id
            ),
            fingerprint=data.fingerprint,
        )
        if existing is not None:
            return existing, False
        snapshot = PortfolioSyncSnapshot(
            **data.model_dump()
        )
        self.db.add(snapshot)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            existing = self.get_by_fingerprint(
                portfolio_id=data.portfolio_id,
                exchange_account_id=(
                    data.exchange_account_id
                ),
                fingerprint=data.fingerprint,
            )
            if existing is None:
                raise
            return existing, False
        self.db.refresh(snapshot)
        return snapshot, True
