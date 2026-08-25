"""Checks a resolved pipeline against the bundle it is to run on. Callers
run these before `run_pipeline`, which does not validate for them."""

from collections.abc import Set

from .pipeline_types import Pipeline


def validate_pipeline(pipeline: Pipeline, available: Set[str]) -> None:
    """
    Check that every step's inputs are available when that step runs.

    Arguments
    ---------
    pipeline: The resolved steps, in run order.
    available: Keys present before the first step -- the input bundle's.

    An optional step is exempt: a missing input means the deployment does not
    carry that sensor, which the runner skips rather than fails. Its output is
    still counted as produced, since whether it runs is not known until then.

    Raises
    ------
    ValueError: If a required step names an input key that no earlier step
        produces and the input bundle does not hold.
    """
    produced: set[str] = set(available)
    for index, step in enumerate(pipeline):
        if step.optional:
            produced.add(step.output)
            continue
        for name, key in step.inputs.items():
            if key not in produced:
                raise ValueError(
                    f"step {index} ({step.processor_key}) reads {name}="
                    f"{key!r}, which the input bundle does not hold and no "
                    f"earlier step produces"
                )
        produced.add(step.output)
