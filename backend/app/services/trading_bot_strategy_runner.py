from collections.abc import (
    Callable,
)
from datetime import (
    UTC,
    datetime,
)
from typing import (
    Any,
)
from app.schemas.market_scanner import (
    MarketTickerSnapshot,
)
from app.schemas.trading_bot_strategy import (
    TradingBotMarketSample,
    TradingBotStrategyContext,
    TradingBotStrategyDecision,
    TradingBotStrategyState,
)
from app.strategies.registry import (
    TradingBotStrategyRegistry,
)
StrategyClock = Callable[[], datetime]
class TradingBotStrategyRunner:
    def __init__(
        self,
        *,
        registry: (
            TradingBotStrategyRegistry
            | None
        ) = None,
        clock: StrategyClock | None = None,
    ):
        self.registry = (
            registry
            or (
                TradingBotStrategyRegistry
                .default()
            )
        )
        self.clock = (
            clock
            or (
                lambda: datetime.now(UTC)
            )
        )
    def validate_bot(
        self,
        bot,
    ) -> dict[str, Any]:
        strategy = self.registry.get(
            bot.strategy_type
        )
        config = dict(
            bot.strategy_config or {}
        )
        return strategy.validate_config(
            config
        )
    async def run(
        self,
        *,
        bot,
        ticker: MarketTickerSnapshot,
        market_history: (
            list[
                TradingBotMarketSample
            ]
            | None
        ) = None,
        state: (
            TradingBotStrategyState | None
        ) = None,
    ) -> TradingBotStrategyDecision:
        strategy = self.registry.get(
            bot.strategy_type
        )
        config = strategy.validate_config(
            dict(
                bot.strategy_config or {}
            )
        )
        context = TradingBotStrategyContext(
            bot_id=bot.id,
            user_id=bot.user_id,
            strategy_type=(
                bot.strategy_type
            ),
            symbol=bot.symbol,
            category=bot.category,
            timeframe=bot.timeframe,
            config=config,
            ticker=ticker,
            market_history=list(
                market_history or []
            ),
            evaluated_at=self.clock(),
            state=(
                state
                if state is not None
                else TradingBotStrategyState()
            ),
        )
        decision = await strategy.evaluate(
            context
        )
        return (
            TradingBotStrategyDecision
            .model_validate(decision)
        )
