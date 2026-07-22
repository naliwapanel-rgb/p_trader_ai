from collections.abc import (
    Iterable,
)
from app.strategies.base import (
    TradingBotStrategy,
)
from app.strategies.dca import (
    DcaTradingStrategy,
)
from app.strategies.grid import (
    GridTradingStrategy,
)
from app.strategies.trend import (
    TrendTradingStrategy,
)
from app.strategies.mean_reversion import (
    MeanReversionTradingStrategy,
)
from app.strategies.scalping import (
    ScalpingTradingStrategy,
)
from app.strategies.rule_based import (
    RuleBasedTradingStrategy,
)
class TradingBotStrategyRegistry:
    def __init__(
        self,
        strategies: (
            Iterable[
                TradingBotStrategy
            ]
            | None
        ) = None,
    ):
        self._strategies: dict[
            str,
            TradingBotStrategy,
        ] = {}
        for strategy in strategies or []:
            self.register(strategy)
    @staticmethod
    def _normalize(
        strategy_type: str,
    ) -> str:
        normalized = (
            strategy_type.strip().upper()
        )
        if not normalized:
            raise ValueError(
                "strategy_type cannot "
                "be blank"
            )
        return normalized
    def register(
        self,
        strategy: TradingBotStrategy,
    ) -> None:
        strategy_type = self._normalize(
            strategy.strategy_type
        )
        if strategy_type in self._strategies:
            raise ValueError(
                "A trading bot strategy is "
                "already registered for "
                f"{strategy_type}"
            )
        self._strategies[
            strategy_type
        ] = strategy
    def get(
        self,
        strategy_type: str,
    ) -> TradingBotStrategy:
        normalized = self._normalize(
            strategy_type
        )
        strategy = self._strategies.get(
            normalized
        )
        if strategy is None:
            raise ValueError(
                "Unsupported trading bot "
                "strategy type: "
                f"{normalized}"
            )
        return strategy
    def list_types(self) -> list[str]:
        return sorted(self._strategies)
    @classmethod
    def default(
        cls,
    ) -> "TradingBotStrategyRegistry":
        return cls(
            strategies=[
                RuleBasedTradingStrategy(),
                DcaTradingStrategy(),
                GridTradingStrategy(),
                TrendTradingStrategy(),
                MeanReversionTradingStrategy(),
                ScalpingTradingStrategy(),
            ]
        )
