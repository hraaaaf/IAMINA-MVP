"""
core.registry — ModuleRegistry

Append-only class-level registry for IAmina condition modules.
Each module (diabetes, hypertension, …) registers itself at Django startup
via its AppConfig.ready() method.

One-way dependency: core.registry must NOT import from any condition module.
The dependency arrow is always module → core.
"""
from dataclasses import dataclass

from ninja import Router

from core.contracts.manifest import ModuleManifest


@dataclass
class RegisteredModule:
    manifest: ModuleManifest
    engine_class: type
    router: Router


class ModuleRegistry:
    _modules: dict[str, RegisteredModule] = {}

    @classmethod
    def register(cls, manifest: ModuleManifest, engine_class: type, router: Router) -> None:
        """Register a condition module.  Calling twice with the same name overwrites silently."""
        cls._modules[manifest.name] = RegisteredModule(manifest, engine_class, router)

    @classmethod
    def get(cls, name: str) -> RegisteredModule:
        """Return the RegisteredModule for *name*.  Raises KeyError if not found."""
        return cls._modules[name]

    @classmethod
    def all(cls) -> list[RegisteredModule]:
        """Return all registered modules (insertion order preserved, Python 3.7+)."""
        return list(cls._modules.values())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        return name in cls._modules
