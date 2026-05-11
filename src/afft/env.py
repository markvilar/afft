"""Loads environment variables from the .env file into os.environ on import."""

from pathlib import Path

from dotenv import load_dotenv

_ENV_FILE: Path = Path(__file__).resolve().parents[2] / ".env"

load_dotenv(_ENV_FILE)
