import unittest

from src.components.runners.value_runner import ValueRunner
from src.core.protocol import JobRequest
from src.core.registry.runner_registry import RunnerRegistry
from src.core.workflow import StepDefinition, WorkflowDefinition
from src.core.workflow_executor import WorkflowExecutor


class TestWorkflowExecutor(unittest.TestCase):
    def setUp(self):
        self.runners = RunnerRegistry()
        self.runners.register_class("value", ValueRunner)

    def test_runs_steps_in_order_and_preserves_runner_values(self):
        workflow = WorkflowDefinition(
            name="demo",
            steps=(
                StepDefinition(
                    name="number",
                    runner="value",
                    config={"value": 42},
                ),
                StepDefinition(
                    name="text",
                    runner="value",
                    config={"value": "done"},
                ),
            ),
        )
        executor = WorkflowExecutor({workflow.name: workflow}, self.runners)

        result = executor.execute(JobRequest.create("demo", "test-source"))

        self.assertEqual(result.status, "succeeded")
        self.assertEqual(result.value, "done")
        self.assertEqual(result.steps["number"].value, 42)
        self.assertEqual(result.steps["text"].value, "done")

    def test_stops_after_failed_step(self):
        workflow = WorkflowDefinition(
            name="demo",
            steps=(
                StepDefinition(
                    name="invalid",
                    runner="value",
                    config={},
                ),
                StepDefinition(name="never", runner="value", config={"value": "x"}),
            ),
        )
        executor = WorkflowExecutor({workflow.name: workflow}, self.runners)

        result = executor.execute(JobRequest.create("demo", "test-source"))

        self.assertEqual(result.status, "failed")
        self.assertIn("invalid", result.steps)
        self.assertNotIn("never", result.steps)
