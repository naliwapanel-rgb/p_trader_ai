from copy import (
    deepcopy,
)
from datetime import (
    UTC,
    datetime,
)
from types import (
    SimpleNamespace,
)
from fastapi import (
    HTTPException,
    status,
)
from pydantic import (
    ValidationError,
)
from sqlalchemy.exc import (
    IntegrityError,
)
from sqlalchemy.orm import (
    Session,
)
from app.models.strategy_template import (
    StrategyTemplate,
)
from app.models.user import (
    User,
)
from app.repositories.strategy_template_repository import (
    StrategyTemplateRepository,
)
from app.schemas.trading_bot import (
    TradingBotCreateRequest,
)
from app.schemas.strategy_template import (
    StrategyTemplateBotCreateRequest,
    StrategyTemplateConfiguration,
    StrategyTemplateCreateRequest,
    StrategyTemplateUpdateRequest,
)
from app.services.trading_bot_service import (
    TradingBotService,
)
from app.services.trading_bot_strategy_runner import (
    TradingBotStrategyRunner,
)
class StrategyTemplateService:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.repository = (
            StrategyTemplateRepository(db)
        )
        self.strategy_runner = (
            TradingBotStrategyRunner()
        )
        self.bot_service = (
            TradingBotService(db)
        )
    def _rollback_safely(self) -> None:
        try:
            self.db.rollback()
        except Exception:
            pass
    def list_templates(
        self,
        *,
        current_user: User,
        template_status: str | None = None,
        visibility: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StrategyTemplate]:
        return self.repository.list_by_user(
            user_id=current_user.id,
            status=template_status,
            visibility=visibility,
            limit=limit,
            offset=offset,
        )
    def list_public_templates(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StrategyTemplate]:
        return (
            self.repository.list_published(
                limit=limit,
                offset=offset,
            )
        )
    def get_template(
        self,
        *,
        current_user: User,
        template_id: int,
    ) -> StrategyTemplate:
        template = (
            self.repository
            .get_by_id_and_user(
                template_id=template_id,
                user_id=current_user.id,
            )
        )
        if template is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Strategy template not found"
                ),
            )
        return template
    def _ensure_name_available(
        self,
        *,
        current_user: User,
        name: str,
        exclude_template_id: (
            int | None
        ) = None,
    ) -> None:
        existing = (
            self.repository
            .get_by_name_and_user(
                name=name,
                user_id=current_user.id,
            )
        )
        if existing is None:
            return
        if (
            exclude_template_id is not None
            and existing.id
            == exclude_template_id
        ):
            return
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "A strategy template with "
                "this name already exists"
            ),
        )
    def _validate_strategy_config(
        self,
        *,
        strategy_type: str,
        strategy_config: dict,
    ) -> dict:
        candidate = SimpleNamespace(
            strategy_type=strategy_type,
            strategy_config=(
                dict(
                    strategy_config or {}
                )
            ),
        )
        try:
            validated = (
                self.strategy_runner
                .validate_bot(candidate)
            )
        except ValueError as error:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=str(error),
            ) from error
        return dict(validated)
    def _validated_fields(
        self,
        configuration: (
            StrategyTemplateConfiguration
        ),
    ) -> dict:
        fields = configuration.model_dump()
        fields["strategy_config"] = (
            self._validate_strategy_config(
                strategy_type=(
                    configuration
                    .strategy_type
                ),
                strategy_config=(
                    configuration
                    .strategy_config
                ),
            )
        )
        return fields
    @staticmethod
    def _configuration_fields(
        template: StrategyTemplate,
    ) -> dict:
        return {
            "name": template.name,
            "description": (
                template.description
            ),
            "strategy_type": (
                template.strategy_type
            ),
            "symbol": template.symbol,
            "category": template.category,
            "timeframe": template.timeframe,
            "visibility": (
                template.visibility
            ),
            "paper_trading": (
                template.paper_trading
            ),
            "dry_run": template.dry_run,
            "risk_per_trade_percent": (
                template
                .risk_per_trade_percent
            ),
            "max_position_value_usd": (
                template
                .max_position_value_usd
            ),
            "max_daily_loss_percent": (
                template
                .max_daily_loss_percent
            ),
            "max_drawdown_percent": (
                template
                .max_drawdown_percent
            ),
            "stop_loss_percent": (
                template.stop_loss_percent
            ),
            "take_profit_percent": (
                template
                .take_profit_percent
            ),
            "strategy_config": dict(
                template.strategy_config
                or {}
            ),
        }
    def create_template(
        self,
        *,
        current_user: User,
        data: StrategyTemplateCreateRequest,
    ) -> StrategyTemplate:
        self._ensure_name_available(
            current_user=current_user,
            name=data.name,
        )
        fields = self._validated_fields(
            data
        )
        fields.update({
            "status": "DRAFT",
            "version": 1,
            "published_at": None,
        })
        try:
            return self.repository.create(
                user_id=current_user.id,
                fields=fields,
            )
        except IntegrityError as error:
            self._rollback_safely()
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "A strategy template with "
                    "this name already exists"
                ),
            ) from error
    def update_template(
        self,
        *,
        current_user: User,
        template_id: int,
        data: StrategyTemplateUpdateRequest,
    ) -> StrategyTemplate:
        template = self.get_template(
            current_user=current_user,
            template_id=template_id,
        )
        if template.status != "DRAFT":
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Only draft strategy "
                    "templates can be modified"
                ),
            )
        requested = data.model_dump(
            exclude_unset=True
        )
        effective = (
            self._configuration_fields(
                template
            )
        )
        effective.update(requested)
        try:
            configuration = (
                StrategyTemplateConfiguration
                .model_validate(effective)
            )
        except ValidationError as error:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=str(error),
            ) from error
        if (
            configuration.name
            != template.name
        ):
            self._ensure_name_available(
                current_user=current_user,
                name=configuration.name,
                exclude_template_id=(
                    template.id
                ),
            )
        fields = self._validated_fields(
            configuration
        )
        fields["version"] = (
            template.version + 1
        )
        try:
            return (
                self.repository
                .update_fields(
                    template=template,
                    fields=fields,
                )
            )
        except IntegrityError as error:
            self._rollback_safely()
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "A strategy template with "
                    "this name already exists"
                ),
            ) from error
    def publish_template(
        self,
        *,
        current_user: User,
        template_id: int,
    ) -> StrategyTemplate:
        template = self.get_template(
            current_user=current_user,
            template_id=template_id,
        )
        if template.status == "ARCHIVED":
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Archived strategy "
                    "templates cannot be "
                    "published"
                ),
            )
        if template.status == "PUBLISHED":
            return template
        try:
            configuration = (
                StrategyTemplateConfiguration
                .model_validate(
                    self._configuration_fields(
                        template
                    )
                )
            )
        except ValidationError as error:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=str(error),
            ) from error
        fields = self._validated_fields(
            configuration
        )
        fields.update({
            "visibility": "PUBLIC",
            "status": "PUBLISHED",
            "published_at": (
                datetime.now(UTC)
            ),
        })
        return self.repository.update_fields(
            template=template,
            fields=fields,
        )
    def unpublish_template(
        self,
        *,
        current_user: User,
        template_id: int,
    ) -> StrategyTemplate:
        template = self.get_template(
            current_user=current_user,
            template_id=template_id,
        )
        if template.status != "PUBLISHED":
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Only published strategy "
                    "templates can be unpublished"
                ),
            )
        return self.repository.update_fields(
            template=template,
            fields={
                "status": "DRAFT",
                "visibility": "PRIVATE",
                "published_at": None,
            },
        )
    def archive_template(
        self,
        *,
        current_user: User,
        template_id: int,
    ) -> StrategyTemplate:
        template = self.get_template(
            current_user=current_user,
            template_id=template_id,
        )
        if template.status != "DRAFT":
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Only draft strategy "
                    "templates can be archived"
                ),
            )
        return self.repository.update_fields(
            template=template,
            fields={
                "status": "ARCHIVED",
                "visibility": "PRIVATE",
                "published_at": None,
            },
        )
    def restore_template(
        self,
        *,
        current_user: User,
        template_id: int,
    ) -> StrategyTemplate:
        template = self.get_template(
            current_user=current_user,
            template_id=template_id,
        )
        if template.status != "ARCHIVED":
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Only archived strategy "
                    "templates can be restored"
                ),
            )
        return self.repository.update_fields(
            template=template,
            fields={
                "status": "DRAFT",
                "visibility": "PRIVATE",
                "published_at": None,
            },
        )

    def get_template_for_bot_creation(
        self,
        *,
        current_user: User,
        template_id: int,
    ) -> StrategyTemplate:
        owned_template = (
            self.repository
            .get_by_id_and_user(
                template_id=template_id,
                user_id=current_user.id,
            )
        )
        if owned_template is not None:
            if (
                owned_template.status
                == "ARCHIVED"
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_409_CONFLICT
                    ),
                    detail=(
                        "Archived strategy "
                        "templates cannot create "
                        "trading bots"
                    ),
                )
            return owned_template
        public_template = (
            self.repository
            .get_published_by_id(
                template_id=template_id,
            )
        )
        if public_template is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Strategy template not found"
                ),
            )
        return public_template
    def create_bot_from_template(
        self,
        *,
        current_user: User,
        template_id: int,
        data: (
            StrategyTemplateBotCreateRequest
        ),
    ):
        template = (
            self.get_template_for_bot_creation(
                current_user=current_user,
                template_id=template_id,
            )
        )
        strategy_config = (
            self._validate_strategy_config(
                strategy_type=(
                    template.strategy_type
                ),
                strategy_config=deepcopy(
                    template.strategy_config
                    or {}
                ),
            )
        )
        if (
            "description"
            in data.model_fields_set
        ):
            description = data.description
        else:
            description = (
                template.description
            )
        try:
            bot_data = (
                TradingBotCreateRequest(
                    exchange_account_id=(
                        data.exchange_account_id
                    ),
                    name=data.name,
                    description=description,
                    strategy_type=(
                        template.strategy_type
                    ),
                    symbol=template.symbol,
                    category=template.category,
                    timeframe=template.timeframe,
                    paper_trading=True,
                    dry_run=True,
                    risk_per_trade_percent=(
                        template
                        .risk_per_trade_percent
                    ),
                    max_position_value_usd=(
                        template
                        .max_position_value_usd
                    ),
                    max_daily_loss_percent=(
                        template
                        .max_daily_loss_percent
                    ),
                    max_drawdown_percent=(
                        template
                        .max_drawdown_percent
                    ),
                    stop_loss_percent=(
                        template
                        .stop_loss_percent
                    ),
                    take_profit_percent=(
                        template
                        .take_profit_percent
                    ),
                    strategy_config=(
                        strategy_config
                    ),
                )
            )
        except ValidationError as error:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "Strategy template cannot "
                    "create a valid trading bot: "
                    f"{error}"
                ),
            ) from error
        return self.bot_service.create_bot(
            current_user=current_user,
            data=bot_data,
        )
    def delete_template(
        self,
        *,
        current_user: User,
        template_id: int,
    ) -> None:
        template = self.get_template(
            current_user=current_user,
            template_id=template_id,
        )
        if template.status == "PUBLISHED":
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Published strategy "
                    "templates must be "
                    "unpublished before deletion"
                ),
            )
        self.repository.delete(template)
