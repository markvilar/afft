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
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run mypy .

# Build
uv build
```

All code must pass linting, formatting, type checking, and tests with no errors.

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

## Python Conventions

### Types

Always add type hints to return types, arguments, fields, and variables. Use the Python 3.12 `type` statement for type aliases:

```python
type WeightVector = np.ndarray
type ComponentIndex = int
```

### Strings

Use double quotes for all strings. Single quotes are acceptable inside f-strings to avoid escaping:

```python
label: str = "linear-regression"
message: str = f"component {component['name']} converged"
```

### Variable names

Prefer full words over abbreviations — use `message` not `msg`, `packet` not `pkt`, `result` not `res`, `error` not `err`, `config` not `cfg`. Three-character abbreviations are just as discouraged as one- or two-character ones. Exception: short or single-character names are acceptable for class member fields where the meaning is established by context (e.g. `x`, `y`, `z`, `w` on a quaternion dataclass).

### Imports

Group imports in the following order, separating `import ...` groups from `from ... import ...` groups with a blank line:

```python
import math
import os

import numpy as np
import pandas as pd

import mypackage

from typing import Sequence

from numpy.typing import NDArray

from mypackage.models import LinearModel, LogisticModel
from mypackage.utils import normalize
```

When importing multiple names from the same module, use parentheses with one name per line:

```python
from datetime import (
    date,
    datetime,
    timedelta,
)
```

Import classes and functions from the package, not from the module within it:

```python
# Preferred
from mypackage.models import LinearModel

# Avoid
from mypackage.models.linear import LinearModel
```

### Docstrings

Add a line of hyphens under `Arguments`, `Returns`, and `Attributes` section headers.

Function example:

```python
def fit(
    data: NDArray[np.float64],
    max_iter: int = 100,
    tol: float = 1e-6,
) -> LinearModel:
    """
    Fit a linear model to data.

    Arguments
    ---------
    data: Input array of shape (n, d).
    max_iter: Maximum number of iterations.
    tol: Convergence tolerance.

    Returns
    -------
    Fitted LinearModel.
    """
```

Class example:

```python
@dataclass
class LinearModel:
    """
    A simple linear model.

    Attributes
    ----------
    weights: Coefficient vector of shape (d,).
    bias: Scalar intercept term.
    """

    weights: NDArray[np.float64]
    bias: float
```

## Conventions

- Never reference Claude in commits, pull requests, source code, or documentation. This includes `Co-Authored-By` trailers, body text, or any other attribution to Claude or Anthropic.
- Use `` ` `` (backtick) for inline code and code blocks in GitHub issues and pull requests, not `` \` `` (escaped backtick).
