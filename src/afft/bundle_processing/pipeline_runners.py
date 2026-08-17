"""Execution of a resolved pipeline against a deployment bundle."""

from dataclasses import dataclass
from typing import Literal

import geopandas as gpd

from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table

from afft.deployment import DeploymentBundleIO, DeploymentBundleReader
from afft.utils.log import suppress_console_logging

from .pipeline_types import Pipeline, PipelineFrame

type StepStatus = Literal["ok", "skipped", "failed"]

_STATUS_STYLES: dict[StepStatus, str] = {
    "ok": "green",
    "skipped": "yellow",
    "failed": "red",
}


class PipelineStepError(RuntimeError):
    """Raised when a pipeline step fails, naming the step that failed."""


@dataclass(slots=True, frozen=True)
class StepReport:
    """
    One pipeline step's outcome, as shown in the run's summary table.

    Attributes
    ----------
    index: The step's position in the pipeline.
    processor_key: Registered name of the step's processor.
    output: Bundle key the step writes to.
    status: Whether the step wrote its output, was skipped, or failed.
    message: Detail for a non-``"ok"`` status; empty for ``"ok"``.
    """

    index: int
    processor_key: str
    output: str
    status: StepStatus
    message: str = ""


def run_pipeline(
    pipeline: Pipeline,
    source: DeploymentBundleReader,
    target: DeploymentBundleIO,
    verbose: bool = False,
) -> None:
    """
    Seed `target` from `source`, then run each step against `target`.

    Arguments
    ---------
    pipeline: The resolved steps, run in order.
    source: Bundle the run starts from; read only, never written.
    target: Bundle the run produces; both the destination of every step and
        the source of every step's inputs.
    verbose: Note each successfully written step's output key in the
        summary table, rather than leaving it blank.

    A step marked optional is skipped when one of its input keys is absent,
    on the reading that the deployment does not carry that sensor.

    Progress across the pipeline's steps is shown on a progress bar, its
    description naming the running step's index and processor. Per-step
    detail (skips, writes, failures) is not logged as it happens, since that
    breaks up the bar's rendering -- it is instead collected and printed as
    a summary table once the run finishes (or stops at a failure). Console
    logging is also suppressed for the run's duration, since a processor
    logging something of its own (e.g. while reading extrinsics) would
    corrupt the bar's rendering the same way; those lines still reach the
    log file, just not the console.

    Raises
    ------
    PipelineStepError: If a step fails, naming the step and chaining the
        original error as its cause.
    """
    for key, seed_frame in source.iter_frames():
        target.write_frame(key, seed_frame)
    for key, seed_geoframe in source.iter_geoframes():
        target.write_geoframe(key, seed_geoframe)

    console: Console = Console()
    reports: list[StepReport] = []

    try:
        with (
            suppress_console_logging(),
            Progress(
                console=console, disable=not console.is_terminal
            ) as progress,
        ):
            task: TaskID = progress.add_task(
                "Pipeline steps", total=len(pipeline)
            )

            for index, step in enumerate(pipeline):
                progress.update(
                    task, description=f"Step {index} - {step.processor_key}"
                )

                missing: str | None = next(
                    (
                        key
                        for key in step.inputs.values()
                        if not target.has_frame(key)
                    ),
                    None,
                )
                if step.optional and missing is not None:
                    reports.append(
                        StepReport(
                            index,
                            step.processor_key,
                            step.output,
                            "skipped",
                            f"{missing} is not in the bundle",
                        )
                    )
                    progress.advance(task)
                    continue

                try:
                    step_geoframe_keys = set(target.list_geoframes())
                    frames: dict[str, PipelineFrame] = {
                        name: (
                            target.read_geoframe(key)
                            if key in step_geoframe_keys
                            else target.read_frame(key)
                        )
                        for name, key in step.inputs.items()
                    }
                    frame: PipelineFrame = step.processor(frames, step.config)
                    if_exists: Literal["fail", "replace"] = (
                        "replace" if target.has_frame(step.output) else "fail"
                    )
                    match frame:
                        case gpd.GeoDataFrame():
                            target.write_geoframe(
                                step.output, frame, if_exists=if_exists
                            )
                        case _:
                            target.write_frame(
                                step.output, frame, if_exists=if_exists
                            )
                except Exception as error:
                    reports.append(
                        StepReport(
                            index,
                            step.processor_key,
                            step.output,
                            "failed",
                            str(error),
                        )
                    )
                    raise PipelineStepError(
                        f"step {index} ({step.processor_key} -> "
                        f"{step.output}) failed"
                    ) from error

                reports.append(
                    StepReport(
                        index,
                        step.processor_key,
                        step.output,
                        "ok",
                        f"wrote {step.output}" if verbose else "",
                    )
                )
                progress.advance(task)
    finally:
        _print_step_reports(console, reports)


def _print_step_reports(console: Console, reports: list[StepReport]) -> None:
    """
    Print `reports` as a table summarizing the run's steps.

    Bundle keys and processor names routinely run longer than a column's
    fair share of console width, so the Processor, Output, and Message
    columns wrap onto extra lines (``overflow="fold"``) rather than
    ellipsizing -- the point of the table is to show that detail, not hide
    it.
    """
    table = Table(title="Pipeline Run Summary")
    table.add_column("Step", justify="right")
    table.add_column("Processor", overflow="fold")
    table.add_column("Output", overflow="fold")
    table.add_column("Status")
    table.add_column("Message", overflow="fold")

    for report in reports:
        style = _STATUS_STYLES[report.status]
        table.add_row(
            str(report.index),
            report.processor_key,
            report.output,
            f"[{style}]{report.status}[/{style}]",
            report.message,
        )

    console.print(table)
