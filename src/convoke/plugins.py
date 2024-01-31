"""Simple metaclasses for plugin management"""
from __future__ import annotations

from abc import ABCMeta
from contextlib import contextmanager
from weakref import WeakSet, WeakValueDictionary


class ABCPluginMount(ABCMeta):
    """Metaclass that allows abstract base classes to keep track of concrete subclasses

    The abstract base class maintains a registry of subclasses in
    `cls.plugins` and `cls.plugins_by_name`.

    Use this in the same way you would use `abc.ABCMeta`:

        class AbstractMyClass(metaclass=ABCPluginMount):
            ...

        class MyCoolSubclass(AbstractMyClass):
            ...

        assert MyCoolSubclass in AbstractMyClass.plugins
        assert 'MyCoolSubclass' in AbstractMyClass.plugins_by_name

    Notably, the registry uses weak references to allow for ephemeral plugins.

    This simple plugin framework is based on a simple proposal by Marty Alchin:

    https://web.archive.org/web/20220506163033/http://martyalchin.com/2008/jan/10/simple-plugin-framework/

    """

    plugins: WeakSet[ABCPluginMount]
    plugins_by_name: WeakValueDictionary[str, ABCPluginMount]

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        if not hasattr(cls, "plugins"):
            # This branch only executes when processing the mount point itself.
            # So, since this is a new plugin type, not an implementation, this
            # class shouldn't be registered as a plugin. Instead, it sets up a
            # list where plugins can be registered later.
            cls.plugins = WeakSet()
            cls.plugins_by_name = WeakValueDictionary()
        else:
            # This must be a plugin implementation, which should be registered.
            # Simply appending it to the list is all that's needed to keep
            # track of it later.
            cls.plugins.add(cls)
            cls.plugins_by_name[cls.__name__] = cls

    @contextmanager
    def fresh_plugins(cls):
        """Context manager to temporarily reset the registry.

        Note that this is a class method on the abstract base class.
        """
        old_plugins = cls.plugins
        old_plugins_by_name = cls.plugins_by_name
        cls.plugins = WeakSet()
        cls.plugins_by_name = WeakValueDictionary()
        yield
        del cls.plugins
        del cls.plugins_by_name
        cls.plugins = old_plugins
        cls.plugins_by_name = old_plugins_by_name
