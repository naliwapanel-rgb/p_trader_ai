from types import (
    SimpleNamespace,
)
import pytest
from fastapi import (
    FastAPI,
    HTTPException,
)
from fastapi.exceptions import (
    RequestValidationError,
)
from fastapi.testclient import (
    TestClient,
)
from sqlalchemy import (
    create_engine,
)
from sqlalchemy.orm import (
    sessionmaker,
)
from sqlalchemy.pool import (
    StaticPool,
)
import app.models  # noqa: F401
from app.api.v1.router import (
    api_router,
)
from app.core.exceptions import (
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.security.token import (
    create_access_token,
)
from app.database.session import (
    Base,
    get_db,
)
from app.database.sqlite import (
    configure_sqlite_engine,
)
from app.models.copy_trading_subscription import (
    CopyTradingSubscription,
)
from app.models.exchange_account import (
    ExchangeAccount,
)
from app.models.strategy_template import (
    StrategyTemplate,
)
from app.models.trading_bot import (
    TradingBot,
)
from app.models.user import (
    User,
)
RULE_CONFIG = {
    "buy_change_percent_24h": 1.0,
    "sell_change_percent_24h": -1.0,
    "maximum_spread_percent": 0.5,
    "minimum_turnover_24h": 0.0,
    "confidence_scale_percent": 5.0,
}
def authorization(
    token: str,
) -> dict[str, str]:
    return {
        "Authorization": (
            f"Bearer {token}"
        ),
    }
def build_bot(
    *,
    user_id: int,
    account_id: int,
    name: str,
) -> TradingBot:
    return TradingBot(
        user_id=user_id,
        exchange_account_id=(
            account_id
        ),
        name=name,
        description=(
            "Ownership integration bot"
        ),
        strategy_type="RULE_BASED",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        status="DRAFT",
        paper_trading=True,
        dry_run=True,
        risk_per_trade_percent=1.0,
        max_position_value_usd=25.0,
        max_daily_loss_percent=3.0,
        max_drawdown_percent=10.0,
        stop_loss_percent=None,
        take_profit_percent=None,
        strategy_config=dict(
            RULE_CONFIG
        ),
    )
def build_template(
    *,
    user_id: int,
    name: str,
    visibility: str,
    status: str,
) -> StrategyTemplate:
    return StrategyTemplate(
        user_id=user_id,
        name=name,
        description=(
            "Ownership integration "
            "template"
        ),
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
        strategy_config=dict(
            RULE_CONFIG
        ),
        version=1,
    )
@pytest.fixture
def integration_context():
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )
    configure_sqlite_engine(
        engine
    )
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(
        bind=engine
    )
    app = FastAPI()
    app.add_exception_handler(
        HTTPException,
        http_exception_handler,
    )
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )
    app.add_exception_handler(
        Exception,
        general_exception_handler,
    )
    app.include_router(
        api_router,
        prefix="/api/v1",
    )
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[
        get_db
    ] = override_get_db
    with session_factory() as db:
        user_a = User(
            full_name="User Alpha",
            email="alpha@example.com",
            hashed_password="hash-alpha",
            is_active=True,
        )
        user_b = User(
            full_name="User Beta",
            email="beta@example.com",
            hashed_password="hash-beta",
            is_active=True,
        )
        inactive_user = User(
            full_name="Inactive User",
            email="inactive@example.com",
            hashed_password=(
                "hash-inactive"
            ),
            is_active=False,
        )
        db.add_all([
            user_a,
            user_b,
            inactive_user,
        ])
        db.commit()
        db.refresh(user_a)
        db.refresh(user_b)
        db.refresh(inactive_user)
        account_a = ExchangeAccount(
            user_id=user_a.id,
            exchange_name="BYBIT",
            account_name=(
                "Alpha Exchange"
            ),
            encrypted_api_key=(
                "encrypted-alpha-key"
            ),
            encrypted_api_secret=(
                "encrypted-alpha-secret"
            ),
            is_testnet=True,
            is_active=True,
        )
        account_b = ExchangeAccount(
            user_id=user_b.id,
            exchange_name="BYBIT",
            account_name=(
                "Beta Exchange"
            ),
            encrypted_api_key=(
                "encrypted-beta-key"
            ),
            encrypted_api_secret=(
                "encrypted-beta-secret"
            ),
            is_testnet=True,
            is_active=True,
        )
        db.add_all([
            account_a,
            account_b,
        ])
        db.commit()
        db.refresh(account_a)
        db.refresh(account_b)
        bot_a = build_bot(
            user_id=user_a.id,
            account_id=account_a.id,
            name="Alpha Bot",
        )
        bot_b = build_bot(
            user_id=user_b.id,
            account_id=account_b.id,
            name="Beta Bot",
        )
        public_template_a = (
            build_template(
                user_id=user_a.id,
                name="Public Alpha Template",
                visibility="PUBLIC",
                status="PUBLISHED",
            )
        )
        private_template_a = (
            build_template(
                user_id=user_a.id,
                name="Private Alpha Template",
                visibility="PRIVATE",
                status="DRAFT",
            )
        )
        db.add_all([
            bot_a,
            bot_b,
            public_template_a,
            private_template_a,
        ])
        db.commit()
        db.refresh(bot_a)
        db.refresh(bot_b)
        db.refresh(public_template_a)
        db.refresh(private_template_a)
        subscription_b = (
            CopyTradingSubscription(
                follower_user_id=(
                    user_b.id
                ),
                source_template_id=(
                    public_template_a.id
                ),
                follower_bot_id=(
                    bot_b.id
                ),
                status="ACTIVE",
                execution_mode=(
                    "PAPER_ONLY"
                ),
                subscribed_template_version=1,
            )
        )
        db.add(subscription_b)
        db.commit()
        db.refresh(subscription_b)
        identifiers = SimpleNamespace(
            user_a=user_a.id,
            user_b=user_b.id,
            inactive_user=(
                inactive_user.id
            ),
            account_a=account_a.id,
            account_b=account_b.id,
            bot_a=bot_a.id,
            bot_b=bot_b.id,
            public_template_a=(
                public_template_a.id
            ),
            private_template_a=(
                private_template_a.id
            ),
            subscription_b=(
                subscription_b.id
            ),
        )
    tokens = SimpleNamespace(
        user_a=create_access_token(
            subject=str(
                identifiers.user_a
            )
        ),
        user_b=create_access_token(
            subject=str(
                identifiers.user_b
            )
        ),
        inactive=create_access_token(
            subject=str(
                identifiers.inactive_user
            )
        ),
    )
    context = SimpleNamespace(
        client=TestClient(app),
        identifiers=identifiers,
        tokens=tokens,
    )
    try:
        yield context
    finally:
        context.client.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(
            bind=engine
        )
        engine.dispose()
@pytest.mark.parametrize(
    (
        "path_template",
        "identifier_name",
        "token_name",
    ),
    [
        (
            (
                "/api/v1/"
                "exchange-accounts/{id}"
            ),
            "account_a",
            "user_b",
        ),
        (
            (
                "/api/v1/"
                "trading-bots/{id}"
            ),
            "bot_a",
            "user_b",
        ),
        (
            (
                "/api/v1/"
                "strategy-templates/{id}"
            ),
            "private_template_a",
            "user_b",
        ),
        (
            (
                "/api/v1/"
                "copy-trading/"
                "subscriptions/{id}"
            ),
            "subscription_b",
            "user_a",
        ),
    ],
)
def test_cross_user_resources_are_hidden(
    integration_context,
    path_template,
    identifier_name,
    token_name,
):
    identifier = getattr(
        integration_context.identifiers,
        identifier_name,
    )
    token = getattr(
        integration_context.tokens,
        token_name,
    )
    response = (
        integration_context.client.get(
            path_template.format(
                id=identifier
            ),
            headers=authorization(
                token
            ),
        )
    )
    assert response.status_code == 404
    assert (
        response.json()["success"]
        is False
    )
def test_exchange_account_response_hides_credentials(
    integration_context,
):
    response = (
        integration_context.client.get(
            (
                "/api/v1/"
                "exchange-accounts/"
                f"{integration_context.identifiers.account_a}"
            ),
            headers=authorization(
                integration_context
                .tokens
                .user_a
            ),
        )
    )
    assert response.status_code == 200
    data = response.json()["data"]
    forbidden_fields = {
        "api_key",
        "api_secret",
        "encrypted_api_key",
        "encrypted_api_secret",
    }
    assert not (
        forbidden_fields
        & set(data)
    )
    response_text = (
        response.text.lower()
    )
    assert (
        "encrypted-alpha-key"
        not in response_text
    )
    assert (
        "encrypted-alpha-secret"
        not in response_text
    )
def test_public_listing_excludes_private_templates(
    integration_context,
):
    response = (
        integration_context.client.get(
            (
                "/api/v1/"
                "strategy-templates/public"
            ),
            headers=authorization(
                integration_context
                .tokens
                .user_b
            ),
        )
    )
    assert response.status_code == 200
    returned_ids = {
        item["id"]
        for item
        in response.json()["data"]
    }
    assert (
        integration_context
        .identifiers
        .public_template_a
        in returned_ids
    )
    assert (
        integration_context
        .identifiers
        .private_template_a
        not in returned_ids
    )
def test_bot_creation_rejects_foreign_exchange_account(
    integration_context,
):
    response = (
        integration_context.client.post(
            "/api/v1/trading-bots",
            headers=authorization(
                integration_context
                .tokens
                .user_b
            ),
            json={
                "exchange_account_id": (
                    integration_context
                    .identifiers
                    .account_a
                ),
                "name": (
                    "Foreign Account Bot"
                ),
                "description": (
                    "Must not be created"
                ),
                "strategy_type": (
                    "RULE_BASED"
                ),
                "symbol": "BTCUSDT",
                "category": "linear",
                "timeframe": "5m",
                "paper_trading": True,
                "dry_run": True,
                (
                    "risk_per_trade_percent"
                ): 1.0,
                (
                    "max_position_value_usd"
                ): 25.0,
                (
                    "max_daily_loss_percent"
                ): 3.0,
                (
                    "max_drawdown_percent"
                ): 10.0,
                "strategy_config": (
                    RULE_CONFIG
                ),
            },
        )
    )
    assert response.status_code == 404
    assert (
        response.json()["message"]
        == "Exchange account not found"
    )
def test_subscription_rejects_foreign_follower_bot(
    integration_context,
):
    response = (
        integration_context.client.post(
            (
                "/api/v1/"
                "copy-trading/"
                "subscriptions"
            ),
            headers=authorization(
                integration_context
                .tokens
                .user_b
            ),
            json={
                "source_template_id": (
                    integration_context
                    .identifiers
                    .public_template_a
                ),
                "follower_bot_id": (
                    integration_context
                    .identifiers
                    .bot_a
                ),
            },
        )
    )
    assert response.status_code == 404
    assert (
        response.json()["message"]
        == "Follower trading bot not found"
    )
def test_inactive_user_token_is_forbidden(
    integration_context,
):
    response = (
        integration_context.client.get(
            "/api/v1/users/me",
            headers=authorization(
                integration_context
                .tokens
                .inactive
            ),
        )
    )
    assert response.status_code == 403
    assert (
        response.json()["message"]
        == "Inactive user"
    )
