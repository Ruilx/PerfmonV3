"""Base contract for result sinks."""

from abc import ABC, abstractmethod
from typing import Any


class SinkBase(ABC):
    """Receives completed JobResult objects and decides when to submit them."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = dict(config or {})

    @abstractmethod
    def submit(self, result: Any) -> None:
        """Accept a result, possibly buffering it."""

    def flush(self) -> None:
        """Submit buffered results immediately."""

    def close(self) -> None:
        """Flush and release sink resources."""
        self.flush()
