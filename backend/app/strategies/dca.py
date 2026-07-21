from typing import (
    Any,
)
from app.schemas.trading_bot_strategy import (
    DcaStrategyConfig,
    TradingBotStrategyContext,
    TradingBotStrategyDecision,
)
class DcaTradingStrategy:
    strategy_type = "DCA"
    def validate_config(
        self,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        validated = (
            DcaStrategyConfig
            .model_validate(config)
        )
        return validated.model_dump()
    @staticmethod
    def _confidence(
        *,
        progress_percent: float,
        scale_percent: float,
    ) -> float:
        return min(
            1.0,
            max(
                0.0,
                abs(progress_percent)
                / scale_percent,
            ),
        )
    @staticmethod
    def _position_profit_percent(
        *,
        side: str,
        current_price: float,
        average_entry_price: float,
    ) -> float:
        if side == "LONG":
            return (
                current_price
                - average_entry_price
            ) / average_entry_price * 100
        return (
            average_entry_price
            - current_price
        ) / average_entry_price * 100
    @staticmethod
    def _entry_spacing_progress(
        *,
        side: str,
        current_price: float,
        last_entry_price: float,
    ) -> float:
        if side == "LONG":
            return (
                last_entry_price
                - current_price
            ) / last_entry_price * 100
        return (
            current_price
            - last_entry_price
        ) / last_entry_price * 100
    @staticmethod
    def _initial_threshold_reached(
        *,
        direction: str,
        change_percent_24h: float,
        threshold: float | None,
    ) -> bool:
        if threshold is None:
            return True
        if direction == "LONG":
            return (
                change_percent_24h
                <= threshold
            )
        return (
            change_percent_24h
            >= threshold
        )
    @staticmethod
    def _decision(
        *,
        context: TradingBotStrategyContext,
        config: DcaStrategyConfig,
        action: str,
        confidence: float,
        reason: str,
        spacing_progress: float = 0.0,
        profit_percent: float = 0.0,
    ) -> TradingBotStrategyDecision:
        ticker = context.ticker
        state = context.state
        position = state.position
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
                "strategy_type": "DCA",
                "symbol": ticker.symbol,
                "direction": (
                    config.direction
                ),
                "current_price": (
                    ticker.last_price
                ),
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
                "entry_spacing_percent": (
                    config
                    .entry_spacing_percent
                ),
                "spacing_progress_percent": (
                    spacing_progress
                ),
                "maximum_entries": (
                    config.maximum_entries
                ),
                "take_profit_percent": (
                    config.take_profit_percent
                ),
                "position_profit_percent": (
                    profit_percent
                ),
                "initial_entry_change_percent_24h": (
                    config
                    .initial_entry_change_percent_24h
                ),
                "position_side": (
                    position.side
                    if position is not None
                    else None
                ),
                "entry_count": (
                    position.entry_count
                    if position is not None
                    else 0
                ),
                "average_entry_price": (
                    position.average_entry_price
                    if position is not None
                    else None
                ),
                "last_entry_price": (
                    position.last_entry_price
                    if position is not None
                    else None
                ),
            },
        )
    async def evaluate(
        self,
        context: TradingBotStrategyContext,
    ) -> TradingBotStrategyDecision:
        config = DcaStrategyConfig.model_validate(
            context.config
        )
        ticker = context.ticker
        state = context.state
        position = state.position
        if ticker.last_price <= 0:
            return self._decision(
                context=context,
                config=config,
                action="HOLD",
                confidence=0.0,
                reason=(
                    "DCA evaluation requires "
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
                    "the configured DCA limit"
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
                    "the configured DCA minimum"
                ),
            )
        entry_action = (
            "BUY"
            if config.direction == "LONG"
            else "SELL"
        )
        exit_action = (
            "SELL"
            if config.direction == "LONG"
            else "BUY"
        )
        if position is None:
            threshold_reached = (
                self._initial_threshold_reached(
                    direction=config.direction,
                    change_percent_24h=(
                        ticker
                        .price_change_percent_24h
                    ),
                    threshold=(
                        config
                        .initial_entry_change_percent_24h
                    ),
                )
            )
            if not threshold_reached:
                return self._decision(
                    context=context,
                    config=config,
                    action="HOLD",
                    confidence=0.0,
                    reason=(
                        "The configured initial "
                        "DCA entry threshold has "
                        "not been reached"
                    ),
                )
            confidence = self._confidence(
                progress_percent=(
                    ticker
                    .price_change_percent_24h
                ),
                scale_percent=(
                    config
                    .confidence_scale_percent
                ),
            )
            if (
                config
                .initial_entry_change_percent_24h
                is None
                and confidence == 0
            ):
                confidence = 0.5
            return self._decision(
                context=context,
                config=config,
                action=entry_action,
                confidence=confidence,
                reason=(
                    "The initial DCA entry "
                    "condition was reached"
                ),
            )
        if position.side != config.direction:
            return self._decision(
                context=context,
                config=config,
                action="HOLD",
                confidence=0.0,
                reason=(
                    "The open position direction "
                    "does not match the configured "
                    "DCA direction"
                ),
            )
        profit_percent = (
            self._position_profit_percent(
                side=position.side,
                current_price=(
                    ticker.last_price
                ),
                average_entry_price=(
                    position
                    .average_entry_price
                ),
            )
        )
        if (
            profit_percent
            >= config.take_profit_percent
        ):
            return self._decision(
                context=context,
                config=config,
                action=exit_action,
                confidence=self._confidence(
                    progress_percent=(
                        profit_percent
                    ),
                    scale_percent=(
                        config
                        .confidence_scale_percent
                    ),
                ),
                reason=(
                    "The DCA position reached "
                    "the configured take-profit "
                    "threshold"
                ),
                profit_percent=(
                    profit_percent
                ),
            )
        if (
            position.entry_count
            >= config.maximum_entries
        ):
            return self._decision(
                context=context,
                config=config,
                action="HOLD",
                confidence=0.0,
                reason=(
                    "The DCA position reached "
                    "the maximum entry count"
                ),
                profit_percent=(
                    profit_percent
                ),
            )
        spacing_progress = (
            self._entry_spacing_progress(
                side=position.side,
                current_price=(
                    ticker.last_price
                ),
                last_entry_price=(
                    position.last_entry_price
                ),
            )
        )
        if (
            spacing_progress
            >= config.entry_spacing_percent
        ):
            return self._decision(
                context=context,
                config=config,
                action=entry_action,
                confidence=self._confidence(
                    progress_percent=(
                        spacing_progress
                    ),
                    scale_percent=(
                        config
                        .confidence_scale_percent
                    ),
                ),
                reason=(
                    "The market reached the next "
                    "configured DCA entry level"
                ),
                spacing_progress=(
                    spacing_progress
                ),
                profit_percent=(
                    profit_percent
                ),
            )
        return self._decision(
            context=context,
            config=config,
            action="HOLD",
            confidence=0.0,
            reason=(
                "No DCA entry or exit condition "
                "was reached"
            ),
            spacing_progress=(
                spacing_progress
            ),
            profit_percent=(
                profit_percent
            ),
        )
