from pathlib import Path


NGINX_TEMPLATE = Path(
    "nginx/templates/default.conf.template"
)
COMPOSE_FILE = Path(
    "compose.production.yml"
)
DOCKER_ENV_EXAMPLE = Path(
    ".env.docker.example"
)
CERT_GITIGNORE = Path(
    "nginx/certs/.gitignore"
)


def test_nginx_deployment_files_exist() -> None:
    assert NGINX_TEMPLATE.is_file()
    assert COMPOSE_FILE.is_file()
    assert DOCKER_ENV_EXAMPLE.is_file()
    assert CERT_GITIGNORE.is_file()


def test_http_redirects_to_https() -> None:
    config = NGINX_TEMPLATE.read_text(
        encoding="utf-8"
    )

    assert "listen 80;" in config
    assert "listen [::]:80;" in config
    assert (
        "return 301 "
        "https://$host$request_uri;"
        in config
    )
    assert config.count(
        "location = /nginx-health"
    ) == 2


def test_https_uses_secure_tls_configuration() -> None:
    config = NGINX_TEMPLATE.read_text(
        encoding="utf-8"
    )

    assert "listen 443 ssl;" in config
    assert "listen [::]:443 ssl;" in config
    assert "http2 on;" in config
    assert (
        "ssl_protocols TLSv1.2 TLSv1.3;"
        in config
    )
    assert (
        "ssl_certificate "
        "/etc/nginx/certs/fullchain.pem;"
        in config
    )
    assert (
        "ssl_certificate_key "
        "/etc/nginx/certs/privkey.pem;"
        in config
    )


def test_nginx_proxies_requests_to_backend() -> None:
    config = NGINX_TEMPLATE.read_text(
        encoding="utf-8"
    )

    assert "server backend:8000;" in config
    assert (
        "proxy_pass "
        "http://p_trader_backend;"
        in config
    )
    assert (
        "proxy_set_header "
        "X-Forwarded-Proto https;"
        in config
    )
    assert (
        "proxy_set_header "
        "X-Forwarded-For "
        "$proxy_add_x_forwarded_for;"
        in config
    )
    assert (
        "proxy_set_header "
        "Upgrade $http_upgrade;"
        in config
    )


def test_compose_defines_nginx_service() -> None:
    compose = COMPOSE_FILE.read_text(
        encoding="utf-8"
    )

    assert "  nginx:" in compose
    assert (
        "image: nginx:1.30.4-alpine"
        in compose
    )
    assert "condition: service_healthy" in compose
    assert (
        "./nginx/templates/"
        "default.conf.template:"
        "/etc/nginx/templates/"
        "default.conf.template:ro"
        in compose
    )
    assert (
        "./nginx/certs:"
        "/etc/nginx/certs:ro"
        in compose
    )
    assert (
        "${NGINX_HTTP_PORT:-80}:80"
        in compose
    )
    assert (
        "${NGINX_HTTPS_PORT:-443}:443"
        in compose
    )
    assert (
        "http://127.0.0.1/"
        "nginx-health"
        in compose
    )


def test_backend_is_not_published_to_host() -> None:
    compose = COMPOSE_FILE.read_text(
        encoding="utf-8"
    )
    backend_block = compose.split(
        "  backend:",
        maxsplit=1,
    )[1].split(
        "  nginx:",
        maxsplit=1,
    )[0]

    assert '    expose:\n      - "8000"' in backend_block
    assert "    ports:" not in backend_block


def test_nginx_environment_example_is_complete() -> None:
    env_example = (
        DOCKER_ENV_EXAMPLE.read_text(
            encoding="utf-8"
        )
    )

    assert "NGINX_SERVER_NAME=" in env_example
    assert "NGINX_BIND_ADDRESS=" in env_example
    assert "NGINX_HTTP_PORT=" in env_example
    assert "NGINX_HTTPS_PORT=" in env_example
    assert (
        "NGINX_CLIENT_MAX_BODY_SIZE="
        in env_example
    )
    assert "BACKEND_PORT=" not in env_example


def test_tls_certificates_are_git_ignored() -> None:
    rules = CERT_GITIGNORE.read_text(
        encoding="utf-8"
    ).splitlines()

    assert "*" in rules
    assert "!.gitignore" in rules
