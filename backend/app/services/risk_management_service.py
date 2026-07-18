from app.schemas.risk_management import (
    RiskConfiguration,
    RiskConfigurationUpdate,
    RiskLimitCheck,
    RiskValidationResult,
)
class RiskManagementService:
    def __init__(
        self,
        configuration: RiskConfiguration | None = None,
    ):
        self._configuration = (
            configuration or RiskConfiguration()
        )
    def get_configuration(self) -> RiskConfiguration:
        return self._configuration.model_copy(deep=True)
    def update_configuration(
        self,
        data: RiskConfigurationUpdate,
    ) -> RiskConfiguration:
        updates = data.model_dump(
            exclude_none=True,
            exclude_unset=True,
        )
        candidate = self._configuration.model_copy(
            update=updates,
        )
        self._configuration = RiskConfiguration(
            **candidate.model_dump()
        )
        return self.get_configuration()
    def restore_defaults(self) -> RiskConfiguration:
        self._configuration = RiskConfiguration()
        return self.get_configuration()
    def validate_leverage(
        self,
        leverage: float,
    ) -> RiskLimitCheck:
        passed = (
            leverage > 0
            and leverage <= self._configuration.max_leverage
        )
        if passed:
            message = "Leverage is within the configured limit"
        else:
            message = (
                "Requested leverage exceeds the configured "
                "maximum leverage"
            )
        return RiskLimitCheck(
            rule="MAX_LEVERAGE",
            passed=passed,
            actual_value=leverage,
            limit_value=self._configuration.max_leverage,
            message=message,
        )
    def validate_open_positions(
        self,
        current_open_positions: int,
    ) -> RiskLimitCheck:
        passed = (
            current_open_positions
            < self._configuration.max_open_positions
        )
        if passed:
            message = (
                "Open position count is within the "
                "configured limit"
            )
        else:
            message = (
                "Maximum number of open positions has "
                "been reached"
            )
        return RiskLimitCheck(
            rule="MAX_OPEN_POSITIONS",
            passed=passed,
            actual_value=current_open_positions,
            limit_value=(
                self._configuration.max_open_positions
            ),
            message=message,
        )
    def validate_risk_reward(
        self,
        risk_reward_ratio: float,
    ) -> RiskLimitCheck:
        passed = (
            risk_reward_ratio
            >= self._configuration
            .minimum_risk_reward_ratio
        )
        if passed:
            message = (
                "Risk/reward ratio meets the configured "
                "minimum"
            )
        else:
            message = (
                "Risk/reward ratio is below the configured "
                "minimum"
            )
        return RiskLimitCheck(
            rule="MINIMUM_RISK_REWARD",
            passed=passed,
            actual_value=risk_reward_ratio,
            limit_value=(
                self._configuration
                .minimum_risk_reward_ratio
            ),
            message=message,
        )
    def build_validation_result(
        self,
        checks: list[RiskLimitCheck],
    ) -> RiskValidationResult:
        rejection_reasons = [
            check.message
            for check in checks
            if not check.passed
        ]
        return RiskValidationResult(
            accepted=not rejection_reasons,
            checks=checks,
            rejection_reasons=rejection_reasons,
        )
class PositionSizeCalculator:
    @staticmethod
    def calculate(
        data,
    ):
        from decimal import Decimal
        from app.exchanges.decimal_utils import (
            round_down_to_step,
            to_decimal,
        )
        from app.schemas.risk_management import (
            PositionSizeResult,
        )
        equity = to_decimal(data.account_equity)
        risk_percent = to_decimal(data.risk_percent)
        entry_price = to_decimal(data.entry_price)
        stop_loss_price = to_decimal(data.stop_loss_price)
        quantity_step = to_decimal(data.quantity_step)
        minimum_quantity = to_decimal(
            data.minimum_quantity
        )
        maximum_quantity = to_decimal(
            data.maximum_quantity
        )
        minimum_notional = to_decimal(
            data.minimum_notional
        )
        leverage = to_decimal(data.leverage)
        one_hundred = Decimal("100")
        requested_risk_amount = (
            equity * risk_percent / one_hundred
        )
        stop_distance = abs(
            entry_price - stop_loss_price
        )
        raw_quantity = (
            requested_risk_amount / stop_distance
        )
        capped_by_maximum_quantity = False
        if raw_quantity > maximum_quantity:
            raw_quantity = maximum_quantity
            capped_by_maximum_quantity = True
        rounded_quantity = round_down_to_step(
            raw_quantity,
            quantity_step,
        )
        position_notional = (
            rounded_quantity * entry_price
        )
        required_margin = (
            position_notional / leverage
        )
        actual_risk_amount = (
            rounded_quantity * stop_distance
        )
        actual_risk_percent = (
            actual_risk_amount
            / equity
            * one_hundred
        )
        rejection_reasons = []
        if rounded_quantity <= 0:
            rejection_reasons.append(
                "Calculated quantity is zero after "
                "quantity-step rounding"
            )
        if rounded_quantity < minimum_quantity:
            rejection_reasons.append(
                "Calculated quantity is below the "
                "instrument minimum quantity"
            )
        if rounded_quantity > maximum_quantity:
            rejection_reasons.append(
                "Calculated quantity exceeds the "
                "instrument maximum quantity"
            )
        if (
            minimum_notional > 0
            and position_notional < minimum_notional
        ):
            rejection_reasons.append(
                "Calculated position notional is below "
                "the instrument minimum notional"
            )
        return PositionSizeResult(
            valid=not rejection_reasons,
            account_equity=float(equity),
            requested_risk_percent=float(
                risk_percent
            ),
            requested_risk_amount=float(
                requested_risk_amount
            ),
            entry_price=float(entry_price),
            stop_loss_price=float(stop_loss_price),
            stop_distance=float(stop_distance),
            raw_quantity=float(raw_quantity),
            rounded_quantity=float(
                rounded_quantity
            ),
            position_notional=float(
                position_notional
            ),
            required_margin=float(
                required_margin
            ),
            actual_risk_amount=float(
                actual_risk_amount
            ),
            actual_risk_percent=float(
                actual_risk_percent
            ),
            quantity_step=float(quantity_step),
            minimum_quantity=float(
                minimum_quantity
            ),
            maximum_quantity=float(
                maximum_quantity
            ),
            minimum_notional=float(
                minimum_notional
            ),
            leverage=float(leverage),
            capped_by_maximum_quantity=(
                capped_by_maximum_quantity
            ),
            rejection_reasons=rejection_reasons,
        )
