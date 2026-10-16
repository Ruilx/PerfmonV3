import time
import unittest

from src.components.runners.value_runner import ValueRunner
from src.core.broker import Broker, WorkerState
from src.core.protocol import JobRequest
from src.core.registry.runner_registry import RunnerRegistry
from src.core.worker_handle import WorkerHandle
from src.core.workflow import StepDefinition, WorkflowDefinition
from src.core.workflow_executor import WorkflowExecutor


def build_broker_executor() -> WorkflowExecutor:
    runners = RunnerRegistry()
    runners.register_class("value", ValueRunner)
    workflow = WorkflowDefinition(
        name="broker-demo",
        steps=(StepDefinition("value", "value", {"value": "ok"}),),
    )
    return WorkflowExecutor({workflow.name: workflow}, runners)


class TestBroker(unittest.TestCase):
    def test_dispatches_pending_job_to_ready_worker(self):
        worker = WorkerHandle("broker-worker", build_broker_executor)
        broker = Broker()
        try:
            broker.register_worker(worker)
            job = JobRequest.create("broker-demo", "test-source")
            broker.submit(job)

            finished = None
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline and finished is None:
                for event in broker.poll(0.2):
                    if event.get("type") == "job_finished":
                        finished = event
                        break

            self.assertIsNotNone(finished)
            self.assertEqual(finished["job_id"], job.job_id)
            self.assertEqual(broker.workers[worker.worker_id].state, WorkerState.IDLE)
            self.assertNotIn(job.job_id, broker.running)
        finally:
            broker.close()
