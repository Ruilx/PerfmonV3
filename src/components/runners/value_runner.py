"""A small built-in Runner useful for configuration and protocol tests."""

from collections.abc import Mapping
from typing import Any

from src.base.runner_base import RunnerBase


class ValueRunner(RunnerBase):
    def run(self, params: Mapping[str, Any]) -> Any:
        if "value" not in self.config:
            raise ValueError("ValueRunner requires a 'value' configuration field.")
        return self.config["value"]
