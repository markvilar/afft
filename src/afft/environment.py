"""
Typed, validated access to the runtime environment.

Declares every environment variable the application reads as a field on a
settings model, and exposes load_environment() to build a validated
Environment from a .env file.
"""

from pathlib import Path

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentDatabase(BaseSettings):
    """
    Postgres connection settings.

    Attributes
    ----------
    host: Database server hostname.
    port: Database server port.
    name: Database name.
    username: Login username.
    password: Login password.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = Field("localhost", validation_alias="PG_HOST")
    port: int = Field(5432, validation_alias="PG_PORT")
    name: str = Field(validation_alias="PG_NAME")
    username: SecretStr = Field(validation_alias="PG_USERNAME")
    password: SecretStr = Field(validation_alias="PG_PASSWORD")


class EnvironmentApiTokens(BaseSettings):
    """
    Tokens for external APIs.

    Attributes
    ----------
    stormglass: Stormglass API token.
    squidle: Squidle+ API token.
    worldtides: WorldTides API token.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    stormglass: SecretStr | None = Field(
        None, validation_alias="STORMGLASS_API_KEY"
    )
    squidle: SecretStr | None = Field(
        None, validation_alias="SQUIDLE_API_TOKEN"
    )
    worldtides: SecretStr | None = Field(
        None, validation_alias="WORLDTIDES_API_KEY"
    )


class EnvironmentDirectories(BaseSettings):
    """
    Filesystem locations for application data.

    Attributes
    ----------
    cache: Directory for cached data.
    logs: Directory for log files.
    export: Directory for exported results.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cache: Path | None = Field(None, validation_alias="AFFT_CACHE_DIR")
    logs: Path | None = Field(None, validation_alias="AFFT_LOG_DIR")
    export: Path | None = Field(None, validation_alias="AFFT_EXPORT_DIR")


class Environment(BaseModel):
    """
    Application runtime environment.

    Attributes
    ----------
    database: Postgres connection settings.
    tokens: Tokens for external APIs.
    directories: Filesystem locations for application data.
    """

    database: EnvironmentDatabase
    tokens: EnvironmentApiTokens
    directories: EnvironmentDirectories


def load_environment(env_file: Path | str | None = None) -> Environment:
    """
    Load and validate the environment from a .env file.

    Arguments
    ---------
    env_file: Path to the .env file to read. When None, the default
        declared in each sub-model's model_config (".env") is used.

    Returns
    -------
    A validated Environment instance.
    """
    if env_file is None:
        return Environment(
            database=EnvironmentDatabase(),
            tokens=EnvironmentApiTokens(),
            directories=EnvironmentDirectories(),
        )
    return Environment(
        database=EnvironmentDatabase(_env_file=env_file),
        tokens=EnvironmentApiTokens(_env_file=env_file),
        directories=EnvironmentDirectories(_env_file=env_file),
    )
