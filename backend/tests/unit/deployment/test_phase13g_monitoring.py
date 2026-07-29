from pathlib import Path


ROOT = Path(".")

MAIN_FILE = ROOT / "app/main.py"
DOCKERFILE = ROOT / "Dockerfile"
COMPOSE_FILE = ROOT / "compose.production.yml"
NGINX_TEMPLATE = (
    ROOT
    / "nginx/templates/default.conf.template"
)
REQUIREMENTS = (
    ROOT
    / "requirements.production.txt"
)
DEVELOPMENT_ENV = ROOT / ".env.example"
PRODUCTION_ENV = (
    ROOT / ".env.production.example"
)
DOCKER_ENV = ROOT / ".env.docker.example"


def read(path: Path) -> str:
    return path.read_text(
        encoding="utf-8"
    )


def test_monitoring_dependency_is_in_production():
    requirements = read(REQUIREMENTS)

    assert (
        "prometheus_client==0.23.1"
        in requirements
    )


def test_development_monitoring_defaults_are_safe():
    content = read(DEVELOPMENT_ENV)

    assert "METRICS_ENABLED=false" in content
    assert "LOG_JSON_ENABLED=false" in content
    assert "LOG_LEVEL=INFO" in content
    assert "API_DOCS_ENABLED=true" in content
    assert (
        "SECURITY_HEADERS_ENABLED=false"
        in content
    )


def test_production_monitoring_is_enabled():
    for path in (
        PRODUCTION_ENV,
        DOCKER_ENV,
    ):
        content = read(path)

        assert (
            "METRICS_ENABLED=true"
            in content
        )
        assert (
            "LOG_JSON_ENABLED=true"
            in content
        )
        assert "LOG_LEVEL=INFO" in content


def test_application_wires_monitoring():
    source = read(MAIN_FILE)

    assert "configure_logging(" in source
    assert "metrics_middleware" in source
    assert (
        "if settings.metrics_enabled"
        in source
    )


def test_backend_image_uses_phase13g():
    compose = read(COMPOSE_FILE)

    assert (
        "image: "
        "p-trader-ai-backend:phase-13g"
        in compose
    )


def test_compose_passes_monitoring_settings():
    compose = read(COMPOSE_FILE)

    assert (
        "METRICS_ENABLED="
        "${METRICS_ENABLED:?required}"
        in compose
    )
    assert (
        "LOG_JSON_ENABLED="
        "${LOG_JSON_ENABLED:?required}"
        in compose
    )
    assert (
        "LOG_LEVEL=${LOG_LEVEL:-INFO}"
        in compose
    )


def test_container_logs_are_rotated():
    compose = read(COMPOSE_FILE)

    assert (
        "x-logging: &default-logging"
        in compose
    )
    assert (
        "logging: *default-logging"
        in compose
    )
    assert 'max-size: "10m"' in compose
    assert 'max-file: "5"' in compose


def test_backend_healthcheck_uses_liveness():
    dockerfile = read(DOCKERFILE)

    assert (
        "/api/v1/live"
        in dockerfile
    )
    assert (
        "/api/v1/health"
        not in dockerfile
    )


def test_duplicate_uvicorn_access_log_is_disabled():
    dockerfile = read(DOCKERFILE)

    assert "--no-access-log" in dockerfile


def test_public_nginx_blocks_metrics_endpoint():
    config = read(NGINX_TEMPLATE)

    assert (
        "location = /api/v1/metrics"
        in config
    )
    assert "return 404;" in config
    assert (
        "proxy_pass "
        "http://p_trader_backend;"
        in config
    )
