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
| `afft database table-ingest DATABASE HOST PORT SOURCE_DIR` | Ingest CSV files from a directory as database tables |
| `afft database table-join DATABASE HOST PORT CONFIG_PATH` | Join tables in the database using a config file |
| `afft database table-write SOURCE DATABASE HOST PORT` | Write a single CSV file to a database table |

### `afft messages` — Message processing

| Command | Description |
|---|---|
| `afft messages parse-messages SOURCE_DIR OUTPUT_DIR` | Parse Sirius AUV message files and write results |

### `afft tasks` — Data processing tasks

| Command | Description |
|---|---|
| `afft tasks clip-tables SOURCE_DIR OUTPUT_DIR --start YYYYMMDD_HHmmSS --end YYYYMMDD_HHmmSS` | Clip CSV files to a time interval |
| `afft tasks correct-pressure-tide READING_FILE SEALEVEL_FILE OUTPUT_FILE` | Tide-correct pressure sensor depth readings |

Run any command with `--help` to see its full options.

