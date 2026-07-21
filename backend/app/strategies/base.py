from typing import (
    Any,
    Protocol,
)
from app.schemas.trading_bot_strategy import (
    TradingBotStrategyContext,
    TradingBotStrategyDecision,
)
class TradingBotStrategy(
    Protocol
):
    strategy_type: str
    def validate_config(
        self,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        ...
    async def evaluate(
        self,
        context: TradingBotStrategyContext,
    ) -> TradingBotStrategyDecision:
        ...
