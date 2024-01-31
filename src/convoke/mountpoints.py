"""Tools for registering Base plugins"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Type


@dataclass
class Mountpoint:
    """A Mountpoint, subclassed, provides a place to register objects for a particular use.

    This registration collaborates with [`Base`][convoke.bases.Base].
    """

    mounted: list = field(default_factory=list)

    _mountpoints: ClassVar[list[Type[Mountpoint]]] = []

    def __init_subclass__(cls):
        cls._mountpoints.append(cls)
        cls.registry = []

    @classmethod
    def register(cls, func):
        """Register the given function for use with the mountpoint.

        This registration collaborates with [`Base`][convoke.bases.Base].
        """
        mp = getattr(func, "__mountpoints__", [])
        mp.append(cls)
        func.__mountpoints__ = mp
        return func

    def mount(self, func):
        """Mount a registered function on this instance."""
        self.mounted.append(func)


class MountpointDict(dict):
    """A dictionary that automates the mapping of a Mountpoint type to an instance."""

    def __missing__(self, key: Type[Mountpoint]):
        value = self[key] = key()
        return value
