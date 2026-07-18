from pydantic import BaseModel, Field, model_validator
class RiskConfiguration(BaseModel):
    max_risk_per_trade_percent: float = Field(
        default=1.0,
        gt=0,
        le=100,
    )
    max_daily_loss_percent: float = Field(
        default=5.0,
        gt=0,
        le=100,
    )
    max_drawdown_percent: float = Field(
        default=20.0,
        gt=0,
        le=100,
    )
    max_leverage: float = Field(
        default=10.0,
        gt=0,
    )
    max_open_positions: int = Field(
        default=5,
        ge=1,
        le=100,
    )
    max_total_exposure_percent: float = Field(
        default=100.0,
        gt=0,
        le=1000,
    )
    minimum_risk_reward_ratio: float = Field(
        default=1.5,
        gt=0,
    )
    trading_enabled: bool = True
    @model_validator(mode="after")
    def validate_risk_limits(self):
        if (
            self.max_risk_per_trade_percent
            > self.max_daily_loss_percent
        ):
            raise ValueError(
                "max_risk_per_trade_percent cannot exceed "
                "max_daily_loss_percent"
            )
        if (
            self.max_daily_loss_percent
            > self.max_drawdown_percent
        ):
            raise ValueError(
                "max_daily_loss_percent cannot exceed "
                "max_drawdown_percent"
            )
        return self
class RiskConfigurationUpdate(BaseModel):
    max_risk_per_trade_percent: float | None = Field(
        default=None,
        gt=0,
        le=100,
    )
    max_daily_loss_percent: float | None = Field(
        default=None,
        gt=0,
        le=100,
    )
    max_drawdown_percent: float | None = Field(
        default=None,
        gt=0,
        le=100,
    )
    max_leverage: float | None = Field(
        default=None,
        gt=0,
    )
    max_open_positions: int | None = Field(
        default=None,
        ge=1,
        le=100,
    )
    max_total_exposure_percent: float | None = Field(
        default=None,
        gt=0,
        le=1000,
    )
    minimum_risk_reward_ratio: float | None = Field(
        default=None,
        gt=0,
    )
    trading_enabled: bool | None = None
    @model_validator(mode="after")
    def require_update_value(self):
        if not self.model_fields_set:
            raise ValueError(
                "At least one risk configuration field "
                "must be provided"
            )
        return self
class RiskLimitCheck(BaseModel):
    rule: str
    passed: bool
    actual_value: float | int | bool | None = None
    limit_value: float | int | bool | None = None
    message: str
class RiskValidationResult(BaseModel):
    accepted: bool
    checks: list[RiskLimitCheck]
    rejection_reasons: list[str]
class PositionSizeRequest(BaseModel):
    account_equity: float = Field(gt=0)
    risk_percent: float = Field(gt=0, le=100)
    entry_price: float = Field(gt=0)
    stop_loss_price: float = Field(gt=0)
    quantity_step: float = Field(gt=0)
    minimum_quantity: float = Field(gt=0)
    maximum_quantity: float = Field(gt=0)
    minimum_notional: float = Field(default=0, ge=0)
    leverage: float = Field(default=1, gt=0)
    @model_validator(mode="after")
    def validate_position_size_inputs(self):
        if self.entry_price == self.stop_loss_price:
            raise ValueError(
                "entry_price and stop_loss_price cannot be equal"
            )
        if self.minimum_quantity > self.maximum_quantity:
            raise ValueError(
                "minimum_quantity cannot exceed maximum_quantity"
            )
        return self
class PositionSizeResult(BaseModel):
    valid: bool
    account_equity: float
    requested_risk_percent: float
    requested_risk_amount: float
    entry_price: float
    stop_loss_price: float
    stop_distance: float
    raw_quantity: float
    rounded_quantity: float
    position_notional: float
    required_margin: float
    actual_risk_amount: float
    actual_risk_percent: float
    quantity_step: float
    minimum_quantity: float
    maximum_quantity: float
    minimum_notional: float
    leverage: float
    capped_by_maximum_quantity: bool = False
    rejection_reasons: list[str] = []
