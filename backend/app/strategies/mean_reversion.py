from typing import (
    Any,
)
from app.schemas.trading_bot_strategy import (
    MeanReversionStrategyConfig,
    TradingBotStrategyContext,
    TradingBotStrategyDecision,
)
from app.services.trading_bot_indicator_service import (
    TradingBotIndicatorService,
)
class MeanReversionTradingStrategy:
    strategy_type = "MEAN_REVERSION"
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
            MeanReversionStrategyConfig
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
        z_score: float,
        rsi: float,
        scale: float,
    ) -> float:
        z_strength = abs(z_score)
        rsi_strength = (
            abs(
                rsi - 50.0
            )
            / 50.0
        )
        strength = max(
            z_strength,
            rsi_strength,
        )
        return min(
            1.0,
            max(
                0.0,
                strength / scale,
            ),
        )
    @staticmethod
    def _decision(
        *,
        context: TradingBotStrategyContext,
        config: (
            MeanReversionStrategyConfig
        ),
        action: str,
        confidence: float,
        reason: str,
        mean_price: float | None = None,
        standard_deviation: (
            float | None
        ) = None,
        z_score: float | None = None,
        rsi: float | None = None,
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
                "strategy_type": (
                    "MEAN_REVERSION"
                ),
                "direction": (
                    config.direction
                ),
                "signal": signal,
                "history_count": len(
                    context.market_history
                ),
                "lookback_period": (
                    config.lookback_period
                ),
                "rsi_period": (
                    config.rsi_period
                ),
                "entry_z_score": (
                    config.entry_z_score
                ),
                "exit_z_score": (
                    config.exit_z_score
                ),
                "oversold_rsi": (
                    config.oversold_rsi
                ),
                "overbought_rsi": (
                    config.overbought_rsi
                ),
                "mean_price": mean_price,
                "standard_deviation": (
                    standard_deviation
                ),
                "z_score": z_score,
                "rsi": rsi,
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
            MeanReversionStrategyConfig
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
                    "Mean-Reversion evaluation "
                    "requires a positive market "
                    "price"
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
                    "the configured "
                    "Mean-Reversion limit"
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
                    "the configured "
                    "Mean-Reversion minimum"
                ),
            )
        close_prices = [
            sample.close_price
            for sample
            in context.market_history
        ]
        mean_price = (
            self.indicators
            .simple_moving_average(
                close_prices,
                config.lookback_period,
            )
        )
        standard_deviation = (
            self.indicators
            .standard_deviation(
                close_prices,
                config.lookback_period,
            )
        )
        z_score = (
            self.indicators
            .z_score(
                close_prices,
                config.lookback_period,
            )
        )
        rsi = (
            self.indicators
            .relative_strength_index(
                close_prices,
                config.rsi_period,
            )
        )
        if (
            mean_price is None
            or standard_deviation is None
            or z_score is None
            or rsi is None
        ):
            return self._decision(
                context=context,
                config=config,
                action="HOLD",
                confidence=0.0,
                reason=(
                    "Mean-Reversion strategy is "
                    "waiting for sufficient "
                    "market history"
                ),
            )
        long_signal = (
            z_score
            <= -config.entry_z_score
            and rsi
            <= config.oversold_rsi
        )
        short_signal = (
            z_score
            >= config.entry_z_score
            and rsi
            >= config.overbought_rsi
        )
        confidence = self._confidence(
            z_score=z_score,
            rsi=rsi,
            scale=config.confidence_scale,
        )
        if long_signal:
            signal = "OVERSOLD"
        elif short_signal:
            signal = "OVERBOUGHT"
        else:
            signal = "NEUTRAL"
        if position is not None:
            if (
                position.side == "LONG"
                and z_score
                >= -config.exit_z_score
            ):
                return self._decision(
                    context=context,
                    config=config,
                    action="SELL",
                    confidence=confidence,
                    reason=(
                        "The LONG position reverted "
                        "toward the statistical mean"
                    ),
                    mean_price=mean_price,
                    standard_deviation=(
                        standard_deviation
                    ),
                    z_score=z_score,
                    rsi=rsi,
                    signal=signal,
                )
            if (
                position.side == "SHORT"
                and z_score
                <= config.exit_z_score
            ):
                return self._decision(
                    context=context,
                    config=config,
                    action="BUY",
                    confidence=confidence,
                    reason=(
                        "The SHORT position reverted "
                        "toward the statistical mean"
                    ),
                    mean_price=mean_price,
                    standard_deviation=(
                        standard_deviation
                    ),
                    z_score=z_score,
                    rsi=rsi,
                    signal=signal,
                )
            return self._decision(
                context=context,
                config=config,
                action="HOLD",
                confidence=confidence,
                reason=(
                    "The open position has not "
                    "reached its Mean-Reversion "
                    "exit threshold"
                ),
                mean_price=mean_price,
                standard_deviation=(
                    standard_deviation
                ),
                z_score=z_score,
                rsi=rsi,
                signal=signal,
            )
        if (
            long_signal
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
                    "Price is statistically "
                    "oversold below its mean"
                ),
                mean_price=mean_price,
                standard_deviation=(
                    standard_deviation
                ),
                z_score=z_score,
                rsi=rsi,
                signal=signal,
            )
        if (
            short_signal
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
                    "Price is statistically "
                    "overbought above its mean"
                ),
                mean_price=mean_price,
                standard_deviation=(
                    standard_deviation
                ),
                z_score=z_score,
                rsi=rsi,
                signal=signal,
            )
        return self._decision(
            context=context,
            config=config,
            action="HOLD",
            confidence=confidence,
            reason=(
                "No actionable Mean-Reversion "
                "signal was confirmed"
            ),
            mean_price=mean_price,
            standard_deviation=(
                standard_deviation
            ),
            z_score=z_score,
            rsi=rsi,
            signal=signal,
        )
