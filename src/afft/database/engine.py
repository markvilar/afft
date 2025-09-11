"""Module for SQL database endpoints."""

import sqlalchemy as sqla


Engine = sqla.Engine


USER_KEY: str = "DB_USER"
PASSWORD_KEY: str = "DB_PASSWORD"


def create_engine(
    database: str,
    host: str,
    port: int,
    username: str,
    password: str,
    drivername: str = "postgresql",
) -> Engine | str:
    """Creates an engine for a SQL database."""

    url: sqla.engine.URL = sqla.engine.URL.create(
        database=database,
        host=host,
        port=port,
        username=username,
        password=password,
        drivername="postgresql",
    )

    return sqla.create_engine(url)
