"""Workflow and Step definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class StepDefinition:
    name: str
    runner: str
    config: dict[str, Any] = field(default_factory=dict)
    timeout: float | None = None
    retries: int = 0

    def __post_init__(self) -> None:
        if not self.name or not self.runner:
            raise ValueError("Step name and runner are required.")
        if self.timeout is not None and self.timeout <= 0:
            raise ValueError("Step timeout must be greater than zero.")
        if self.retries < 0:
            raise ValueError("Step retries cannot be negative.")
        object.__setattr__(self, "config", dict(self.config))


@dataclass(frozen=True, slots=True)
class WorkflowDefinition:
    name: str
    steps: tuple[StepDefinition, ...]
    reenterable: bool = False
    kind: str = "default"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Workflow name cannot be empty.")
        if not self.steps:
            raise ValueError("Workflow must contain at least one step.")
        object.__setattr__(self, "steps", tuple(self.steps))
        object.__setattr__(self, "metadata", dict(self.metadata))
