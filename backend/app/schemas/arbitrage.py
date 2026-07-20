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
CrossExchangeSortField = Literal[
    "net_profit_percent",
    "net_profit_amount",
    "gross_spread_percent",
    "evaluated_starting_amount",
    "quote_time_skew_ms",
]
class ArbitrageMarketQuote(BaseModel):
    exchange: str = Field(
        min_length=2,
        max_length=50,
    )
    symbol: str = Field(
        min_length=3,
        max_length=50,
    )
    base_asset: str = Field(
        min_length=1,
        max_length=20,
    )
    quote_asset: str = Field(
        min_length=1,
        max_length=20,
    )
    bid_price: Decimal = Field(
        gt=0,
    )
    ask_price: Decimal = Field(
        gt=0,
    )
    bid_size: Decimal = Field(
        gt=0,
    )
    ask_size: Decimal = Field(
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
    fixed_buy_cost: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )
    fixed_sell_cost: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )
    observed_at_ms: int = Field(
        default=0,
        ge=0,
    )
    @field_validator(
        "exchange",
        "symbol",
        "base_asset",
        "quote_asset",
    )
    @classmethod
    def normalize_quote_identifier(
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
    def validate_quote(self):
        if self.base_asset == self.quote_asset:
            raise ValueError(
                "base_asset and quote_asset "
                "must be different"
            )
        if self.ask_price < self.bid_price:
            raise ValueError(
                "ask_price cannot be below "
                "bid_price"
            )
        return self
class CrossExchangeScanRequest(BaseModel):
    starting_asset: str = Field(
        default="USDT",
        min_length=1,
        max_length=20,
    )
    starting_amount: Decimal = Field(
        gt=0,
    )
    minimum_profit_percent: Decimal = Field(
        default=Decimal("0"),
    )
    maximum_quote_age_ms: int | None = Field(
        default=None,
        ge=0,
    )
    maximum_time_skew_ms: int | None = Field(
        default=None,
        ge=0,
    )
    require_full_liquidity: bool = True
    sort_by: CrossExchangeSortField = (
        "net_profit_percent"
    )
    descending: bool = True
    limit: int = Field(
        default=50,
        ge=1,
        le=200,
    )
    quotes: list[ArbitrageMarketQuote] = Field(
        min_length=2,
        max_length=500,
    )
    @field_validator("starting_asset")
    @classmethod
    def normalize_scan_starting_asset(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError(
                "starting_asset cannot be blank"
            )
        return normalized
class CrossExchangeOpportunity(BaseModel):
    base_asset: str
    quote_asset: str
    buy_exchange: str
    buy_symbol: str
    buy_ask_price: Decimal
    sell_exchange: str
    sell_symbol: str
    sell_bid_price: Decimal
    gross_spread_percent: Decimal
    requested_starting_amount: Decimal
    evaluated_starting_amount: Decimal
    maximum_starting_amount_by_liquidity: (
        Decimal
    )
    fully_liquid: bool
    quote_time_skew_ms: int = Field(
        ge=0,
    )
    evaluation: ArbitrageEvaluationResult
class CrossExchangeScanResult(BaseModel):
    starting_asset: str
    requested_starting_amount: Decimal
    total_quotes: int = Field(
        ge=0,
    )
    total_pairs: int = Field(
        ge=0,
    )
    total_routes_evaluated: int = Field(
        ge=0,
    )
    profitable_count: int = Field(
        ge=0,
    )
    matched_count: int = Field(
        ge=0,
    )
    returned_count: int = Field(
        ge=0,
    )
    scanned_at_ms: int = Field(
        ge=0,
    )
    opportunities: list[
        CrossExchangeOpportunity
    ] = Field(
        default_factory=list
    )
