"""Tests for the environment module."""

from pathlib import Path

import pytest

from pydantic import ValidationError

from afft.environment import load_environment

_VARIABLES: list[str] = [
    "PG_HOST",
    "PG_PORT",
    "PG_NAME",
    "PG_USERNAME",
    "PG_PASSWORD",
    "STORMGLASS_API_KEY",
    "SQUIDLE_API_TOKEN",
    "WORLDTIDES_API_KEY",
    "AFFT_CACHE_DIR",
    "AFFT_LOG_DIR",
    "AFFT_EXPORT_DIR",
]


@pytest.fixture(autouse=True)
def _clear_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear application variables so the process environment cannot leak in."""
    for variable in _VARIABLES:
        monkeypatch.delenv(variable, raising=False)


def _write_env(directory: Path, contents: str) -> Path:
    env_file: Path = directory / ".env"
    env_file.write_text(contents)
    return env_file


def test_load_full_environment(tmp_path: Path) -> None:
    env_file = _write_env(
        tmp_path,
        "PG_HOST=db.example.com\n"
        "PG_PORT=6543\n"
        "PG_NAME=sirius\n"
        "PG_USERNAME=martin\n"
        "PG_PASSWORD=secret\n"
        "STORMGLASS_API_KEY=storm\n"
        "SQUIDLE_API_TOKEN=squid\n"
        "WORLDTIDES_API_KEY=tide\n"
        "AFFT_CACHE_DIR=/data/cache\n"
        "AFFT_LOG_DIR=/data/logs\n"
        "AFFT_EXPORT_DIR=/data/export\n",
    )

    environment = load_environment(env_file)

    assert environment.database.host == "db.example.com"
    assert environment.database.port == 6543
    assert environment.database.name == "sirius"
    assert environment.database.username.get_secret_value() == "martin"
    assert environment.database.password.get_secret_value() == "secret"
    assert environment.tokens.stormglass is not None
    assert environment.tokens.stormglass.get_secret_value() == "storm"
    assert environment.tokens.squidle is not None
    assert environment.tokens.squidle.get_secret_value() == "squid"
    assert environment.tokens.worldtides is not None
    assert environment.tokens.worldtides.get_secret_value() == "tide"
    assert environment.directories.cache == Path("/data/cache")
    assert environment.directories.logs == Path("/data/logs")
    assert environment.directories.export == Path("/data/export")


def test_database_defaults_and_optional_fields(tmp_path: Path) -> None:
    env_file = _write_env(
        tmp_path,
        "PG_NAME=sirius\nPG_USERNAME=martin\nPG_PASSWORD=secret\n",
    )

    environment = load_environment(env_file)

    assert environment.database.host == "localhost"
    assert environment.database.port == 5432
    assert environment.tokens.stormglass is None
    assert environment.tokens.squidle is None
    assert environment.tokens.worldtides is None
    assert environment.directories.cache is None
    assert environment.directories.logs is None
    assert environment.directories.export is None


def test_port_coerced_to_int(tmp_path: Path) -> None:
    env_file = _write_env(
        tmp_path,
        "PG_PORT=7000\n"
        "PG_NAME=sirius\n"
        "PG_USERNAME=martin\n"
        "PG_PASSWORD=secret\n",
    )

    environment = load_environment(env_file)

    assert environment.database.port == 7000
    assert isinstance(environment.database.port, int)


def test_secret_is_masked_in_repr(tmp_path: Path) -> None:
    env_file = _write_env(
        tmp_path,
        "PG_NAME=sirius\nPG_USERNAME=martin\nPG_PASSWORD=secret\n",
    )

    environment = load_environment(env_file)

    assert "secret" not in repr(environment.database.password)
    assert "martin" not in repr(environment.database.username)


def test_missing_required_variable_raises(tmp_path: Path) -> None:
    env_file = _write_env(tmp_path, "PG_HOST=localhost\n")

    with pytest.raises(ValidationError):
        load_environment(env_file)
