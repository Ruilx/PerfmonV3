"""Common execution policy for one workflow step."""

from __future__ import annotations

from collections.abc import Mapping
from time import monotonic
from typing import Any

from src.base.runner_base import RunnerBase
from src.core.protocol import ErrorInfo, StepResult
from src.core.workflow import StepDefinition


class StepExecutor:
    def execute(
        self,
        step: StepDefinition,
        runner: RunnerBase,
        params: Mapping[str, Any],
    ) -> StepResult:
        started = monotonic()
        last_error: ErrorInfo | None = None

        for attempt in range(1, step.retries + 2):
            try:
                value = runner.run(dict(params))
                duration = monotonic() - started
                if step.timeout is not None and duration > step.timeout:
                    raise TimeoutError(
                        f"Step '{step.name}' exceeded timeout of {step.timeout} seconds."
                    )
                return StepResult(step.name, "succeeded", value, attempt, duration)
            except Exception as error:
                last_error = ErrorInfo.from_exception(error)

        return StepResult(
            step=step.name,
            status="failed",
            attempts=step.retries + 1,
            duration=monotonic() - started,
            error=last_error,
        )
