import unittest

from src.core.protocol import JobRequest, JobResult
from src.core.result_validation import ResultValidator, ValidationResult


def successful_result(value):
    request = JobRequest.create("demo", "test-source")
    return JobResult(
        job_id=request.job_id,
        workflow=request.workflow,
        source=request.source,
        status="succeeded",
        value=value,
    )


class TestResultValidator(unittest.TestCase):
    def test_accepts_successful_result_without_custom_check(self):
        outcome = ResultValidator().validate(successful_result({"value": 1}))

        self.assertEqual(outcome, ValidationResult(accepted=True))

    def test_check_can_request_retry(self):
        validator = ResultValidator(
            lambda result: ValidationResult(
                accepted=False,
                retryable=True,
                message=f"unexpected value: {result.value!r}",
            )
        )

        outcome = validator.validate(successful_result("bad"))

        self.assertFalse(outcome.accepted)
        self.assertTrue(outcome.retryable)
        self.assertIn("unexpected value", outcome.message)
