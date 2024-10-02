# Afft - AUV File Formatting Tool

![ci](https://github.com/markvilar/raft/actions/workflows/ci.yml/badge.svg)
![pylint](https://github.com/markvilar/raft/actions/workflows/pylint.yml/badge.svg)

Raft is a collection of tools for working with data from ACFRs AUVs. The
tools consist of creating file queries from metadata, transferring files and 
directories, and parsing various data files. The repository includes support 
for the following tools:

The repository includes support for the following tools:
* poetry - package management and build system
* pytest - unit tests


## Getting started

### Install poetry

```shell
# Install pipenv
pip3 install --user poetry
```

### Configure the project environment and install dependencies

```shell
# Set the Python version 3.12
poetry env use 3.12

# Validate the environment configuration
poetry env info
```

```shell
# Install dependencies
poetry install

# Build the project
poetry build
```

## Tasks

### Message parsing and database ingestion

In order to use the AFFTs database ingestion tools, you first need to install
Postgres on your computer, for instance by following this [guide](https://www.devart.com/dbforge/postgresql/how-to-install-postgresql-on-linux/). 

To ease interactions with Postgres databases we highly recommend installing PgAdmin. PgAdmin is specifically designed for managing Postgres databases, and lets you create, delete, and inspect database through a graphical user interface. To get started with PgAdmin please refer to the following [guide](https://www.pgadmin.org/docs/pgadmin4/8.11/getting_started.html#).

To give AFFT access to your Postgres database, create a `.env` file at the root of the repository, and enter the login credentials of your Postgres user as seen below. Make sure that `.env` is added to the `.gitignore` so that it is not committed to `git` and pushed to a remote repository!

```text
PG_USER=YOUR_POSTGRES_USER
PG_PASSWORD=YOUR_POSTGRES_PASSWORD
```


## Other uses

### Running unit tests

```shell
poetry run pytest
```

### Running notebooks

```shell
poetry run jupyter notebook
```

### Managing the project environment

```shell
poetry env info
```

```shell
poetry env remove
```

### Activate the project environment in a shell

```shell
poetry shell
```

### Removing dependencies

```shell
poetry remove <package>
```
