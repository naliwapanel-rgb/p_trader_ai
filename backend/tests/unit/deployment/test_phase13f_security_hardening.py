from pathlib import Path

from app.core.config import Settings


ROOT = Path(".")

MAIN_FILE = ROOT / "app/main.py"
RUNTIME_FILE = ROOT / "app/core/security/runtime.py"
PRODUCTION_ENV = ROOT / ".env.production.example"
DOCKER_ENV = ROOT / ".env.docker.example"
COMPOSE_FILE = ROOT / "compose.production.yml"
DOCKERFILE = ROOT / "Dockerfile"
NGINX_TEMPLATE = (
    ROOT
    / "nginx/templates/default.conf.template"
)


def read(path: Path) -> str:
    return path.read_text(
        encoding="utf-8"
    )


def test_trusted_hosts_are_normalized():
    settings = Settings(
        _env_file=None,
        trusted_hosts=[
            " API.Example.com. ",
            "api.example.com",
            "",
        ],
    )

    assert settings.trusted_hosts == [
        "api.example.com",
    ]


def test_fastapi_security_controls_are_wired():
    source = read(MAIN_FILE)

    assert "TrustedHostMiddleware" in source
    assert (
        "allowed_hosts=settings.trusted_hosts"
        in source
    )
    assert "www_redirect=False" in source
    assert (
        "security_headers_middleware"
        in source
    )
    assert (
        "if settings.api_docs_enabled"
        in source
    )


def test_runtime_requires_hardened_security():
    source = read(RUNTIME_FILE)

    assert (
        "Wildcard trusted hosts are not"
        in source
    )
    assert (
        "Security headers must be enabled"
        in source
    )
    assert (
        "disabled in hardened environments"
        in source
    )


def test_production_environment_is_hardened():
    content = read(PRODUCTION_ENV)

    assert (
        'TRUSTED_HOSTS='
        '["api.example.com","127.0.0.1"]'
        in content
    )
    assert "API_DOCS_ENABLED=false" in content
    assert (
        "SECURITY_HEADERS_ENABLED=true"
        in content
    )


def test_docker_environment_is_hardened():
    content = read(DOCKER_ENV)

    assert "TRUSTED_HOSTS=" in content
    assert "API_DOCS_ENABLED=false" in content
    assert (
        "SECURITY_HEADERS_ENABLED=true"
        in content
    )


def test_backend_container_is_restricted():
    compose = read(COMPOSE_FILE)

    backend = compose.split(
        "  backend:",
        maxsplit=1,
    )[1].split(
        "  nginx:",
        maxsplit=1,
    )[0]

    assert (
        "image: "
        "p-trader-ai-backend:phase-13f"
        in backend
    )
    assert "    read_only: true" in backend
    assert (
        "      - no-new-privileges:true"
        in backend
    )
    assert "    cap_drop:" in backend
    assert "      - ALL" in backend
    assert (
        "/tmp:size=64m,mode=1777"
        in backend
    )


def test_security_environment_reaches_backend():
    compose = read(COMPOSE_FILE)

    assert (
        "TRUSTED_HOSTS="
        "${TRUSTED_HOSTS:?required}"
        in compose
    )
    assert (
        "API_DOCS_ENABLED="
        "${API_DOCS_ENABLED:?required}"
        in compose
    )
    assert (
        "SECURITY_HEADERS_ENABLED="
        "${SECURITY_HEADERS_ENABLED:?required}"
        in compose
    )


def test_database_network_is_internal():
    compose = read(COMPOSE_FILE)

    assert "  application_net:" in compose
    assert "  database_net:" in compose
    assert "    internal: true" in compose

    postgres = compose.split(
        "  postgres:",
        maxsplit=1,
    )[1].split(
        "  backend:",
        maxsplit=1,
    )[0]

    nginx = compose.split(
        "  nginx:",
        maxsplit=1,
    )[1].split(
        "\nnetworks:",
        maxsplit=1,
    )[0]

    assert "      - database_net" in postgres
    assert "application_net" not in postgres
    assert "      - application_net" in nginx
    assert "database_net" not in nginx


def test_uvicorn_server_header_is_disabled():
    content = read(DOCKERFILE)

    assert "--no-server-header" in content
    assert "USER app" in content


def test_nginx_suppresses_version_information():
    config = read(NGINX_TEMPLATE)

    assert config.count(
        "server_tokens off;"
    ) == 2
    assert (
        "proxy_hide_header Server;"
        in config
    )
    assert (
        "proxy_hide_header X-Powered-By;"
        in config
    )
    assert (
        "ssl_protocols TLSv1.2 TLSv1.3;"
        in config
    )
