"""Module for SQL database endpoints."""

from typing import Optional

import sqlalchemy as db
import dotenv as env

from ...utils.result import Ok, Err, Result

Endpoint = db.Engine


USER_KEY: str = "DB_USER"
PASSWORD_KEY: str = "DB_PASSWORD"


def create_endpoint(
    database: str,
    host: str,
    port: int,
    drivername: str = "postgresql",
) -> Result[Endpoint, str]:
    """Creates a connection to a SQL database."""

    username: Optional[str] = env.dotenv_values().get(USER_KEY)
    password: Optional[str] = env.dotenv_values().get(PASSWORD_KEY)

    if not username:
        return Err(f"missing environment value: '{USER_KEY}'")
    if not password:
        return Err(f"missing environment value: '{PASSWORD_KEY}'")

    url: db.engine.URL = db.engine.URL.create(
        drivername=drivername,
        database=database,
        host=host,
        port=port,
        username=username,
        password=password,
    )

    return Ok(db.create_engine(url))
