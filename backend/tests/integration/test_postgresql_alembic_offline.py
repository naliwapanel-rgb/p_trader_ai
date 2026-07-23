from pathlib import Path
import os
import subprocess
import sys
def test_postgresql_migrations_compile_offline(
) -> None:
    environment = os.environ.copy()
    environment.update({
        "ENVIRONMENT": "development",
        "DATABASE_URL": (
            "postgresql+psycopg2://"
            "p_trader@localhost/"
            "p_trader_ai"
        ),
    })
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "upgrade",
            "head",
            "--sql",
        ],
        cwd=Path.cwd(),
        env=environment,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        result.stderr
    )
    assert "PostgresqlImpl" in result.stderr
    assert "CREATE TABLE" in result.stdout
    assert "13b0b1c2d3e4" in result.stdout
def test_initial_users_migration_generates_users_table():
    import os
    from pathlib import Path
    import subprocess
    import sys
    repository_root = (
        Path(__file__)
        .resolve()
        .parents[2]
    )
    environment = os.environ.copy()
    environment.update(
        {
            "ENVIRONMENT": "development",
            "DATABASE_URL": (
                "postgresql+psycopg2://"
                "test_user:test_password@"
                "127.0.0.1:5432/test_database"
            ),
        }
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "upgrade",
            "8b50466e15ae",
            "--sql",
        ],
        cwd=repository_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (
        result.stdout
        + "\n"
        + result.stderr
    )
    assert result.returncode == 0, output
    normalized_output = (
        output
        .lower()
        .replace('"', "")
    )
    assert (
        "create table users"
        in normalized_output
    )
    assert (
        "ix_users_email"
        in normalized_output
    )
    assert (
        "ix_users_id"
        in normalized_output
    )
def test_postgresql_trading_bot_boolean_defaults_are_portable():
    import os
    from pathlib import Path
    import re
    import subprocess
    import sys
    repository_root = (
        Path(__file__)
        .resolve()
        .parents[2]
    )
    environment = os.environ.copy()
    environment.update(
        {
            "ENVIRONMENT": "development",
            "DATABASE_URL": (
                "postgresql+psycopg2://"
                "test_user:test_password@"
                "127.0.0.1:5432/"
                "test_database"
            ),
        }
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "upgrade",
            "12a0b1c2d3e4",
            "--sql",
        ],
        cwd=repository_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (
        result.stdout
        + "\n"
        + result.stderr
    )
    assert result.returncode == 0, output
    normalized_output = (
        output
        .lower()
        .replace('"', "")
    )
    assert not re.search(
        r"\bboolean\s+default\s+[01]\b",
        normalized_output,
    )
    assert (
        normalized_output.count(
            "boolean default true"
        )
        >= 2
    )
