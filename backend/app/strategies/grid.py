from typing import (
    Any,
)
from app.schemas.trading_bot_strategy import (
    GridStrategyConfig,
    TradingBotStrategyContext,
    TradingBotStrategyDecision,
)
class GridTradingStrategy:
    strategy_type = "GRID"
    def validate_config(
        self,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        validated = (
            GridStrategyConfig
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
    def _grid_spacing(
        config: GridStrategyConfig,
    ) -> float:
        return (
            config.upper_price
            - config.lower_price
        ) / (
            config.grid_levels
            - 1
        )
    @staticmethod
    def _price_in_range(
        *,
        price: float,
        config: GridStrategyConfig,
    ) -> bool:
        return (
            config.lower_price
            <= price
            <= config.upper_price
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
    def _grid_index(
        *,
        price: float,
        config: GridStrategyConfig,
        spacing: float,
    ) -> int:
        raw_index = round(
            (
                price
                - config.lower_price
            )
            / spacing
        )
        return max(
            0,
            min(
                config.grid_levels - 1,
                raw_index,
            ),
        )
    @staticmethod
    def _next_entry_price(
        *,
        side: str,
        last_entry_price: float,
        spacing: float,
    ) -> float:
        if side == "LONG":
            return (
                last_entry_price
                - spacing
            )
        return (
            last_entry_price
            + spacing
        )
    @staticmethod
    def _entry_reached(
        *,
        side: str,
        current_price: float,
        next_entry_price: float,
    ) -> bool:
        if side == "LONG":
            return (
                current_price
                <= next_entry_price
            )
        return (
            current_price
            >= next_entry_price
        )
    @staticmethod
    def _decision(
        *,
        context: TradingBotStrategyContext,
        config: GridStrategyConfig,
        action: str,
        confidence: float,
        reason: str,
        grid_spacing: float,
        next_entry_price: (
            float | None
        ) = None,
        profit_percent: float = 0.0,
    ) -> TradingBotStrategyDecision:
        ticker = context.ticker
        position = context.state.position
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
                "strategy_type": "GRID",
                "symbol": ticker.symbol,
                "direction": (
                    config.direction
                ),
                "current_price": (
                    ticker.last_price
                ),
                "lower_price": (
                    config.lower_price
                ),
                "upper_price": (
                    config.upper_price
                ),
                "grid_levels": (
                    config.grid_levels
                ),
                "grid_spacing_usd": (
                    grid_spacing
                ),
                "current_grid_index": (
                    GridTradingStrategy
                    ._grid_index(
                        price=(
                            ticker.last_price
                        ),
                        config=config,
                        spacing=grid_spacing,
                    )
                ),
                "next_entry_price": (
                    next_entry_price
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
                "spread_percent": (
                    ticker.spread_percent
                ),
                "turnover_24h": (
                    ticker.turnover_24h
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
        config = (
            GridStrategyConfig
            .model_validate(
                context.config
            )
        )
        ticker = context.ticker
        position = context.state.position
        spacing = self._grid_spacing(
            config
        )
        if ticker.last_price <= 0:
            return self._decision(
                context=context,
                config=config,
                action="HOLD",
                confidence=0.0,
                reason=(
                    "Grid evaluation requires "
                    "a positive market price"
                ),
                grid_spacing=spacing,
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
                    "the configured Grid limit"
                ),
                grid_spacing=spacing,
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
                    "the configured Grid minimum"
                ),
                grid_spacing=spacing,
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
            if not self._price_in_range(
                price=ticker.last_price,
                config=config,
            ):
                return self._decision(
                    context=context,
                    config=config,
                    action="HOLD",
                    confidence=0.0,
                    reason=(
                        "The market price is "
                        "outside the configured "
                        "Grid range"
                    ),
                    grid_spacing=spacing,
                )
            range_size = (
                config.upper_price
                - config.lower_price
            )
            if config.direction == "LONG":
                progress = (
                    config.upper_price
                    - ticker.last_price
                ) / range_size * 100
            else:
                progress = (
                    ticker.last_price
                    - config.lower_price
                ) / range_size * 100
            confidence = self._confidence(
                progress_percent=progress,
                scale_percent=(
                    config
                    .confidence_scale_percent
                ),
            )
            if confidence == 0:
                confidence = 0.5
            return self._decision(
                context=context,
                config=config,
                action=entry_action,
                confidence=confidence,
                reason=(
                    "The market price entered "
                    "the configured Grid range"
                ),
                grid_spacing=spacing,
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
                    "Grid direction"
                ),
                grid_spacing=spacing,
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
                    "The Grid position reached "
                    "the configured take-profit "
                    "threshold"
                ),
                grid_spacing=spacing,
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
                    "The Grid position reached "
                    "the maximum entry count"
                ),
                grid_spacing=spacing,
                profit_percent=(
                    profit_percent
                ),
            )
        next_entry_price = (
            self._next_entry_price(
                side=position.side,
                last_entry_price=(
                    position.last_entry_price
                ),
                spacing=spacing,
            )
        )
        if not self._price_in_range(
            price=ticker.last_price,
            config=config,
        ):
            return self._decision(
                context=context,
                config=config,
                action="HOLD",
                confidence=0.0,
                reason=(
                    "The market price is "
                    "outside the configured "
                    "Grid range"
                ),
                grid_spacing=spacing,
                next_entry_price=(
                    next_entry_price
                ),
                profit_percent=(
                    profit_percent
                ),
            )
        if self._entry_reached(
            side=position.side,
            current_price=(
                ticker.last_price
            ),
            next_entry_price=(
                next_entry_price
            ),
        ):
            spacing_progress = (
                abs(
                    ticker.last_price
                    - position.last_entry_price
                )
                / position.last_entry_price
                * 100
            )
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
                    "configured Grid entry level"
                ),
                grid_spacing=spacing,
                next_entry_price=(
                    next_entry_price
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
                "No Grid entry or exit condition "
                "was reached"
            ),
            grid_spacing=spacing,
            next_entry_price=(
                next_entry_price
            ),
            profit_percent=(
                profit_percent
            ),
        )
