"""Validation policy for results before they reach a Sink."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from src.core.protocol import JobResult


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """The outcome of checking one completed job result."""

    accepted: bool
    retryable: bool = False
    message: str = ""


ValidationCheck = Callable[[JobResult], ValidationResult | bool]


class ResultValidator:
    """Apply a submission-time content check without changing the result."""

    def __init__(
        self,
        check: ValidationCheck | None = None,
        *,
        retryable_on_rejection: bool = False,
    ) -> None:
        self._check = check
        self._retryable_on_rejection = retryable_on_rejection

    def validate(self, result: JobResult) -> ValidationResult:
        if result.status != "succeeded":
            return ValidationResult(
                accepted=False,
                message="Only successful job results can be submitted.",
            )
        if self._check is None:
            return ValidationResult(accepted=True)

        try:
            outcome = self._check(result)
        except Exception as error:
            return ValidationResult(
                accepted=False,
                message=f"Result validation failed: {error}",
            )

        if isinstance(outcome, ValidationResult):
            return outcome
        if isinstance(outcome, bool):
            return ValidationResult(
                accepted=outcome,
                retryable=not outcome and self._retryable_on_rejection,
                message="" if outcome else "Result content was rejected.",
            )
        raise TypeError("Result validation checks must return bool or ValidationResult.")
