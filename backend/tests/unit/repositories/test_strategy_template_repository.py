from __future__ import (
    annotations,
)
from collections.abc import (
    Generator,
)
import pytest
from sqlalchemy import (
    create_engine,
)
from sqlalchemy.exc import (
    IntegrityError,
)
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)
from sqlalchemy.pool import (
    StaticPool,
)
from app.database.session import (
    Base,
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
@pytest.fixture
def db() -> Generator[
    Session,
    None,
    None,
]:
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        bind=engine,
        tables=[
            User.__table__,
            StrategyTemplate.__table__,
        ],
    )
    testing_session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    session = testing_session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(
            bind=engine,
            tables=[
                StrategyTemplate.__table__,
                User.__table__,
            ],
        )
        engine.dispose()
def create_user(
    db: Session,
    *,
    email: str,
) -> User:
    user = User(
        full_name="Test User",
        email=email,
        hashed_password="hashed-password",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
def template_fields(
    *,
    name: str = "Momentum Template",
    visibility: str = "PRIVATE",
    status: str = "DRAFT",
) -> dict:
    return {
        "name": name,
        "description": (
            "Reusable momentum strategy"
        ),
        "strategy_type": "MOMENTUM",
        "symbol": "BTCUSDT",
        "category": "linear",
        "timeframe": "5m",
        "visibility": visibility,
        "status": status,
        "paper_trading": True,
        "dry_run": True,
        "risk_per_trade_percent": 1.0,
        "max_position_value_usd": 25.0,
        "max_daily_loss_percent": 3.0,
        "max_drawdown_percent": 10.0,
        "stop_loss_percent": 1.5,
        "take_profit_percent": 3.0,
        "strategy_config": {
            "lookback_period": 20,
        },
        "version": 1,
    }
def test_create_and_get_owned_template(
    db: Session,
):
    user = create_user(
        db,
        email="owner@example.com",
    )
    repository = (
        StrategyTemplateRepository(db)
    )
    template = repository.create(
        user_id=user.id,
        fields=template_fields(),
    )
    loaded = (
        repository.get_by_id_and_user(
            template_id=template.id,
            user_id=user.id,
        )
    )
    assert loaded is not None
    assert loaded.id == template.id
    assert loaded.user_id == user.id
    assert loaded.name == (
        "Momentum Template"
    )
    assert loaded.strategy_config == {
        "lookback_period": 20,
    }
def test_template_owner_isolation(
    db: Session,
):
    owner = create_user(
        db,
        email="owner@example.com",
    )
    other_user = create_user(
        db,
        email="other@example.com",
    )
    repository = (
        StrategyTemplateRepository(db)
    )
    template = repository.create(
        user_id=owner.id,
        fields=template_fields(),
    )
    assert (
        repository.get_by_id_and_user(
            template_id=template.id,
            user_id=other_user.id,
        )
        is None
    )
def test_name_is_unique_per_owner(
    db: Session,
):
    user = create_user(
        db,
        email="owner@example.com",
    )
    repository = (
        StrategyTemplateRepository(db)
    )
    repository.create(
        user_id=user.id,
        fields=template_fields(),
    )
    with pytest.raises(
        IntegrityError,
    ):
        repository.create(
            user_id=user.id,
            fields=template_fields(),
        )
    db.rollback()
def test_same_name_allowed_for_different_users(
    db: Session,
):
    first_user = create_user(
        db,
        email="first@example.com",
    )
    second_user = create_user(
        db,
        email="second@example.com",
    )
    repository = (
        StrategyTemplateRepository(db)
    )
    first = repository.create(
        user_id=first_user.id,
        fields=template_fields(),
    )
    second = repository.create(
        user_id=second_user.id,
        fields=template_fields(),
    )
    assert first.name == second.name
    assert first.user_id != second.user_id
def test_list_by_user_filters_status(
    db: Session,
):
    user = create_user(
        db,
        email="owner@example.com",
    )
    repository = (
        StrategyTemplateRepository(db)
    )
    repository.create(
        user_id=user.id,
        fields=template_fields(
            name="Draft Template",
        ),
    )
    repository.create(
        user_id=user.id,
        fields=template_fields(
            name="Published Template",
            visibility="PUBLIC",
            status="PUBLISHED",
        ),
    )
    templates = repository.list_by_user(
        user_id=user.id,
        status="PUBLISHED",
    )
    assert len(templates) == 1
    assert templates[0].name == (
        "Published Template"
    )
def test_public_listing_requires_published_status(
    db: Session,
):
    user = create_user(
        db,
        email="owner@example.com",
    )
    repository = (
        StrategyTemplateRepository(db)
    )
    repository.create(
        user_id=user.id,
        fields=template_fields(
            name="Public Draft",
            visibility="PUBLIC",
            status="DRAFT",
        ),
    )
    published = repository.create(
        user_id=user.id,
        fields=template_fields(
            name="Public Published",
            visibility="PUBLIC",
            status="PUBLISHED",
        ),
    )
    repository.create(
        user_id=user.id,
        fields=template_fields(
            name="Private Published",
            visibility="PRIVATE",
            status="PUBLISHED",
        ),
    )
    templates = (
        repository.list_published()
    )
    assert [
        template.id
        for template in templates
    ] == [published.id]
def test_update_fields_preserves_owner(
    db: Session,
):
    user = create_user(
        db,
        email="owner@example.com",
    )
    repository = (
        StrategyTemplateRepository(db)
    )
    template = repository.create(
        user_id=user.id,
        fields=template_fields(),
    )
    updated = repository.update_fields(
        template=template,
        fields={
            "name": "Updated Template",
            "version": 2,
        },
    )
    assert updated.name == (
        "Updated Template"
    )
    assert updated.version == 2
    assert updated.user_id == user.id
    with pytest.raises(
        ValueError,
        match="Protected",
    ):
        repository.update_fields(
            template=updated,
            fields={
                "user_id": user.id + 1,
            },
        )
def test_delete_template(
    db: Session,
):
    user = create_user(
        db,
        email="owner@example.com",
    )
    repository = (
        StrategyTemplateRepository(db)
    )
    template = repository.create(
        user_id=user.id,
        fields=template_fields(),
    )
    template_id = template.id
    repository.delete(template)
    assert (
        repository.get_by_id_and_user(
            template_id=template_id,
            user_id=user.id,
        )
        is None
    )
def test_execution_safety_constraint(
    db: Session,
):
    user = create_user(
        db,
        email="owner@example.com",
    )
    repository = (
        StrategyTemplateRepository(db)
    )
    fields = template_fields()
    fields["paper_trading"] = False
    fields["dry_run"] = False
    with pytest.raises(
        IntegrityError,
    ):
        repository.create(
            user_id=user.id,
            fields=fields,
        )
    db.rollback()
def test_risk_hierarchy_constraint(
    db: Session,
):
    user = create_user(
        db,
        email="owner@example.com",
    )
    repository = (
        StrategyTemplateRepository(db)
    )
    fields = template_fields()
    fields[
        "risk_per_trade_percent"
    ] = 5.0
    fields[
        "max_daily_loss_percent"
    ] = 3.0
    with pytest.raises(
        IntegrityError,
    ):
        repository.create(
            user_id=user.id,
            fields=fields,
        )
    db.rollback()
def test_get_published_by_id_hides_unavailable_templates(
    db: Session,
):
    user = create_user(
        db,
        email="publisher@example.com",
    )
    repository = (
        StrategyTemplateRepository(db)
    )
    public_published = (
        repository.create(
            user_id=user.id,
            fields=template_fields(
                name="Public Published",
                visibility="PUBLIC",
                status="PUBLISHED",
            ),
        )
    )
    public_draft = repository.create(
        user_id=user.id,
        fields=template_fields(
            name="Public Draft",
            visibility="PUBLIC",
            status="DRAFT",
        ),
    )
    private_published = (
        repository.create(
            user_id=user.id,
            fields=template_fields(
                name="Private Published",
                visibility="PRIVATE",
                status="PUBLISHED",
            ),
        )
    )
    assert (
        repository.get_published_by_id(
            template_id=(
                public_published.id
            ),
        )
        is public_published
    )
    assert (
        repository.get_published_by_id(
            template_id=public_draft.id,
        )
        is None
    )
    assert (
        repository.get_published_by_id(
            template_id=(
                private_published.id
            ),
        )
        is None
    )
