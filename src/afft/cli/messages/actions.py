"""Actions for message processing CLI commands."""

from pathlib import Path

from afft.tasks.parse_messages import ParseMessageCommand, run_parse_messages


def dispatch_parse_messages(
    source: str | Path,
    config: str | Path,
    database: str | None = None,
    host: str | None = None,
    port: int | None = None,
    prefix: str | None = None,
    output_dir: str | Path | None = None,
) -> None:
    command = ParseMessageCommand(
        source_file=Path(source),
        config_file=Path(config),
        database=database,
        host=host,
        port=port,
        prefix=prefix,
        output_dir=Path(output_dir) if output_dir else None,
    )
    run_parse_messages(command)
