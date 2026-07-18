from pydantic import BaseModel, Field
class OrderRiskContext(BaseModel):
    account_equity: float = Field(gt=0)
    requested_leverage: float = Field(
        default=1,
        gt=0,
    )
    estimated_entry_price: float | None = Field(
        default=None,
        gt=0,
    )
    stop_loss_price: float = Field(gt=0)
    take_profit_price: float = Field(gt=0)
    current_open_positions: int = Field(
        default=0,
        ge=0,
    )
    current_total_exposure_percent: float = Field(
        default=0,
        ge=0,
    )
    current_daily_loss_percent: float = Field(
        default=0,
        ge=0,
    )
    current_drawdown_percent: float = Field(
        default=0,
        ge=0,
    )
