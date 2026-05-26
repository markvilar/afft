# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AFFT (AUV File Formatting Tool) is a Python toolbox for working with data files from ACFR AUVs (Autonomous Underwater Vehicles), specifically the Sirius AUV. It handles message parsing, database ingestion, metocean data integration, and filesystem operations.

## Commands

```bash
# Install (development)
uv sync --all-extras --dev

# Run tests
uv run pytest

# Run a single test file
uv run pytest tests/test_logger.py

# Lint
uv run ruff check

# Format
uv run ruff format

# Build
uv build
```

Line length is 80 characters (configured in `pyproject.toml` via ruff).

## Architecture

The main package is at `src/afft/` with these modules:

- **`cli/`** — Click-based CLI. `entrypoint.py` composes two groups: `database_cli.py` (table operations) and `message_cli.py` (message parsing/ingestion).
- **`sirius/`** — Protocol parsing for Sirius AUV messages. `message_protocol.py` drives parsing; `message_parsers.py` contains concrete parser implementations; `message_interfaces.py` defines the abstract contracts.
- **`database/`** — PostgreSQL via SQLAlchemy. `engine.py` manages connections; `readers.py` and `writers.py` handle table I/O.
- **`metocean/`** — External API clients for sea level (WorldTides), solar irradiance, and solar zenith data (Stormglass).
- **`filesystem/`** — Directory search and file query utilities.
- **`io/`** — File line I/O and TOML config read/write.
- **`tasks/`** — Composed task implementations (database joins, renav processing, deployment file transfer).
- **`utils/`** — Shared helpers: Loguru logging (`log.py`), environment variables (`env.py`), time utilities (`time.py`).

## Configuration & Environment

- `.env` — PostgreSQL credentials (`PG_USERNAME`, `PG_PASSWORD`) and external API keys (StormGlass, WorldTides).
- `config/default.toml` — Default runtime configuration.

## Notebooks

`notebooks/` contains Jupyter notebooks demonstrating data workflows, organized into subdirectories by data type.

## Conventions

- Never reference Claude in commits, pull requests, source code, or documentation.
