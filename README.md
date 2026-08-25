# AUV File Formatting Tool

![build-ubuntu](https://github.com/markvilar/afft/actions/workflows/build-ubuntu.yml/badge.svg)
![license](https://img.shields.io/badge/license-GPLv3-blue.svg)
![python](https://img.shields.io/badge/python-3.12%2B-blue.svg)

Afft is a collection of tools for working with data from ACFRs AUVs. The
tools consist of creating file queries from metadata, transferring files and 
directories, and parsing various data files. The repository includes support 
for the following tools:

The repository includes support for the following tools:
* poetry - package management and build system
* pytest - unit tests


## Getting started

### Prerequisites

- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — used for dependency management and running the tool

### Installation

Clone the repository and install the package with all extras in development mode:

```bash
git clone https://github.com/markvilar/afft.git
cd afft
uv sync --all-extras --dev
```

The `afft` command is then available via `uv run`:

```bash
uv run afft --help
```

### Environment

Create a `.env` file at the root of the repository with your credentials and API keys. This file must not be committed to version control — confirm that `.env` is listed in `.gitignore`.

```text
# PostgreSQL credentials (required for database commands)
PG_USERNAME=YOUR_POSTGRES_USER
PG_PASSWORD=YOUR_POSTGRES_PASSWORD
```

## CLI Commands

### `afft database` — Database operations

| Command | Description |
|---|---|
| `afft database table-export DATABASE HOST PORT OUTPUT_DIR` | Export database tables to CSV files |
| `afft database table-write SOURCE DATABASE HOST PORT` | Write a single CSV file to a database table |

Run any command with `--help` to see its full options.

