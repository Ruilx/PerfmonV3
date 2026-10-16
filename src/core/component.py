"""Description and loading of a component class."""

from __future__ import annotations

import importlib
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ComponentSpec:
    name: str
    module_path: str
    class_name: str

    @classmethod
    def from_class(cls, name: str, component_class: type) -> "ComponentSpec":
        return cls(name, component_class.__module__, component_class.__qualname__)

    def load_class(self) -> type:
        if not self.module_path or not self.class_name:
            raise ValueError("ComponentSpec requires module_path and class_name.")
        module = importlib.import_module(self.module_path)
        component_class = module
        for part in self.class_name.split("."):
            component_class = getattr(component_class, part)
        if not isinstance(component_class, type):
            raise TypeError(f"Component '{self.name}' does not resolve to a class.")
        return component_class

    def create(self, *args, **kwargs):
        return self.load_class()(*args, **kwargs)


# Import-level alias for modules that still use the shorter name.
Component = ComponentSpec
