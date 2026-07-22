from datetime import (
    UTC,
    datetime,
)
from types import (
    SimpleNamespace,
)
from unittest.mock import (
    MagicMock,
)
import pytest
from fastapi import (
    HTTPException,
)
from app.schemas.strategy_template import (
    StrategyTemplateBotCreateRequest,
    StrategyTemplateCreateRequest,
    StrategyTemplateUpdateRequest,
)
from app.services.strategy_template_service import (
    StrategyTemplateService,
)
NOW = datetime(
    2026,
    7,
    22,
    14,
    0,
    tzinfo=UTC,
)
def build_user():
    return SimpleNamespace(
        id=7,
    )
def build_template(
    *,
    template_id=10,
    status="DRAFT",
    visibility="PRIVATE",
    version=1,
):
    return SimpleNamespace(
        id=template_id,
        user_id=7,
        name="Momentum Template",
        description="Reusable template",
        strategy_type="RULE_BASED",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        visibility=visibility,
        status=status,
        paper_trading=True,
        dry_run=True,
        risk_per_trade_percent=1.0,
        max_position_value_usd=25.0,
        max_daily_loss_percent=3.0,
        max_drawdown_percent=10.0,
        stop_loss_percent=None,
        take_profit_percent=None,
        strategy_config={
            "buy_change_percent_24h": 1.0,
            "sell_change_percent_24h": -1.0,
        },
        version=version,
        published_at=(
            NOW
            if status == "PUBLISHED"
            else None
        ),
        created_at=NOW,
        updated_at=NOW,
    )
def build_service(
    *,
    template=None,
):
    db = MagicMock()
    service = (
        StrategyTemplateService(db)
    )
    repository = MagicMock()
    runner = MagicMock()
    bot_service = MagicMock()
    service.repository = repository
    service.strategy_runner = runner
    service.bot_service = bot_service
    repository.get_by_id_and_user.return_value = (
        template
    )
    repository.get_published_by_id.return_value = (
        None
    )
    repository.get_by_name_and_user.return_value = (
        None
    )
    def update_fields(
        *,
        template,
        fields,
    ):
        for key, value in fields.items():
            setattr(
                template,
                key,
                value,
            )
        return template
    repository.update_fields.side_effect = (
        update_fields
    )
    runner.validate_bot.return_value = {
        "buy_change_percent_24h": 1.0,
        "sell_change_percent_24h": -1.0,
        "maximum_spread_percent": 0.5,
        "minimum_turnover_24h": 0.0,
        "confidence_scale_percent": 5.0,
    }
    return SimpleNamespace(
        service=service,
        repository=repository,
        runner=runner,
        bot_service=bot_service,
        db=db,
    )
def create_request():
    return StrategyTemplateCreateRequest(
        name=" Momentum Template ",
        description=" Reusable template ",
        strategy_type="RULE_BASED",
        symbol=" btcusdt ",
        strategy_config={
            "buy_change_percent_24h": 1.0,
            "sell_change_percent_24h": -1.0,
        },
    )
def test_list_is_owner_scoped():
    context = build_service()
    user = build_user()
    context.repository.list_by_user.return_value = [
        build_template()
    ]
    result = (
        context.service.list_templates(
            current_user=user,
            template_status="DRAFT",
            visibility="PRIVATE",
            limit=20,
            offset=5,
        )
    )
    assert len(result) == 1
    context.repository.list_by_user.assert_called_once_with(
        user_id=7,
        status="DRAFT",
        visibility="PRIVATE",
        limit=20,
        offset=5,
    )
def test_get_missing_template_is_rejected():
    context = build_service(
        template=None
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        context.service.get_template(
            current_user=build_user(),
            template_id=10,
        )
    assert error.value.status_code == 404
def test_create_validates_strategy():
    context = build_service()
    user = build_user()
    created = build_template()
    context.repository.create.return_value = (
        created
    )
    result = (
        context.service.create_template(
            current_user=user,
            data=create_request(),
        )
    )
    assert result is created
    context.runner.validate_bot.assert_called_once()
    candidate = (
        context.runner
        .validate_bot
        .call_args
        .args[0]
    )
    assert candidate.strategy_type == (
        "RULE_BASED"
    )
    _, kwargs = (
        context.repository
        .create
        .call_args
    )
    assert kwargs["user_id"] == 7
    assert kwargs["fields"]["name"] == (
        "Momentum Template"
    )
    assert kwargs["fields"]["symbol"] == (
        "BTCUSDT"
    )
    assert kwargs["fields"]["status"] == (
        "DRAFT"
    )
    assert kwargs["fields"]["version"] == 1
def test_create_rejects_duplicate_name():
    context = build_service()
    context.repository.get_by_name_and_user.return_value = (
        build_template()
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        context.service.create_template(
            current_user=build_user(),
            data=create_request(),
        )
    assert error.value.status_code == 409
    context.runner.validate_bot.assert_not_called()
def test_invalid_strategy_config_is_rejected():
    context = build_service()
    context.runner.validate_bot.side_effect = (
        ValueError(
            "Invalid strategy configuration"
        )
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        context.service.create_template(
            current_user=build_user(),
            data=create_request(),
        )
    assert error.value.status_code == 400
    assert (
        "Invalid strategy configuration"
        in error.value.detail
    )
def test_published_template_cannot_be_edited():
    context = build_service(
        template=build_template(
            status="PUBLISHED",
            visibility="PUBLIC",
        )
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        context.service.update_template(
            current_user=build_user(),
            template_id=10,
            data=StrategyTemplateUpdateRequest(
                name="Changed Template"
            ),
        )
    assert error.value.status_code == 409
def test_update_merges_and_increments_version():
    template = build_template()
    context = build_service(
        template=template
    )
    result = (
        context.service.update_template(
            current_user=build_user(),
            template_id=10,
            data=StrategyTemplateUpdateRequest(
                risk_per_trade_percent=2.0,
                max_daily_loss_percent=4.0,
            ),
        )
    )
    assert result.version == 2
    assert (
        result.risk_per_trade_percent
        == 2.0
    )
    assert (
        result.max_daily_loss_percent
        == 4.0
    )
    context.runner.validate_bot.assert_called_once()
def test_publish_validates_and_makes_public():
    template = build_template()
    context = build_service(
        template=template
    )
    result = (
        context.service.publish_template(
            current_user=build_user(),
            template_id=10,
        )
    )
    assert result.status == "PUBLISHED"
    assert result.visibility == "PUBLIC"
    assert result.published_at is not None
    context.runner.validate_bot.assert_called_once()
def test_archived_template_cannot_be_published():
    context = build_service(
        template=build_template(
            status="ARCHIVED"
        )
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        context.service.publish_template(
            current_user=build_user(),
            template_id=10,
        )
    assert error.value.status_code == 409
def test_unpublish_returns_template_to_draft():
    context = build_service(
        template=build_template(
            status="PUBLISHED",
            visibility="PUBLIC",
        )
    )
    result = (
        context.service.unpublish_template(
            current_user=build_user(),
            template_id=10,
        )
    )
    assert result.status == "DRAFT"
    assert result.visibility == "PRIVATE"
    assert result.published_at is None
def test_archive_and_restore_template():
    template = build_template()
    context = build_service(
        template=template
    )
    archived = (
        context.service.archive_template(
            current_user=build_user(),
            template_id=10,
        )
    )
    assert archived.status == "ARCHIVED"
    restored = (
        context.service.restore_template(
            current_user=build_user(),
            template_id=10,
        )
    )
    assert restored.status == "DRAFT"
    assert restored.visibility == "PRIVATE"
def test_published_template_cannot_be_deleted():
    context = build_service(
        template=build_template(
            status="PUBLISHED",
            visibility="PUBLIC",
        )
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        context.service.delete_template(
            current_user=build_user(),
            template_id=10,
        )
    assert error.value.status_code == 409
    context.repository.delete.assert_not_called()
def test_draft_template_can_be_deleted():
    template = build_template()
    context = build_service(
        template=template
    )
    context.service.delete_template(
        current_user=build_user(),
        template_id=10,
    )
    context.repository.delete.assert_called_once_with(
        template
    )
def test_owner_can_create_bot_from_draft():
    template = build_template()
    context = build_service(
        template=template
    )
    created_bot = SimpleNamespace(
        id=50,
        user_id=7,
        name="My Template Bot",
    )
    context.bot_service.create_bot.return_value = (
        created_bot
    )
    result = (
        context.service
        .create_bot_from_template(
            current_user=build_user(),
            template_id=10,
            data=(
                StrategyTemplateBotCreateRequest(
                    exchange_account_id=5,
                    name="My Template Bot",
                )
            ),
        )
    )
    assert result is created_bot
    context.repository.get_published_by_id.assert_not_called()
def test_public_published_template_is_accessible():
    public_template = build_template(
        status="PUBLISHED",
        visibility="PUBLIC",
    )
    context = build_service(
        template=None
    )
    context.repository.get_published_by_id.return_value = (
        public_template
    )
    context.bot_service.create_bot.return_value = (
        SimpleNamespace(id=50)
    )
    context.service.create_bot_from_template(
        current_user=build_user(),
        template_id=10,
        data=StrategyTemplateBotCreateRequest(
            name="Public Template Bot",
        ),
    )
    context.repository.get_published_by_id.assert_called_once_with(
        template_id=10,
    )
def test_private_foreign_template_is_hidden():
    context = build_service(
        template=None
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        (
            context.service
            .create_bot_from_template(
                current_user=build_user(),
                template_id=10,
                data=(
                    StrategyTemplateBotCreateRequest(
                        name="Hidden Template Bot"
                    )
                ),
            )
        )
    assert error.value.status_code == 404
    context.bot_service.create_bot.assert_not_called()
def test_archived_owned_template_is_blocked():
    context = build_service(
        template=build_template(
            status="ARCHIVED"
        )
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        (
            context.service
            .create_bot_from_template(
                current_user=build_user(),
                template_id=10,
                data=(
                    StrategyTemplateBotCreateRequest(
                        name="Archived Bot"
                    )
                ),
            )
        )
    assert error.value.status_code == 409
    context.bot_service.create_bot.assert_not_called()
def test_template_creation_forces_safe_execution():
    template = build_template()
    template.paper_trading = False
    template.dry_run = True
    context = build_service(
        template=template
    )
    context.bot_service.create_bot.return_value = (
        SimpleNamespace(id=50)
    )
    context.service.create_bot_from_template(
        current_user=build_user(),
        template_id=10,
        data=StrategyTemplateBotCreateRequest(
            exchange_account_id=99,
            name="Safe Copied Bot",
        ),
    )
    _, kwargs = (
        context.bot_service
        .create_bot
        .call_args
    )
    assert kwargs["current_user"].id == 7
    bot_data = kwargs["data"]
    assert bot_data.exchange_account_id == 99
    assert bot_data.name == "Safe Copied Bot"
    assert bot_data.paper_trading is True
    assert bot_data.dry_run is True
    assert bot_data.strategy_type == (
        template.strategy_type
    )
    assert bot_data.symbol == template.symbol
    assert bot_data.category == (
        template.category
    )
    assert bot_data.timeframe == (
        template.timeframe
    )
    assert (
        bot_data.risk_per_trade_percent
        == template
        .risk_per_trade_percent
    )
def test_template_description_can_be_overridden():
    template = build_template()
    context = build_service(
        template=template
    )
    context.bot_service.create_bot.return_value = (
        SimpleNamespace(id=50)
    )
    context.service.create_bot_from_template(
        current_user=build_user(),
        template_id=10,
        data=StrategyTemplateBotCreateRequest(
            name="Description Bot",
            description="Follower description",
        ),
    )
    _, kwargs = (
        context.bot_service
        .create_bot
        .call_args
    )
    assert (
        kwargs["data"].description
        == "Follower description"
    )
def test_template_strategy_is_revalidated():
    context = build_service(
        template=build_template()
    )
    context.runner.validate_bot.side_effect = (
        ValueError(
            "Invalid template strategy"
        )
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        (
            context.service
            .create_bot_from_template(
                current_user=build_user(),
                template_id=10,
                data=(
                    StrategyTemplateBotCreateRequest(
                        name="Invalid Strategy Bot"
                    )
                ),
            )
        )
    assert error.value.status_code == 400
    assert (
        "Invalid template strategy"
        in error.value.detail
    )
    context.bot_service.create_bot.assert_not_called()
