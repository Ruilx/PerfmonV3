"""Registry for Source components."""

from src.base.source_base import SourceBase
from src.core.registry.base import RegistryBase


class SourceRegistry(RegistryBase[SourceBase]):
    def __init__(self):
        super().__init__(SourceBase)
