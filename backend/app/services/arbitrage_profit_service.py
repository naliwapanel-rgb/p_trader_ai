from decimal import Decimal
from app.schemas.arbitrage import (
    ArbitrageEvaluationRequest,
    ArbitrageEvaluationResult,
    ArbitrageLegRequest,
    ArbitrageLegResult,
)
ONE_HUNDRED = Decimal("100")
class ArbitrageProfitService:
    @staticmethod
    def _input_asset(
        leg: ArbitrageLegRequest,
    ) -> str:
        if leg.side == "BUY":
            return leg.quote_asset
        return leg.base_asset
    @staticmethod
    def _output_asset(
        leg: ArbitrageLegRequest,
    ) -> str:
        if leg.side == "BUY":
            return leg.base_asset
        return leg.quote_asset
    @staticmethod
    def _convert_at_price(
        *,
        amount: Decimal,
        leg: ArbitrageLegRequest,
        price: Decimal,
    ) -> Decimal:
        if leg.side == "BUY":
            return amount / price
        return amount * price
    @staticmethod
    def _effective_price(
        leg: ArbitrageLegRequest,
    ) -> Decimal:
        slippage_rate = (
            leg.slippage_percent
            / ONE_HUNDRED
        )
        if leg.side == "BUY":
            effective_price = (
                leg.price
                * (
                    Decimal("1")
                    + slippage_rate
                )
            )
        else:
            effective_price = (
                leg.price
                * (
                    Decimal("1")
                    - slippage_rate
                )
            )
        if effective_price <= 0:
            raise ValueError(
                "effective execution price "
                "must be greater than zero"
            )
        return effective_price
    @classmethod
    def _evaluate_leg(
        cls,
        *,
        sequence: int,
        input_amount: Decimal,
        leg: ArbitrageLegRequest,
    ) -> ArbitrageLegResult:
        effective_price = (
            cls._effective_price(leg)
        )
        ideal_output_amount = (
            cls._convert_at_price(
                amount=input_amount,
                leg=leg,
                price=leg.price,
            )
        )
        slippage_adjusted_output = (
            cls._convert_at_price(
                amount=input_amount,
                leg=leg,
                price=effective_price,
            )
        )
        fee_amount = (
            slippage_adjusted_output
            * leg.fee_rate_percent
            / ONE_HUNDRED
        )
        net_output_amount = (
            slippage_adjusted_output
            - fee_amount
            - leg.fixed_cost
        )
        if net_output_amount <= 0:
            raise ValueError(
                f"leg {sequence} costs consume "
                "the entire output amount"
            )
        return ArbitrageLegResult(
            sequence=sequence,
            exchange=leg.exchange,
            symbol=leg.symbol,
            side=leg.side,
            input_asset=(
                cls._input_asset(leg)
            ),
            output_asset=(
                cls._output_asset(leg)
            ),
            input_amount=input_amount,
            reference_price=leg.price,
            effective_price=effective_price,
            ideal_output_amount=(
                ideal_output_amount
            ),
            slippage_adjusted_output_amount=(
                slippage_adjusted_output
            ),
            fee_rate_percent=(
                leg.fee_rate_percent
            ),
            fee_amount=fee_amount,
            fixed_cost=leg.fixed_cost,
            net_output_amount=(
                net_output_amount
            ),
        )
    @classmethod
    def evaluate(
        cls,
        data: ArbitrageEvaluationRequest,
    ) -> ArbitrageEvaluationResult:
        gross_amount = data.starting_amount
        net_amount = data.starting_amount
        leg_results: list[
            ArbitrageLegResult
        ] = []
        ending_asset = data.starting_asset
        for sequence, leg in enumerate(
            data.legs,
            start=1,
        ):
            gross_amount = (
                cls._convert_at_price(
                    amount=gross_amount,
                    leg=leg,
                    price=leg.price,
                )
            )
            leg_result = cls._evaluate_leg(
                sequence=sequence,
                input_amount=net_amount,
                leg=leg,
            )
            leg_results.append(leg_result)
            net_amount = (
                leg_result.net_output_amount
            )
            ending_asset = (
                leg_result.output_asset
            )
        gross_profit_amount = (
            gross_amount
            - data.starting_amount
        )
        net_profit_amount = (
            net_amount
            - data.starting_amount
        )
        gross_profit_percent = (
            gross_profit_amount
            / data.starting_amount
            * ONE_HUNDRED
        )
        net_profit_percent = (
            net_profit_amount
            / data.starting_amount
            * ONE_HUNDRED
        )
        total_cost_impact = (
            gross_amount - net_amount
        )
        profitable = (
            net_profit_amount > 0
        )
        meets_minimum_profit = (
            net_profit_percent
            >= data.minimum_profit_percent
        )
        return ArbitrageEvaluationResult(
            opportunity_type=(
                data.opportunity_type
            ),
            starting_asset=(
                data.starting_asset
            ),
            ending_asset=ending_asset,
            starting_amount=(
                data.starting_amount
            ),
            gross_ending_amount=(
                gross_amount
            ),
            net_ending_amount=net_amount,
            gross_profit_amount=(
                gross_profit_amount
            ),
            net_profit_amount=(
                net_profit_amount
            ),
            gross_profit_percent=(
                gross_profit_percent
            ),
            net_profit_percent=(
                net_profit_percent
            ),
            total_cost_impact=(
                total_cost_impact
            ),
            minimum_profit_percent=(
                data.minimum_profit_percent
            ),
            profitable=profitable,
            meets_minimum_profit=(
                meets_minimum_profit
            ),
            executable=(
                profitable
                and meets_minimum_profit
            ),
            legs=leg_results,
        )
