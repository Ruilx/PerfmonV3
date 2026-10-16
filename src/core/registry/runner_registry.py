"""Registry for Runner components."""

from src.base.runner_base import RunnerBase
from src.core.registry.base import RegistryBase


class RunnerRegistry(RegistryBase[RunnerBase]):
    def __init__(self):
        super().__init__(RunnerBase)
