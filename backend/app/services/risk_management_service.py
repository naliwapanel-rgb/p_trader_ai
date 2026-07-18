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
