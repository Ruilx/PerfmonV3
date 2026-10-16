import time
import unittest

from src.components.runners.value_runner import ValueRunner
from src.core.protocol import JobRequest
from src.core.registry.runner_registry import RunnerRegistry
from src.core.workflow import StepDefinition, WorkflowDefinition
from src.core.worker_handle import WorkerHandle
from src.core.workflow_executor import WorkflowExecutor


def build_test_executor() -> WorkflowExecutor:
    runners = RunnerRegistry()
    runners.register_class("value", ValueRunner)
    workflow = WorkflowDefinition(
        name="worker-demo",
        steps=(StepDefinition("value", "value", {"value": "ok"}),),
    )
    return WorkflowExecutor({workflow.name: workflow}, runners)


class TestWorkerHandle(unittest.TestCase):
    def test_worker_executes_job_over_dedicated_pipe(self):
        worker = WorkerHandle("worker-test", build_test_executor)
        try:
            worker.start()
            ready = self._wait_for_event(worker, "worker_ready")
            self.assertEqual(ready["worker_id"], "worker-test")

            job = JobRequest.create("worker-demo", "test-source")
            worker.send_job(job)

            started = self._wait_for_event(worker, "job_started")
            finished = self._wait_for_event(worker, "job_finished")
            self.assertEqual(started["job_id"], job.job_id)
            self.assertEqual(finished["job_id"], job.job_id)
            self.assertEqual(finished["result"]["value"], "ok")
        finally:
            worker.stop()
            worker.join(5)
            worker.close()

    @staticmethod
    def _wait_for_event(worker: WorkerHandle, expected_type: str) -> dict:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            event = worker.poll_event(0.2)
            if event is not None and event.get("type") == expected_type:
                return event
        raise AssertionError(f"Timed out waiting for {expected_type!r}.")
