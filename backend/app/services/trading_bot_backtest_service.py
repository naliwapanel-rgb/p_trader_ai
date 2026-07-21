from sqlalchemy.orm import (
    Session,
)
from app.models.user import (
    User,
)
from app.schemas.trading_bot_backtest import (
    TradingBotBacktestRequest,
    TradingBotBacktestResult,
)
from app.services.backtest_execution_engine import (
    BacktestExecutionEngine,
)
from app.services.backtest_performance_service import (
    BacktestPerformanceService,
)
from app.services.trading_bot_service import (
    TradingBotService,
)
class TradingBotBacktestService:
    def __init__(
        self,
        db: Session,
        *,
        bot_service: (
            TradingBotService | None
        ) = None,
        execution_engine: (
            BacktestExecutionEngine | None
        ) = None,
        performance_service=None,
    ):
        self.db = db
        self.bot_service = (
            bot_service
            or TradingBotService(db)
        )
        self.execution_engine = (
            execution_engine
            or BacktestExecutionEngine()
        )
        self.performance_service = (
            performance_service
            or BacktestPerformanceService
        )
    async def run_backtest(
        self,
        *,
        current_user: User,
        bot_id: int,
        data: TradingBotBacktestRequest,
    ) -> TradingBotBacktestResult:
        bot = self.bot_service.get_bot(
            current_user=current_user,
            bot_id=bot_id,
        )
        execution = (
            await self.execution_engine.run(
                bot=bot,
                data=data,
            )
        )
        return (
            self.performance_service
            .analyze(execution)
        )
