"""Generic dynamic component registry."""

from __future__ import annotations

from typing import Generic, TypeVar

from src.core.component import ComponentSpec

ComponentType = TypeVar("ComponentType")


class RegistryError(ValueError):
    """Raised when a component registry operation is invalid."""


class RegistryBase(Generic[ComponentType]):
    def __init__(self, component_type: type[ComponentType]):
        self._component_type = component_type
        self._components: dict[str, ComponentSpec] = {}

    def register(self, name: str, component: ComponentSpec) -> None:
        if not name:
            raise RegistryError("Component name cannot be empty.")
        if name in self._components:
            raise RegistryError(f"Component '{name}' is already registered.")
        if not isinstance(component, ComponentSpec):
            raise TypeError("component must be a ComponentSpec.")
        component_class = component.load_class()
        if not issubclass(component_class, self._component_type):
            raise TypeError(
                f"Component '{name}' must inherit from {self._component_type.__name__}."
            )
        self._components[name] = component

    def register_class(self, name: str, component_class: type[ComponentType]) -> None:
        if not issubclass(component_class, self._component_type):
            raise TypeError(
                f"Component '{name}' must inherit from {self._component_type.__name__}."
            )
        self.register(name, ComponentSpec.from_class(name, component_class))

    def get_class(self, name: str) -> type[ComponentType]:
        try:
            return self._components[name].load_class()
        except KeyError as error:
            raise RegistryError(f"Component '{name}' is not registered.") from error

    def create(self, name: str, *args, **kwargs) -> ComponentType:
        return self.get_class(name)(*args, **kwargs)

    def has(self, name: str) -> bool:
        return name in self._components

    def names(self) -> tuple[str, ...]:
        return tuple(self._components)
