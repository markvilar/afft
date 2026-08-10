"""Execution of a resolved pipeline against a deployment bundle."""

from afft.deployment import DeploymentBundleIO, DeploymentBundleReader
from afft.utils.log import logger

from .pipeline_types import Pipeline


class PipelineStepError(RuntimeError):
    """Raised when a pipeline step fails, naming the step that failed."""


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
    verbose: Log each step's output key as it is written.

    A step marked optional is skipped when one of its input keys is absent,
    on the reading that the deployment does not carry that sensor. The skip
    is logged with the missing key, since a mistyped key looks the same.

    Raises
    ------
    PipelineStepError: If a step fails, naming the step and chaining the
        original error as its cause.
    """
    for key in source.list_frames():
        target.write_frame(key, source.read_frame(key))

    for index, step in enumerate(pipeline):
        missing: str | None = next(
            (key for key in step.inputs.values() if not target.has_frame(key)),
            None,
        )
        if step.optional and missing is not None:
            logger.info(
                f"pipeline step {index} ({step.processor_key}) skipped: "
                f"{missing} is not in the bundle"
            )
            continue

        try:
            frames = {
                name: target.read_frame(key)
                for name, key in step.inputs.items()
            }
            frame = step.processor(frames, step.config)
            target.write_frame(
                step.output,
                frame,
                if_exists=(
                    "replace" if target.has_frame(step.output) else "fail"
                ),
            )
            if verbose:
                logger.info(
                    f"pipeline step {index} ({step.processor_key}) wrote "
                    f"{step.output}"
                )
        except Exception as error:
            logger.error(
                f"pipeline step {index} ({step.processor_key}) failed: {error}"
            )
            raise PipelineStepError(
                f"step {index} ({step.processor_key} -> {step.output}) failed"
            ) from error
