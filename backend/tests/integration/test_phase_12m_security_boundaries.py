import ast
from pathlib import (
    Path,
)
from app.main import (
    app,
)
from app.models.copy_trading_subscription import (
    CopyTradingSubscription,
)
from app.models.strategy_template import (
    StrategyTemplate,
)
from app.schemas.exchange_account import (
    ExchangeAccountResponse,
)
ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)
def source_text(
    relative_path: str,
) -> str:
    return (
        ROOT
        .joinpath(relative_path)
        .read_text(
            encoding="utf-8-sig"
        )
        .replace("\r\n", "\n")
    )
def imported_modules(
    relative_path: str,
) -> set[str]:
    tree = ast.parse(
        source_text(relative_path)
    )
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(
            node,
            ast.Import,
        ):
            modules.update(
                alias.name
                for alias in node.names
            )
        if isinstance(
            node,
            ast.ImportFrom,
        ):
            if node.module:
                modules.add(
                    node.module
                )
    return modules
def test_copy_mirroring_has_no_live_exchange_imports():
    modules = imported_modules(
        (
            "app/services/"
            "copy_trading_decision_"
            "mirror_service.py"
        )
    )
    prohibited_prefixes = (
        "app.exchanges",
        (
            "app.services."
            "exchange_trading"
        ),
        (
            "app.services."
            "automation_trade_execution"
        ),
        (
            "app.services."
            "order_execution"
        ),
        (
            "app.services."
            "position_management"
        ),
    )
    violations = sorted(
        module
        for module in modules
        if module.startswith(
            prohibited_prefixes
        )
    )
    assert violations == []
def test_decision_mirroring_is_not_public_api():
    paths = {
        path.lower()
        for path in (
            app.openapi()["paths"]
        )
    }
    mirror_paths = sorted(
        path
        for path in paths
        if "mirror" in path
    )
    assert mirror_paths == []
def test_exchange_response_has_no_credentials():
    response_fields = set(
        ExchangeAccountResponse
        .model_fields
    )
    forbidden_fields = {
        "api_key",
        "api_secret",
        "encrypted_api_key",
        "encrypted_api_secret",
        "password",
        "access_token",
        "refresh_token",
    }
    assert not (
        response_fields
        & forbidden_fields
    )
def test_template_and_copy_models_store_no_credentials():
    template_columns = set(
        StrategyTemplate
        .__table__
        .columns
        .keys()
    )
    subscription_columns = set(
        CopyTradingSubscription
        .__table__
        .columns
        .keys()
    )
    forbidden_columns = {
        "api_key",
        "api_secret",
        "encrypted_api_key",
        "encrypted_api_secret",
        "password",
        "hashed_password",
        "access_token",
        "refresh_token",
        "balance",
        "available_balance",
    }
    assert not (
        template_columns
        & forbidden_columns
    )
    assert not (
        subscription_columns
        & forbidden_columns
    )
def test_request_logger_never_reads_sensitive_payloads():
    content = source_text(
        (
            "app/middleware/"
            "request_logger.py"
        )
    )
    prohibited = {
        "request.body(",
        "await request.json(",
        "dict(request.headers)",
        "request.headers.items(",
        "exc_info=True",
        "str(error)",
        "str(exc)",
    }
    violations = sorted(
        item
        for item in prohibited
        if item in content
    )
    assert violations == []
def test_security_and_recovery_are_wired_at_startup():
    main_source = source_text(
        "app/main.py"
    )
    session_source = source_text(
        "app/database/session.py"
    )
    required_main_markers = {
        "validate_runtime_security(",
        "DatabaseRecoveryService(",
        ".prepare_startup()",
        ".checkpoint()",
        ".restore_running_bots()",
    }
    for marker in (
        required_main_markers
    ):
        assert marker in main_source
    assert (
        "configure_sqlite_engine("
        in session_source
    )
def test_authentication_guards_remain_enabled():
    dependency_source = source_text(
        "app/api/dependencies.py"
    )
    websocket_source = source_text(
        (
            "app/api/"
            "websocket_dependencies.py"
        )
    )
    auth_service_source = source_text(
        "app/services/auth_service.py"
    )
    for content in (
        dependency_source,
        websocket_source,
    ):
        assert "int(subject)" in content
        assert "user_id <= 0" in content
        assert "Invalid token subject" in (
            content
        )
        assert "Inactive user" in content
    assert "Inactive user" in (
        auth_service_source
    )
