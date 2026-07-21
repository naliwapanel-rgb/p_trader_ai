from datetime import (
    UTC,
    datetime,
)
from sqlalchemy.orm import (
    Session,
)
from app.models.trading_bot import (
    TradingBot,
)
from app.schemas.trading_bot import (
    TradingBotCreateRequest,
    TradingBotUpdateRequest,
)
class TradingBotRepository:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db
    def create(
        self,
        *,
        user_id: int,
        data: TradingBotCreateRequest,
    ) -> TradingBot:
        bot = TradingBot(
            user_id=user_id,
            status="DRAFT",
            **data.model_dump(),
        )
        self.db.add(bot)
        self.db.commit()
        self.db.refresh(bot)
        return bot
    def get_by_id_and_user(
        self,
        *,
        bot_id: int,
        user_id: int,
    ) -> TradingBot | None:
        return (
            self.db.query(TradingBot)
            .filter(
                TradingBot.id == bot_id,
                TradingBot.user_id
                == user_id,
            )
            .first()
        )
    def get_by_name_and_user(
        self,
        *,
        name: str,
        user_id: int,
    ) -> TradingBot | None:
        return (
            self.db.query(TradingBot)
            .filter(
                TradingBot.name == name,
                TradingBot.user_id
                == user_id,
            )
            .first()
        )
    def list_by_user(
        self,
        *,
        user_id: int,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TradingBot]:
        query = (
            self.db.query(TradingBot)
            .filter(
                TradingBot.user_id
                == user_id
            )
        )
        if status is not None:
            query = query.filter(
                TradingBot.status
                == status
            )
        return (
            query.order_by(
                TradingBot.updated_at.desc(),
                TradingBot.id.desc(),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )
    def list_by_status(
        self,
        *,
        status: str,
    ) -> list[TradingBot]:
        return (
            self.db.query(TradingBot)
            .filter(
                TradingBot.status == status
            )
            .order_by(
                TradingBot.id.asc(),
            )
            .all()
        )
    @staticmethod
    def _validate_effective_values(
        *,
        bot: TradingBot,
        fields: dict,
    ) -> None:
        paper_trading = fields.get(
            "paper_trading",
            bot.paper_trading,
        )
        dry_run = fields.get(
            "dry_run",
            bot.dry_run,
        )
        if (
            not paper_trading
            and not dry_run
        ):
            raise ValueError(
                "At least paper_trading or "
                "dry_run must remain enabled"
            )
        risk_per_trade = fields.get(
            "risk_per_trade_percent",
            bot.risk_per_trade_percent,
        )
        daily_loss = fields.get(
            "max_daily_loss_percent",
            bot.max_daily_loss_percent,
        )
        drawdown = fields.get(
            "max_drawdown_percent",
            bot.max_drawdown_percent,
        )
        if risk_per_trade > daily_loss:
            raise ValueError(
                "risk_per_trade_percent "
                "cannot exceed "
                "max_daily_loss_percent"
            )
        if daily_loss > drawdown:
            raise ValueError(
                "max_daily_loss_percent "
                "cannot exceed "
                "max_drawdown_percent"
            )
    def update(
        self,
        *,
        bot: TradingBot,
        data: TradingBotUpdateRequest,
    ) -> TradingBot:
        fields = data.model_dump(
            exclude_unset=True
        )
        self._validate_effective_values(
            bot=bot,
            fields=fields,
        )
        for key, value in fields.items():
            setattr(bot, key, value)
        bot.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(bot)
        return bot
    def save_lifecycle(
        self,
        *,
        bot: TradingBot,
        status: str,
        updated_at: datetime,
        started_at=...,
        stopped_at=...,
        last_error=...,
        last_run_at=...,
    ) -> TradingBot:
        bot.status = status
        bot.updated_at = updated_at
        if started_at is not ...:
            bot.started_at = started_at
        if stopped_at is not ...:
            bot.stopped_at = stopped_at
        if last_error is not ...:
            bot.last_error = last_error
        if last_run_at is not ...:
            bot.last_run_at = last_run_at
        self.db.commit()
        self.db.refresh(bot)
        return bot
    def delete(
        self,
        bot: TradingBot,
    ) -> None:
        self.db.delete(bot)
        self.db.commit()
