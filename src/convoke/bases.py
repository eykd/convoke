"""Decentralized module dependency declaration and initialization

Bases provide a similar concept to Django's AppConfig, and act as a
central place for each module to register important things like signal
handlers and template context processors, without needing a global
central object.

A single HQ acts as the coordinator for a suite of Bases. At runtime,
an application instantiates an HQ, providing a list of dependencies
(dotted strings, similar to Django's `INSTALLED_APPS` setting). Each
dependency is a dotted string to a module or package containing a Base
subclass named `Main`. Bases may also declare their own dependencies.

This system allows us to avoid module-level code dependencies that
depend overly on import order and global state, and allows a better
separation of initialization and execution.

"""
from __future__ import annotations

import importlib
import inspect
import logging
from collections import defaultdict
from collections.abc import Sequence
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Optional, Type, Union

from convoke.configs import BaseConfig
from convoke.inspectors import is_async_callable
from convoke.mountpoints import Mountpoint, MountpointDict
from convoke.signals import Receiver, Signal

PATH = Path(__file__).absolute().parent


@dataclass
class HQ:
    """The HQ is the special root Base.

    The HQ is directly instantiated by a client code entrypoint, rather than
    discovered by the dependency loader.

        hq = HQ(config=MyConfig(), dependencies=['foo'])
    """

    config: BaseConfig = field(default_factory=BaseConfig, repr=False)

    bases: dict[str, Base] = field(init=False, default_factory=dict, repr=False)
    signal_receivers: dict[Type[Signal], set[Receiver]] = field(init=False, default_factory=lambda: defaultdict(set))
    mountpoints: MountpointDict[Type[Mountpoint], Mountpoint] = field(init=False, default_factory=MountpointDict)

    hq: HQ = field(init=False)

    current_instance: ClassVar[ContextVar] = ContextVar("current_instance")

    def __post_init__(self):
        self.hq = self
        self.current_instance.set(self)

    @classmethod
    def get_current(cls):
        """Return the instance of HQ for the current context."""
        return cls.current_instance.get()

    def reset(self):
        """Reset this HQ and its associated Bases.

        Primarily, this re-establishes this instance as the current HQ
        instance, and re-initializes bases.

        """
        self.current_instance.set(self)
        for base in self.bases.values():
            base.reset()

    def load_dependencies(self, dependencies: Sequence[str]):
        """Load peripheral Base dependencies.

        :param Sequence[str] dependencies: a list of dotted paths to
            modules/packages that contain a Base subclass named `Main`.
        """
        load_dependencies(self, dependencies)
        for base in self.bases.values():
            base.ready()
            logging.debug(f"{base.__module__} reports ready")

    def connect_signal_receiver(self, signal_class: Type[Signal], receiver: Receiver):
        """Connect a receiver function to the given Signal subclass.

        All connections are local to this HQ instance. Mostly used
        internally via the `Base.responds(SignalSubclass)` decorator.

        :param Type[Signal] signal_class: The Signal subclass to connect to.
        :param Receiver receiver: a Callable that accepts a message of the type
            defined on the Signal subclass.

        """
        self.signal_receivers[signal_class].add(receiver)

    def disconnect_signal_receiver(self, signal_class: Type[Signal], receiver: Receiver):
        """Disconnect a receiver function previously connected to the given Signal subclass.

        :param Type[Signal] signal_class: The Signal subclass to disconnect from.
        :param Receiver receiver: a previously-connected Callable.
        """
        self.signal_receivers[signal_class].discard(receiver)

    async def send_signal(self, signal_class: Type[Signal], msg):
        """Send a Message to all receivers of the given Signal subclass.

        :param Type[Signal] signal_class: The Signal subclass to send
        :param Any msg: An instance of signal_class.Message
        """
        for receiver in self.signal_receivers[signal_class]:
            try:
                if is_async_callable(receiver):
                    await receiver(msg)
                else:
                    receiver(msg)
            except Exception:  # pragma: nocover
                # It's important that we swallow the exception, log
                # it, and soldier on. We don't need to cover this
                # branch though.
                logging.exception(
                    f"Exception occurred while sending {signal_class!r}:\nReceiver {receiver!r}\n Message: {msg!r}"
                )


def load_dependencies(
    subject: Union[Base, HQ], dependencies: Sequence[str], seen: Optional[dict[str, Base]] = None
) -> None:
    """Load dependencies and subdependencies.

    The dependency loader does a depth-first, left-to-right
    traversal of the dependency graph, and can handle circular
    dependencies.

    """
    if seen is None:
        seen = {}

    for name in dependencies:
        if name in seen:
            subject.hq.bases[name] = subject.bases[name] = seen[name]

        else:
            mod = importlib.import_module(name)
            base = subject.hq.bases[name] = seen[name] = subject.bases[name] = mod.Main(hq=subject.hq)
            load_dependencies(base, base.dependencies, seen)


def responds(signal: Type[Signal]):
    """Decorate a Base method as a signal handler."""

    def decorator(the_func: Receiver):
        signals = getattr(the_func, "__signals__", [])
        signals.append(signal)
        the_func.__signals__ = signals
        return the_func

    return decorator


class BaseMeta(type):
    r"""Automatically wrap Base subclasses with @dataclass

    This does not appear to work when performed in
    Base.__init_subclass__(). ¯\\_(ツ)_//¯
    """

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        dataclass(cls)


class Base(metaclass=BaseMeta):
    """A Base organizes an app within a Convoke project.

    For base discovery, an app should provide a subclass named `Main`
    in the app's primary module:

        class Main(Base):
            config_class: MyConfig = MyConfig

            # Dependencies are dotted paths to modules containing a
            # Main subclass:
            dependencies = ['foo', 'foo.bar']

    Base is similar in concept to Django's `AppConfig`.
    """

    hq: HQ

    bases: dict[str, Base] = field(init=False, default_factory=dict, repr=False)

    config: BaseConfig = field(init=False, repr=False)

    dependencies: ClassVar[Sequence[str]] = ()
    config_class: ClassVar[Type[BaseConfig]] = BaseConfig
    current_instance: ClassVar[ContextVar]

    def __init_subclass__(cls):
        cls.current_instance = ContextVar("current_instance")

    def __post_init__(self):
        self.reset()

    def ready(self):
        """Make the base ready for action."""
        self.on_ready()

    field = field
    responds = responds

    def reset(self):
        """Reset the base, reloading configuration and initialization."""
        self.config = self.config_class.from_config(self.hq.config)
        self.on_init()
        self._register_special_methods()
        self.current_instance.set(self)

    def on_init(self):
        """Subclass-overridable method to call at the end of initialization"""
        pass

    def on_ready(self):
        """Subclass-overridable method to call after all Bases ready"""
        pass

    @classmethod
    def get_current(cls):
        """Return the current instance of this Base for the current context."""
        return cls.current_instance.get()

    def _register_special_methods(self):
        """Look for and register specially-decorated Base methods."""
        # We need to inspect members of the class, not the instance,
        # to avoid tripping over any descriptors before we're ready.
        for name, func in inspect.getmembers(self.__class__, inspect.isfunction):
            if inspect.ismethod(method := getattr(self, name)):
                # Register signals
                signals = getattr(func, "__signals__", ())
                for signal in signals:
                    self.hq.connect_signal_receiver(signal, method)

                # Register mountpoints
                mountpoints = getattr(method.__func__, "__mountpoints__", ())
                for mountpoint in mountpoints:
                    self.hq.mountpoints[mountpoint].mount(method)
            else:  # pragma: nocover
                pass
                # Some days, branch coverage makes us do silly things to get to 100%.
