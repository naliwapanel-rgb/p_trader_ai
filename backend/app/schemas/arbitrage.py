from decimal import Decimal
from typing import Literal
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)
ArbitrageOpportunityType = Literal[
    "CROSS_EXCHANGE",
    "TRIANGULAR",
    "CUSTOM",
]
ArbitrageSide = Literal[
    "BUY",
    "SELL",
]
class ArbitrageLegRequest(BaseModel):
    exchange: str = Field(
        min_length=2,
        max_length=50,
    )
    symbol: str = Field(
        min_length=3,
        max_length=40,
    )
    base_asset: str = Field(
        min_length=1,
        max_length=20,
    )
    quote_asset: str = Field(
        min_length=1,
        max_length=20,
    )
    side: ArbitrageSide
    price: Decimal = Field(
        gt=0,
    )
    fee_rate_percent: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        lt=Decimal("100"),
    )
    slippage_percent: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        lt=Decimal("100"),
    )
    fixed_cost: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )
    @field_validator(
        "exchange",
        "symbol",
        "base_asset",
        "quote_asset",
    )
    @classmethod
    def normalize_identifier(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError(
                "identifier cannot be blank"
            )
        return normalized
    @model_validator(mode="after")
    def validate_assets(self):
        if self.base_asset == self.quote_asset:
            raise ValueError(
                "base_asset and quote_asset "
                "must be different"
            )
        return self
class ArbitrageEvaluationRequest(BaseModel):
    opportunity_type: ArbitrageOpportunityType = (
        "CUSTOM"
    )
    starting_asset: str = Field(
        min_length=1,
        max_length=20,
    )
    starting_amount: Decimal = Field(
        gt=0,
    )
    minimum_profit_percent: Decimal = Field(
        default=Decimal("0"),
    )
    legs: list[ArbitrageLegRequest] = Field(
        min_length=2,
        max_length=6,
    )
    @field_validator("starting_asset")
    @classmethod
    def normalize_starting_asset(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError(
                "starting_asset cannot be blank"
            )
        return normalized
    @model_validator(mode="after")
    def validate_route(self):
        if (
            self.opportunity_type
            == "CROSS_EXCHANGE"
            and len(self.legs) != 2
        ):
            raise ValueError(
                "CROSS_EXCHANGE opportunities "
                "must contain exactly two legs"
            )
        if (
            self.opportunity_type
            == "TRIANGULAR"
            and len(self.legs) != 3
        ):
            raise ValueError(
                "TRIANGULAR opportunities "
                "must contain exactly three legs"
            )
        current_asset = self.starting_asset
        for index, leg in enumerate(
            self.legs,
            start=1,
        ):
            if leg.side == "BUY":
                required_input_asset = (
                    leg.quote_asset
                )
                output_asset = leg.base_asset
            else:
                required_input_asset = (
                    leg.base_asset
                )
                output_asset = leg.quote_asset
            if current_asset != required_input_asset:
                raise ValueError(
                    f"leg {index} requires "
                    f"{required_input_asset} but "
                    f"current asset is "
                    f"{current_asset}"
                )
            current_asset = output_asset
        if current_asset != self.starting_asset:
            raise ValueError(
                "arbitrage route must finish in "
                "the starting asset"
            )
        return self
class ArbitrageLegResult(BaseModel):
    sequence: int = Field(
        ge=1,
    )
    exchange: str
    symbol: str
    side: ArbitrageSide
    input_asset: str
    output_asset: str
    input_amount: Decimal
    reference_price: Decimal
    effective_price: Decimal
    ideal_output_amount: Decimal
    slippage_adjusted_output_amount: (
        Decimal
    )
    fee_rate_percent: Decimal
    fee_amount: Decimal
    fixed_cost: Decimal
    net_output_amount: Decimal
class ArbitrageEvaluationResult(BaseModel):
    opportunity_type: (
        ArbitrageOpportunityType
    )
    starting_asset: str
    ending_asset: str
    starting_amount: Decimal
    gross_ending_amount: Decimal
    net_ending_amount: Decimal
    gross_profit_amount: Decimal
    net_profit_amount: Decimal
    gross_profit_percent: Decimal
    net_profit_percent: Decimal
    total_cost_impact: Decimal
    minimum_profit_percent: Decimal
    profitable: bool
    meets_minimum_profit: bool
    executable: bool
    legs: list[ArbitrageLegResult] = Field(
        default_factory=list
    )
