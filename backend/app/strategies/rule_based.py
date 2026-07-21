from typing import (
    Any,
)
from app.schemas.trading_bot_strategy import (
    RuleBasedStrategyConfig,
    TradingBotStrategyContext,
    TradingBotStrategyDecision,
)
class RuleBasedTradingStrategy:
    strategy_type = "RULE_BASED"
    def validate_config(
        self,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        validated = (
            RuleBasedStrategyConfig
            .model_validate(config)
        )
        return validated.model_dump()
    @staticmethod
    def _confidence(
        *,
        change_percent: float,
        scale_percent: float,
    ) -> float:
        return min(
            1.0,
            abs(change_percent)
            / scale_percent,
        )
    @staticmethod
    def _decision(
        *,
        context: TradingBotStrategyContext,
        action: str,
        confidence: float,
        reason: str,
        config: RuleBasedStrategyConfig,
    ) -> TradingBotStrategyDecision:
        ticker = context.ticker
        return TradingBotStrategyDecision(
            action=action,
            confidence=confidence,
            reason=reason,
            reference_price=(
                ticker.last_price
            ),
            evaluated_at=(
                context.evaluated_at
            ),
            metadata={
                "symbol": ticker.symbol,
                "change_percent_24h": (
                    ticker
                    .price_change_percent_24h
                ),
                "spread_percent": (
                    ticker.spread_percent
                ),
                "turnover_24h": (
                    ticker.turnover_24h
                ),
                "buy_threshold": (
                    config
                    .buy_change_percent_24h
                ),
                "sell_threshold": (
                    config
                    .sell_change_percent_24h
                ),
            },
        )
    async def evaluate(
        self,
        context: TradingBotStrategyContext,
    ) -> TradingBotStrategyDecision:
        config = (
            RuleBasedStrategyConfig
            .model_validate(context.config)
        )
        ticker = context.ticker
        if ticker.last_price <= 0:
            return self._decision(
                context=context,
                action="HOLD",
                confidence=0.0,
                reason=(
                    "Ticker price is unavailable "
                    "or invalid"
                ),
                config=config,
            )
        if (
            ticker.turnover_24h
            < config.minimum_turnover_24h
        ):
            return self._decision(
                context=context,
                action="HOLD",
                confidence=0.0,
                reason=(
                    "Market turnover is below "
                    "the configured minimum"
                ),
                config=config,
            )
        if (
            ticker.spread_percent
            > config.maximum_spread_percent
        ):
            return self._decision(
                context=context,
                action="HOLD",
                confidence=0.0,
                reason=(
                    "Market spread exceeds the "
                    "configured maximum"
                ),
                config=config,
            )
        change = (
            ticker.price_change_percent_24h
        )
        confidence = self._confidence(
            change_percent=change,
            scale_percent=(
                config.confidence_scale_percent
            ),
        )
        if (
            change
            >= config.buy_change_percent_24h
        ):
            return self._decision(
                context=context,
                action="BUY",
                confidence=confidence,
                reason=(
                    "The 24-hour price change "
                    "reached the configured "
                    "buy threshold"
                ),
                config=config,
            )
        if (
            change
            <= config.sell_change_percent_24h
        ):
            return self._decision(
                context=context,
                action="SELL",
                confidence=confidence,
                reason=(
                    "The 24-hour price change "
                    "reached the configured "
                    "sell threshold"
                ),
                config=config,
            )
        return self._decision(
            context=context,
            action="HOLD",
            confidence=0.0,
            reason=(
                "No configured rule threshold "
                "was reached"
            ),
            config=config,
        )
