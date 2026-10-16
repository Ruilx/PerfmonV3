"""Serializable messages exchanged by Perfmon V3 components."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import uuid4


class ProtocolError(ValueError):
    """Raised when a protocol message is malformed."""


def _required_string(message: dict[str, Any], key: str) -> str:
    value = message.get(key)
    if not isinstance(value, str) or not value:
        raise ProtocolError(f"Message field '{key}' must be a non-empty string.")
    return value


@dataclass(frozen=True, slots=True)
class JobRequest:
    """A single request to execute a Workflow."""

    job_id: str
    workflow: str
    source: str
    params: dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    attempt: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.job_id or not self.workflow or not self.source:
            raise ValueError("job_id, workflow and source are required.")
        if self.attempt < 1:
            raise ValueError("attempt must be greater than zero.")
        object.__setattr__(self, "params", dict(self.params))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @classmethod
    def create(
        cls,
        workflow: str,
        source: str,
        params: dict[str, Any] | None = None,
        *,
        priority: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> "JobRequest":
        return cls(
            job_id=str(uuid4()),
            workflow=workflow,
            source=source,
            params=params or {},
            priority=priority,
            metadata=metadata or {},
        )

    def to_message(self) -> dict[str, Any]:
        return {
            "type": "job_request",
            "job_id": self.job_id,
            "workflow": self.workflow,
            "source": self.source,
            "params": dict(self.params),
            "priority": self.priority,
            "attempt": self.attempt,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_message(cls, message: dict[str, Any]) -> "JobRequest":
        if message.get("type") != "job_request":
            raise ProtocolError("Message type must be 'job_request'.")
        params = message.get("params", {})
        metadata = message.get("metadata", {})
        if not isinstance(params, dict) or not isinstance(metadata, dict):
            raise ProtocolError("params and metadata must be dictionaries.")
        return cls(
            job_id=_required_string(message, "job_id"),
            workflow=_required_string(message, "workflow"),
            source=_required_string(message, "source"),
            params=params,
            priority=message.get("priority", 0),
            attempt=message.get("attempt", 1),
            metadata=metadata,
        )


@dataclass(frozen=True, slots=True)
class ErrorInfo:
    type_name: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_exception(cls, error: Exception) -> "ErrorInfo":
        return cls(type(error).__name__, str(error), {"repr": repr(error)})

    def to_message(self) -> dict[str, Any]:
        return {
            "type": self.type_name,
            "message": self.message,
            "details": dict(self.details),
        }


@dataclass(frozen=True, slots=True)
class StepResult:
    step: str
    status: Literal["succeeded", "failed"]
    value: Any = None
    attempts: int = 1
    duration: float = 0.0
    error: ErrorInfo | None = None

    def to_message(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "status": self.status,
            "value": self.value,
            "attempts": self.attempts,
            "duration": self.duration,
            "error": self.error.to_message() if self.error else None,
        }


@dataclass(frozen=True, slots=True)
class JobResult:
    job_id: str
    workflow: str
    source: str
    status: Literal["succeeded", "failed"]
    value: Any = None
    steps: dict[str, StepResult] = field(default_factory=dict)
    error: ErrorInfo | None = None
    attempt: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_message(self) -> dict[str, Any]:
        return {
            "type": "job_result",
            "job_id": self.job_id,
            "workflow": self.workflow,
            "source": self.source,
            "status": self.status,
            "value": self.value,
            "steps": {name: result.to_message() for name, result in self.steps.items()},
            "error": self.error.to_message() if self.error else None,
            "attempt": self.attempt,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class WorkerEvent:
    event: Literal["worker_ready", "job_started", "job_finished", "job_failed", "worker_stopped"]
    worker_id: str
    job_id: str | None = None
    attempt: int | None = None
    result: JobResult | None = None
    error: ErrorInfo | None = None

    def to_message(self) -> dict[str, Any]:
        return {
            "type": self.event,
            "worker_id": self.worker_id,
            "job_id": self.job_id,
            "attempt": self.attempt,
            "result": self.result.to_message() if self.result else None,
            "error": self.error.to_message() if self.error else None,
        }
