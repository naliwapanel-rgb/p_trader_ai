from decimal import (
    Decimal,
)
from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.orm import (
    Session,
)
from app.models.user import (
    User,
)
from app.repositories.paper_trading_repository import (
    PaperTradingRepository,
)
from app.schemas.paper_trading import (
    PaperTradingAccountResponse,
    PaperTradingOrderResponse,
    PaperTradingPositionResponse,
)
from app.schemas.trading_bot_performance import (
    PaperTradingAccountSummaryResult,
    PaperTradingOrderHistoryResult,
    PaperTradingPerformanceResult,
    PaperTradingPositionHistoryResult,
)
from app.services.trading_bot_service import (
    TradingBotService,
)
class PaperTradingHistoryService:
    def __init__(
        self,
        db: Session,
        *,
        bot_service: (
            TradingBotService | None
        ) = None,
        repository: (
            PaperTradingRepository | None
        ) = None,
    ):
        self.db = db
        self.bot_service = (
            bot_service
            or TradingBotService(db)
        )
        self.repository = (
            repository
            or PaperTradingRepository(db)
        )
    @staticmethod
    def _decimal(
        value,
    ) -> Decimal:
        return Decimal(str(value))
    def _get_bot_and_account(
        self,
        *,
        current_user: User,
        bot_id: int,
    ):
        bot = self.bot_service.get_bot(
            current_user=current_user,
            bot_id=bot_id,
        )
        account = (
            self.repository
            .get_account_by_bot(
                user_id=current_user.id,
                trading_bot_id=bot.id,
            )
        )
        if account is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Paper trading account "
                    "not found"
                ),
            )
        return bot, account
    def get_account_summary(
        self,
        *,
        current_user: User,
        bot_id: int,
    ) -> PaperTradingAccountSummaryResult:
        bot, account = (
            self._get_bot_and_account(
                current_user=current_user,
                bot_id=bot_id,
            )
        )
        return (
            PaperTradingAccountSummaryResult(
                bot_id=bot.id,
                account=(
                    PaperTradingAccountResponse
                    .model_validate(account)
                ),
            )
        )
    def list_orders(
        self,
        *,
        current_user: User,
        bot_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> PaperTradingOrderHistoryResult:
        bot, account = (
            self._get_bot_and_account(
                current_user=current_user,
                bot_id=bot_id,
            )
        )
        orders = self.repository.list_orders(
            paper_account_id=account.id,
            limit=limit,
            offset=offset,
        )
        total_count = (
            self.repository.count_orders(
                paper_account_id=account.id
            )
        )
        return PaperTradingOrderHistoryResult(
            bot_id=bot.id,
            paper_account_id=account.id,
            total_count=total_count,
            limit=limit,
            offset=offset,
            items=[
                PaperTradingOrderResponse
                .model_validate(order)
                for order in orders
            ],
        )
    def list_positions(
        self,
        *,
        current_user: User,
        bot_id: int,
        position_status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PaperTradingPositionHistoryResult:
        bot, account = (
            self._get_bot_and_account(
                current_user=current_user,
                bot_id=bot_id,
            )
        )
        positions = (
            self.repository.list_positions(
                paper_account_id=account.id,
                status=position_status,
                limit=limit,
                offset=offset,
            )
        )
        total_count = (
            self.repository.count_positions(
                paper_account_id=account.id,
                status=position_status,
            )
        )
        return (
            PaperTradingPositionHistoryResult(
                bot_id=bot.id,
                paper_account_id=account.id,
                position_status=(
                    position_status
                ),
                total_count=total_count,
                limit=limit,
                offset=offset,
                items=[
                    PaperTradingPositionResponse
                    .model_validate(position)
                    for position in positions
                ],
            )
        )
    def get_performance(
        self,
        *,
        current_user: User,
        bot_id: int,
    ) -> PaperTradingPerformanceResult:
        bot, account = (
            self._get_bot_and_account(
                current_user=current_user,
                bot_id=bot_id,
            )
        )
        positions = (
            self.repository.list_positions(
                paper_account_id=account.id,
                status=None,
                limit=None,
                offset=0,
            )
        )
        closed_positions = [
            position
            for position in positions
            if position.status == "CLOSED"
        ]
        open_positions = [
            position
            for position in positions
            if position.status == "OPEN"
        ]
        net_closed_results = [
            (
                self._decimal(
                    position.realized_pnl_usd
                )
                - self._decimal(
                    position.total_fees_usd
                )
            )
            for position in closed_positions
        ]
        winning_results = [
            result
            for result in net_closed_results
            if result > 0
        ]
        losing_results = [
            result
            for result in net_closed_results
            if result < 0
        ]
        breakeven_results = [
            result
            for result in net_closed_results
            if result == 0
        ]
        gross_realized = sum(
            (
                self._decimal(
                    position.realized_pnl_usd
                )
                for position in closed_positions
            ),
            Decimal("0"),
        )
        realized_fees = sum(
            (
                self._decimal(
                    position.total_fees_usd
                )
                for position in closed_positions
            ),
            Decimal("0"),
        )
        net_realized = (
            gross_realized
            - realized_fees
        )
        gross_profit = sum(
            winning_results,
            Decimal("0"),
        )
        gross_loss = abs(
            sum(
                losing_results,
                Decimal("0"),
            )
        )
        completed_count = len(
            closed_positions
        )
        winning_count = len(
            winning_results
        )
        losing_count = len(
            losing_results
        )
        win_rate = (
            (
                Decimal(winning_count)
                / Decimal(completed_count)
                * Decimal("100")
            )
            if completed_count
            else Decimal("0")
        )
        average_win = (
            gross_profit
            / Decimal(winning_count)
            if winning_count
            else Decimal("0")
        )
        average_loss = (
            -gross_loss
            / Decimal(losing_count)
            if losing_count
            else Decimal("0")
        )
        profit_factor = (
            gross_profit
            / gross_loss
            if gross_loss > 0
            else None
        )
        initial_balance = self._decimal(
            account.initial_balance_usd
        )
        equity = self._decimal(
            account.equity_usd
        )
        total_net_pnl = (
            equity
            - initial_balance
        )
        return_percent = (
            (
                total_net_pnl
                / initial_balance
                * Decimal("100")
            )
            if initial_balance > 0
            else Decimal("0")
        )
        return PaperTradingPerformanceResult(
            bot_id=bot.id,
            paper_account_id=account.id,
            currency=account.currency,
            initial_balance_usd=float(
                initial_balance
            ),
            cash_balance_usd=(
                account.cash_balance_usd
            ),
            reserved_balance_usd=(
                account.reserved_balance_usd
            ),
            equity_usd=float(equity),
            order_count=(
                self.repository.count_orders(
                    paper_account_id=account.id
                )
            ),
            trade_count=len(positions),
            completed_trade_count=(
                completed_count
            ),
            open_trade_count=len(
                open_positions
            ),
            winning_trade_count=(
                winning_count
            ),
            losing_trade_count=(
                losing_count
            ),
            breakeven_trade_count=len(
                breakeven_results
            ),
            gross_realized_pnl_usd=float(
                gross_realized
            ),
            realized_fees_usd=float(
                realized_fees
            ),
            net_realized_pnl_usd=float(
                net_realized
            ),
            unrealized_pnl_usd=(
                account.unrealized_pnl_usd
            ),
            total_fees_usd=(
                account.total_fees_usd
            ),
            total_net_pnl_usd=float(
                total_net_pnl
            ),
            gross_profit_usd=float(
                gross_profit
            ),
            gross_loss_usd=float(
                gross_loss
            ),
            win_rate_percent=float(
                win_rate
            ),
            average_win_usd=float(
                average_win
            ),
            average_loss_usd=float(
                average_loss
            ),
            profit_factor=(
                float(profit_factor)
                if profit_factor is not None
                else None
            ),
            return_percent=float(
                return_percent
            ),
        )
