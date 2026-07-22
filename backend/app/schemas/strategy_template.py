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
from app.schemas.trading_bot import (
    TradingBotCategory,
    TradingBotStrategyType,
    TradingBotTimeframe,
)
StrategyTemplateVisibility = Literal[
    "PRIVATE",
    "PUBLIC",
]
StrategyTemplateStatus = Literal[
    "DRAFT",
    "PUBLISHED",
    "ARCHIVED",
]
class StrategyTemplateConfiguration(
    BaseModel
):
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
    visibility: (
        StrategyTemplateVisibility
    ) = "PRIVATE"
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
    model_config = ConfigDict(
        extra="forbid",
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
class StrategyTemplateCreateRequest(
    StrategyTemplateConfiguration
):
    pass
class StrategyTemplateUpdateRequest(
    BaseModel
):
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
    visibility: (
        StrategyTemplateVisibility | None
    ) = None
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
    model_config = ConfigDict(
        extra="forbid",
    )
    @field_validator("name")
    @classmethod
    def normalize_name(
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
    def validate_update(
        self,
    ):
        if not self.model_fields_set:
            raise ValueError(
                "At least one strategy "
                "template field must be "
                "provided"
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
class StrategyTemplateResponse(
    StrategyTemplateConfiguration
):
    id: int
    user_id: int
    status: StrategyTemplateStatus
    version: int = Field(
        ge=1,
    )
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(
        from_attributes=True,
    )
StrategyTemplateAction = Literal[
    "PUBLISH",
    "UNPUBLISH",
    "ARCHIVE",
    "RESTORE",
]
class StrategyTemplateActionResult(
    BaseModel
):
    action: StrategyTemplateAction
    previous_status: (
        StrategyTemplateStatus
    )
    status: StrategyTemplateStatus
    changed: bool
    template: StrategyTemplateResponse
class StrategyTemplateBotCreateRequest(
    BaseModel
):
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
    model_config = ConfigDict(
        extra="forbid",
    )
    @field_validator("name")
    @classmethod
    def normalize_bot_name(
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
    def normalize_bot_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None
