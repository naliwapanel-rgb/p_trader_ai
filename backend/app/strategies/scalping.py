from typing import (
    Any,
)
from app.schemas.trading_bot_strategy import (
    ScalpingStrategyConfig,
    TradingBotStrategyContext,
    TradingBotStrategyDecision,
)
from app.services.trading_bot_indicator_service import (
    TradingBotIndicatorService,
)
class ScalpingTradingStrategy:
    strategy_type = "SCALPING"
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
            ScalpingStrategyConfig
            .model_validate(config)
        )
        return validated.model_dump()
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
    def _confidence(
        *,
        ema_separation_percent: float,
        momentum_percent: float,
        atr_percent: float,
        scale_percent: float,
    ) -> float:
        strength = max(
            abs(
                ema_separation_percent
            ),
            abs(momentum_percent),
            abs(atr_percent),
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
    def _decision(
        *,
        context: TradingBotStrategyContext,
        config: ScalpingStrategyConfig,
        action: str,
        confidence: float,
        reason: str,
        fast_ema: float | None = None,
        slow_ema: float | None = None,
        momentum_percent: (
            float | None
        ) = None,
        rsi: float | None = None,
        atr: float | None = None,
        atr_percent: float | None = None,
        ema_separation_percent: (
            float | None
        ) = None,
        signal: str = "WARMUP",
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
                "strategy_type": "SCALPING",
                "direction": (
                    config.direction
                ),
                "signal": signal,
                "history_count": len(
                    context.market_history
                ),
                "fast_ema_period": (
                    config.fast_ema_period
                ),
                "slow_ema_period": (
                    config.slow_ema_period
                ),
                "rsi_period": (
                    config.rsi_period
                ),
                "atr_period": (
                    config.atr_period
                ),
                "momentum_lookback": (
                    config.momentum_lookback
                ),
                "fast_ema": fast_ema,
                "slow_ema": slow_ema,
                "ema_separation_percent": (
                    ema_separation_percent
                ),
                "momentum_percent": (
                    momentum_percent
                ),
                "rsi": rsi,
                "atr": atr,
                "atr_percent": atr_percent,
                (
                    "minimum_momentum_"
                    "percent"
                ): (
                    config
                    .minimum_momentum_percent
                ),
                "minimum_atr_percent": (
                    config.minimum_atr_percent
                ),
                "maximum_atr_percent": (
                    config.maximum_atr_percent
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
            ScalpingStrategyConfig
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
                    "Scalping evaluation requires "
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
                    "the configured Scalping limit"
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
                    "the configured Scalping "
                    "minimum"
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
        rsi = (
            self.indicators
            .relative_strength_index(
                close_prices,
                config.rsi_period,
            )
        )
        atr = (
            self.indicators
            .average_true_range(
                context.market_history,
                config.atr_period,
            )
        )
        if (
            fast_ema is None
            or slow_ema is None
            or momentum_percent is None
            or rsi is None
            or atr is None
        ):
            return self._decision(
                context=context,
                config=config,
                action="HOLD",
                confidence=0.0,
                reason=(
                    "Scalping strategy is waiting "
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
        atr_percent = (
            atr
            / ticker.last_price
            * 100
        )
        volatility_allowed = (
            config.minimum_atr_percent
            <= atr_percent
            <= config.maximum_atr_percent
        )
        bullish = (
            fast_ema > slow_ema
            and momentum_percent
            >= config.minimum_momentum_percent
            and config.long_rsi_minimum
            <= rsi
            <= config.long_rsi_maximum
            and volatility_allowed
        )
        bearish = (
            fast_ema < slow_ema
            and momentum_percent
            <= -config.minimum_momentum_percent
            and config.short_rsi_minimum
            <= rsi
            <= config.short_rsi_maximum
            and volatility_allowed
        )
        if bullish:
            signal = "BULLISH_SCALP"
        elif bearish:
            signal = "BEARISH_SCALP"
        elif not volatility_allowed:
            signal = "VOLATILITY_FILTERED"
        else:
            signal = "NEUTRAL"
        confidence = self._confidence(
            ema_separation_percent=(
                ema_separation_percent
            ),
            momentum_percent=(
                momentum_percent
            ),
            atr_percent=atr_percent,
            scale_percent=(
                config
                .confidence_scale_percent
            ),
        )
        if position is not None:
            if position.side == "LONG":
                should_exit = (
                    bearish
                    or fast_ema <= slow_ema
                    or momentum_percent
                    <= -(
                        config
                        .exit_momentum_percent
                    )
                )
                if should_exit:
                    return self._decision(
                        context=context,
                        config=config,
                        action="SELL",
                        confidence=confidence,
                        reason=(
                            "Short-term conditions "
                            "reversed against the "
                            "open LONG scalp"
                        ),
                        fast_ema=fast_ema,
                        slow_ema=slow_ema,
                        momentum_percent=(
                            momentum_percent
                        ),
                        rsi=rsi,
                        atr=atr,
                        atr_percent=(
                            atr_percent
                        ),
                        ema_separation_percent=(
                            ema_separation_percent
                        ),
                        signal=signal,
                    )
            if position.side == "SHORT":
                should_exit = (
                    bullish
                    or fast_ema >= slow_ema
                    or momentum_percent
                    >= (
                        config
                        .exit_momentum_percent
                    )
                )
                if should_exit:
                    return self._decision(
                        context=context,
                        config=config,
                        action="BUY",
                        confidence=confidence,
                        reason=(
                            "Short-term conditions "
                            "reversed against the "
                            "open SHORT scalp"
                        ),
                        fast_ema=fast_ema,
                        slow_ema=slow_ema,
                        momentum_percent=(
                            momentum_percent
                        ),
                        rsi=rsi,
                        atr=atr,
                        atr_percent=(
                            atr_percent
                        ),
                        ema_separation_percent=(
                            ema_separation_percent
                        ),
                        signal=signal,
                    )
            return self._decision(
                context=context,
                config=config,
                action="HOLD",
                confidence=confidence,
                reason=(
                    "The open scalp remains "
                    "aligned with short-term "
                    "market conditions"
                ),
                fast_ema=fast_ema,
                slow_ema=slow_ema,
                momentum_percent=(
                    momentum_percent
                ),
                rsi=rsi,
                atr=atr,
                atr_percent=atr_percent,
                ema_separation_percent=(
                    ema_separation_percent
                ),
                signal=signal,
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
                    "Bullish short-term EMA, RSI, "
                    "momentum and volatility "
                    "conditions were confirmed"
                ),
                fast_ema=fast_ema,
                slow_ema=slow_ema,
                momentum_percent=(
                    momentum_percent
                ),
                rsi=rsi,
                atr=atr,
                atr_percent=atr_percent,
                ema_separation_percent=(
                    ema_separation_percent
                ),
                signal=signal,
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
                    "Bearish short-term EMA, RSI, "
                    "momentum and volatility "
                    "conditions were confirmed"
                ),
                fast_ema=fast_ema,
                slow_ema=slow_ema,
                momentum_percent=(
                    momentum_percent
                ),
                rsi=rsi,
                atr=atr,
                atr_percent=atr_percent,
                ema_separation_percent=(
                    ema_separation_percent
                ),
                signal=signal,
            )
        return self._decision(
            context=context,
            config=config,
            action="HOLD",
            confidence=confidence,
            reason=(
                "No actionable Scalping signal "
                "was confirmed"
            ),
            fast_ema=fast_ema,
            slow_ema=slow_ema,
            momentum_percent=(
                momentum_percent
            ),
            rsi=rsi,
            atr=atr,
            atr_percent=atr_percent,
            ema_separation_percent=(
                ema_separation_percent
            ),
            signal=signal,
        )
