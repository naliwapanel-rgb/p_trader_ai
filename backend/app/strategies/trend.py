from typing import (
    Any,
)
from app.schemas.trading_bot_strategy import (
    TradingBotStrategyContext,
    TradingBotStrategyDecision,
    TrendStrategyConfig,
)
from app.services.trading_bot_indicator_service import (
    TradingBotIndicatorService,
)
class TrendTradingStrategy:
    strategy_type = "TREND"
    def __init__(
        self,
        *,
        indicators: (
            TradingBotIndicatorService | None
        ) = None,
    ):
        self.indicators = (
            indicators
            or TradingBotIndicatorService()
        )
    def validate_config(
        self,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        validated = (
            TrendStrategyConfig
            .model_validate(config)
        )
        return validated.model_dump()
    @staticmethod
    def _confidence(
        *,
        ema_separation_percent: float,
        momentum_percent: float,
        scale_percent: float,
    ) -> float:
        strength = max(
            abs(
                ema_separation_percent
            ),
            abs(momentum_percent),
        )
        return min(
            1.0,
            max(
                0.0,
                strength
                / scale_percent,
            ),
        )
    @staticmethod
    def _direction_allows(
        *,
        configured_direction: str,
        position_side: str,
    ) -> bool:
        return (
            configured_direction == "BOTH"
            or configured_direction
            == position_side
        )
    @staticmethod
    def _decision(
        *,
        context: TradingBotStrategyContext,
        config: TrendStrategyConfig,
        action: str,
        confidence: float,
        reason: str,
        fast_ema: float | None = None,
        slow_ema: float | None = None,
        momentum_percent: (
            float | None
        ) = None,
        ema_separation_percent: (
            float | None
        ) = None,
        trend: str = "WARMUP",
    ) -> TradingBotStrategyDecision:
        position = context.state.position
        return TradingBotStrategyDecision(
            action=action,
            confidence=confidence,
            reason=reason,
            reference_price=(
                context.ticker.last_price
            ),
            evaluated_at=(
                context.evaluated_at
            ),
            metadata={
                "strategy_type": "TREND",
                "direction": (
                    config.direction
                ),
                "trend": trend,
                "history_count": len(
                    context.market_history
                ),
                "fast_ema_period": (
                    config.fast_ema_period
                ),
                "slow_ema_period": (
                    config.slow_ema_period
                ),
                "momentum_lookback": (
                    config.momentum_lookback
                ),
                "fast_ema": fast_ema,
                "slow_ema": slow_ema,
                "momentum_percent": (
                    momentum_percent
                ),
                "ema_separation_percent": (
                    ema_separation_percent
                ),
                (
                    "minimum_momentum_"
                    "percent"
                ): (
                    config
                    .minimum_momentum_percent
                ),
                (
                    "minimum_ema_"
                    "separation_percent"
                ): (
                    config
                    .minimum_ema_separation_percent
                ),
                "spread_percent": (
                    context.ticker
                    .spread_percent
                ),
                "turnover_24h": (
                    context.ticker
                    .turnover_24h
                ),
                "position_side": (
                    position.side
                    if position is not None
                    else None
                ),
            },
        )
    async def evaluate(
        self,
        context: TradingBotStrategyContext,
    ) -> TradingBotStrategyDecision:
        config = (
            TrendStrategyConfig
            .model_validate(
                context.config
            )
        )
        ticker = context.ticker
        position = context.state.position
        if ticker.last_price <= 0:
            return self._decision(
                context=context,
                config=config,
                action="HOLD",
                confidence=0.0,
                reason=(
                    "Trend evaluation requires "
                    "a positive market price"
                ),
            )
        if (
            ticker.spread_percent
            > config.maximum_spread_percent
        ):
            return self._decision(
                context=context,
                config=config,
                action="HOLD",
                confidence=0.0,
                reason=(
                    "The market spread exceeds "
                    "the configured Trend limit"
                ),
            )
        if (
            ticker.turnover_24h
            < config.minimum_turnover_24h
        ):
            return self._decision(
                context=context,
                config=config,
                action="HOLD",
                confidence=0.0,
                reason=(
                    "The market turnover is below "
                    "the configured Trend minimum"
                ),
            )
        close_prices = [
            sample.close_price
            for sample
            in context.market_history
        ]
        fast_ema = (
            self.indicators
            .exponential_moving_average(
                close_prices,
                config.fast_ema_period,
            )
        )
        slow_ema = (
            self.indicators
            .exponential_moving_average(
                close_prices,
                config.slow_ema_period,
            )
        )
        momentum_percent = (
            self.indicators
            .percentage_change(
                close_prices,
                config.momentum_lookback,
            )
        )
        if (
            fast_ema is None
            or slow_ema is None
            or momentum_percent is None
        ):
            return self._decision(
                context=context,
                config=config,
                action="HOLD",
                confidence=0.0,
                reason=(
                    "Trend strategy is waiting "
                    "for sufficient market history"
                ),
            )
        ema_separation_percent = (
            (
                fast_ema
                - slow_ema
            )
            / slow_ema
            * 100
        )
        bullish = (
            ema_separation_percent
            >= (
                config
                .minimum_ema_separation_percent
            )
            and momentum_percent
            >= (
                config
                .minimum_momentum_percent
            )
        )
        bearish = (
            ema_separation_percent
            <= -(
                config
                .minimum_ema_separation_percent
            )
            and momentum_percent
            <= -(
                config
                .minimum_momentum_percent
            )
        )
        if bullish:
            trend = "BULLISH"
        elif bearish:
            trend = "BEARISH"
        else:
            trend = "NEUTRAL"
        confidence = self._confidence(
            ema_separation_percent=(
                ema_separation_percent
            ),
            momentum_percent=(
                momentum_percent
            ),
            scale_percent=(
                config
                .confidence_scale_percent
            ),
        )
        if position is not None:
            if (
                position.side == "LONG"
                and bearish
            ):
                return self._decision(
                    context=context,
                    config=config,
                    action="SELL",
                    confidence=confidence,
                    reason=(
                        "The trend reversed "
                        "against the open LONG "
                        "position"
                    ),
                    fast_ema=fast_ema,
                    slow_ema=slow_ema,
                    momentum_percent=(
                        momentum_percent
                    ),
                    ema_separation_percent=(
                        ema_separation_percent
                    ),
                    trend=trend,
                )
            if (
                position.side == "SHORT"
                and bullish
            ):
                return self._decision(
                    context=context,
                    config=config,
                    action="BUY",
                    confidence=confidence,
                    reason=(
                        "The trend reversed "
                        "against the open SHORT "
                        "position"
                    ),
                    fast_ema=fast_ema,
                    slow_ema=slow_ema,
                    momentum_percent=(
                        momentum_percent
                    ),
                    ema_separation_percent=(
                        ema_separation_percent
                    ),
                    trend=trend,
                )
            return self._decision(
                context=context,
                config=config,
                action="HOLD",
                confidence=confidence,
                reason=(
                    "The open position remains "
                    "aligned with the current "
                    "trend"
                ),
                fast_ema=fast_ema,
                slow_ema=slow_ema,
                momentum_percent=(
                    momentum_percent
                ),
                ema_separation_percent=(
                    ema_separation_percent
                ),
                trend=trend,
            )
        if (
            bullish
            and self._direction_allows(
                configured_direction=(
                    config.direction
                ),
                position_side="LONG",
            )
        ):
            return self._decision(
                context=context,
                config=config,
                action="BUY",
                confidence=confidence,
                reason=(
                    "Bullish EMA alignment and "
                    "momentum were confirmed"
                ),
                fast_ema=fast_ema,
                slow_ema=slow_ema,
                momentum_percent=(
                    momentum_percent
                ),
                ema_separation_percent=(
                    ema_separation_percent
                ),
                trend=trend,
            )
        if (
            bearish
            and self._direction_allows(
                configured_direction=(
                    config.direction
                ),
                position_side="SHORT",
            )
        ):
            return self._decision(
                context=context,
                config=config,
                action="SELL",
                confidence=confidence,
                reason=(
                    "Bearish EMA alignment and "
                    "momentum were confirmed"
                ),
                fast_ema=fast_ema,
                slow_ema=slow_ema,
                momentum_percent=(
                    momentum_percent
                ),
                ema_separation_percent=(
                    ema_separation_percent
                ),
                trend=trend,
            )
        return self._decision(
            context=context,
            config=config,
            action="HOLD",
            confidence=confidence,
            reason=(
                "No actionable Trend signal "
                "was confirmed"
            ),
            fast_ema=fast_ema,
            slow_ema=slow_ema,
            momentum_percent=(
                momentum_percent
            ),
            ema_separation_percent=(
                ema_separation_percent
            ),
            trend=trend,
        )
