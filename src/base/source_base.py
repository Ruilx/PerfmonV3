"""Base contract for task-producing sources."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from typing import Any

from src.core.protocol import JobRequest


class SourceBase(ABC):
    """A source discovers work and emits JobRequest objects."""

    def __init__(
        self,
        name: str,
        config: Mapping[str, Any] | None = None,
        emit_job: Callable[[JobRequest], None] | None = None,
    ):
        if not name:
            raise ValueError("Source name cannot be empty.")
        self.name = name
        self.config = dict(config or {})
        self._emit_job = emit_job

    def set_job_emitter(self, emit_job: Callable[[JobRequest], None]) -> None:
        self._emit_job = emit_job

    def emit_job(self, job: JobRequest) -> None:
        if self._emit_job is None:
            raise RuntimeError("Source has no JobRequest emitter.")
        self._emit_job(job)

    @abstractmethod
    def start(self) -> None:
        """Start source activity."""

    @abstractmethod
    def stop(self) -> None:
        """Stop source activity and release resources."""
