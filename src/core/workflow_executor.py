"""Execute a WorkflowDefinition for one JobRequest."""

from __future__ import annotations

from typing import Any

from src.core.protocol import ErrorInfo, JobRequest, JobResult
from src.core.registry.runner_registry import RunnerRegistry
from src.core.step_executor import StepExecutor
from src.core.workflow import WorkflowDefinition


class WorkflowExecutor:
    def __init__(
        self,
        workflows: dict[str, WorkflowDefinition],
        runners: RunnerRegistry,
        step_executor: StepExecutor | None = None,
    ):
        self.workflows = dict(workflows)
        self.runners = runners
        self.step_executor = step_executor or StepExecutor()

    def execute(self, job: JobRequest) -> JobResult:
        try:
            workflow = self.workflows[job.workflow]
        except KeyError:
            return JobResult(
                job_id=job.job_id,
                workflow=job.workflow,
                source=job.source,
                status="failed",
                error=ErrorInfo.from_exception(
                    ValueError(f"Workflow '{job.workflow}' is not registered.")
                ),
                attempt=job.attempt,
                metadata=job.metadata,
            )

        params: dict[str, Any] = dict(job.params)
        step_results = {}
        final_value: Any = None

        for step in workflow.steps:
            runner = self.runners.create(step.runner, config=step.config)
            try:
                result = self.step_executor.execute(step, runner, params)
            finally:
                runner.close()

            step_results[step.name] = result
            if result.status == "failed":
                return JobResult(
                    job_id=job.job_id,
                    workflow=job.workflow,
                    source=job.source,
                    status="failed",
                    value=final_value,
                    steps=step_results,
                    error=result.error,
                    attempt=job.attempt,
                    metadata=job.metadata,
                )

            final_value = result.value
            params["_value"] = final_value
            params.setdefault("_steps", {})[step.name] = result.value

        return JobResult(
            job_id=job.job_id,
            workflow=job.workflow,
            source=job.source,
            status="succeeded",
            value=final_value,
            steps=step_results,
            attempt=job.attempt,
            metadata=job.metadata,
        )
