"""Module for SQL database endpoint."""

import sqlalchemy as db

from dotenv import dotenv_values


values = dotenv_values("/home/martin/dev/afft/.env")


url: db.engine.URL = db.engine.URL.create(
    drivername="postgresql",
    database="acfr_auv_revisits",
    host="localhost",
    port=5432,
    username=values.get("PG_USER"),
    password=values.get("PG_PASSWORD"),
)

engine: db.Engine = db.create_engine(url)
