"""Registry for Sink components."""

from src.base.sink_base import SinkBase
from src.core.registry.base import RegistryBase


class SinkRegistry(RegistryBase[SinkBase]):
    def __init__(self):
        super().__init__(SinkBase)
