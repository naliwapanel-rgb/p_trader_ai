from datetime import (
    datetime,
)
from typing import (
    Any,
    Literal,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
TradingBotStrategyType = Literal[
    "RULE_BASED",
    "MOMENTUM",
    "TREND",
    "MEAN_REVERSION",
    "SCALPING",
    "GRID",
    "DCA",
    "ARBITRAGE",
    "CUSTOM",
]
TradingBotStatus = Literal[
    "DRAFT",
    "STOPPED",
    "STARTING",
    "RUNNING",
    "PAUSED",
    "ERROR",
    "ARCHIVED",
]
TradingBotCategory = Literal[
    "spot",
    "linear",
    "inverse",
]
TradingBotTimeframe = Literal[
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "6h",
    "12h",
    "1d",
]
class TradingBotConfiguration(BaseModel):
    exchange_account_id: (
        int | None
    ) = Field(
        default=None,
        gt=0,
    )
    name: str = Field(
        min_length=2,
        max_length=150,
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
    )
    strategy_type: (
        TradingBotStrategyType
    ) = "RULE_BASED"
    symbol: str = Field(
        min_length=2,
        max_length=30,
    )
    category: TradingBotCategory = (
        "linear"
    )
    timeframe: TradingBotTimeframe = (
        "5m"
    )
    paper_trading: bool = True
    dry_run: bool = True
    risk_per_trade_percent: float = (
        Field(
            default=1.0,
            gt=0,
            le=100,
        )
    )
    max_position_value_usd: float = (
        Field(
            default=25.0,
            gt=0,
        )
    )
    max_daily_loss_percent: float = (
        Field(
            default=3.0,
            gt=0,
            le=100,
        )
    )
    max_drawdown_percent: float = Field(
        default=10.0,
        gt=0,
        le=100,
    )
    stop_loss_percent: float | None = (
        Field(
            default=None,
            gt=0,
            le=100,
        )
    )
    take_profit_percent: (
        float | None
    ) = Field(
        default=None,
        gt=0,
        le=1000,
    )
    strategy_config: dict[
        str,
        Any,
    ] = Field(
        default_factory=dict
    )
    @field_validator("name")
    @classmethod
    def normalize_name(
        cls,
        value: str,
    ) -> str:
        normalized = " ".join(
            value.split()
        )
        if not normalized:
            raise ValueError(
                "name cannot be blank"
            )
        return normalized
    @field_validator("description")
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None
    @field_validator("symbol")
    @classmethod
    def normalize_symbol(
        cls,
        value: str,
    ) -> str:
        normalized = (
            value.strip().upper()
        )
        if not normalized:
            raise ValueError(
                "symbol cannot be blank"
            )
        return normalized
    @model_validator(mode="after")
    def validate_safety_and_risk(
        self,
    ):
        if (
            not self.paper_trading
            and not self.dry_run
        ):
            raise ValueError(
                "At least paper_trading or "
                "dry_run must remain enabled"
            )
        if (
            self.risk_per_trade_percent
            > self.max_daily_loss_percent
        ):
            raise ValueError(
                "risk_per_trade_percent "
                "cannot exceed "
                "max_daily_loss_percent"
            )
        if (
            self.max_daily_loss_percent
            > self.max_drawdown_percent
        ):
            raise ValueError(
                "max_daily_loss_percent "
                "cannot exceed "
                "max_drawdown_percent"
            )
        return self
class TradingBotCreateRequest(
    TradingBotConfiguration
):
    pass
class TradingBotUpdateRequest(
    BaseModel
):
    exchange_account_id: (
        int | None
    ) = Field(
        default=None,
        gt=0,
    )
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
    )
    strategy_type: (
        TradingBotStrategyType | None
    ) = None
    symbol: str | None = Field(
        default=None,
        min_length=2,
        max_length=30,
    )
    category: (
        TradingBotCategory | None
    ) = None
    timeframe: (
        TradingBotTimeframe | None
    ) = None
    status: TradingBotStatus | None = (
        None
    )
    paper_trading: bool | None = None
    dry_run: bool | None = None
    risk_per_trade_percent: (
        float | None
    ) = Field(
        default=None,
        gt=0,
        le=100,
    )
    max_position_value_usd: (
        float | None
    ) = Field(
        default=None,
        gt=0,
    )
    max_daily_loss_percent: (
        float | None
    ) = Field(
        default=None,
        gt=0,
        le=100,
    )
    max_drawdown_percent: (
        float | None
    ) = Field(
        default=None,
        gt=0,
        le=100,
    )
    stop_loss_percent: (
        float | None
    ) = Field(
        default=None,
        gt=0,
        le=100,
    )
    take_profit_percent: (
        float | None
    ) = Field(
        default=None,
        gt=0,
        le=1000,
    )
    strategy_config: (
        dict[str, Any] | None
    ) = None
    last_error: str | None = Field(
        default=None,
        max_length=4000,
    )
    started_at: datetime | None = None
    stopped_at: datetime | None = None
    last_run_at: datetime | None = None
    @field_validator("name")
    @classmethod
    def normalize_update_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        normalized = " ".join(
            value.split()
        )
        if not normalized:
            raise ValueError(
                "name cannot be blank"
            )
        return normalized
    @field_validator("description")
    @classmethod
    def normalize_update_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None
    @field_validator("symbol")
    @classmethod
    def normalize_update_symbol(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        normalized = (
            value.strip().upper()
        )
        if not normalized:
            raise ValueError(
                "symbol cannot be blank"
            )
        return normalized
    @model_validator(mode="after")
    def require_update_value(self):
        if not self.model_fields_set:
            raise ValueError(
                "At least one trading bot "
                "field must be provided"
            )
        if (
            self.paper_trading is False
            and self.dry_run is False
        ):
            raise ValueError(
                "At least paper_trading or "
                "dry_run must remain enabled"
            )
        return self
class TradingBotResponse(
    TradingBotConfiguration
):
    id: int
    user_id: int
    status: TradingBotStatus
    last_error: str | None = None
    started_at: datetime | None = None
    stopped_at: datetime | None = None
    last_run_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(
        from_attributes=True
    )
TradingBotLifecycleAction = Literal[
    "PREPARE",
    "START",
    "PAUSE",
    "RESUME",
    "STOP",
]
class TradingBotLifecycleActionResult(
    BaseModel
):
    action: TradingBotLifecycleAction
    previous_status: TradingBotStatus
    status: TradingBotStatus
    changed: bool
    bot: TradingBotResponse
