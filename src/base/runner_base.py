"""Base contract for workflow steps."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class RunnerBase(ABC):
    """A component that performs one workflow step."""

    def __init__(self, config: Mapping[str, Any] | None = None):
        self.config = dict(config or {})

    @abstractmethod
    def run(self, params: Mapping[str, Any]) -> Any:
        """Return the final value produced by this step."""

    def close(self) -> None:
        """Release resources held by the runner."""
