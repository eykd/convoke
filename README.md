# Convoke

A decentralized async-first app configuration toolkit that tries to do things
right.

    from convoke.configs import BaseConfig, env_field
    from convoke.bases import Base

    class ComponentConfig(BaseConfig):
    # Get your stuff done
    project.do_stuff()

## Features

- Type-safe, environment-based configuration
- Decentralized app configurations

## Installation

With Pip:

    pip install convoke


## Configuration

Configurations are modular, inspired by Python's `dataclasses` module:

    >>> from convoke.configs import BaseConfig, env_field

    >>> class CacheConfig(BaseConfig):
    ...     """Configuration for the caching framework."""
    ...
    ...     CACHE_STORAGE_URI: str = env_field(
    ...         default="memory://",
    ...         doc="""A configuration URI pointing to the desired cache backend.
    ...
    ...         For instance, for a simple Redis-based cache, use:
    ...
    ...             redis://localhost:6379/mycachepath
    ...         """,
    ...     )
    ...

In this example, instantiating `CacheConfig()` will read `CACHE_STORAGE_URI`
from the process environment (`os.environ`), defaulting to `'memory://'` if
nothing is defined.

Rather than defining one singular configuration (e.g. Django's `settings.py`),
`convoke` encourages defining modular, limited-scope configurations close to
where the settings will be used.


### Configuration discovery & .env files

In order to discover what configuration values an application needs, `convoke`
provides a `.env` file generator:

    >>> from convoke.configs import generate_dot_env

    >>> print(generate_dot_env(BaseConfig.gather_settings()))
    ################################
    ## convoke.configs.BaseConfig ##
    ################################
    ##
    ## Base settings common to all configurations

    # ------------------
    # -- DEBUG (bool) --
    # ------------------
    #
    # Development mode?

    DEBUG=""

    # --------------------
    # -- TESTING (bool) --
    # --------------------
    #
    # Testing mode?

    TESTING=""


    ##########################
    ## __main__.CacheConfig ##
    ##########################
    ##
    ## Configuration for the caching framework.

    # -----------------------------
    # -- CACHE_STORAGE_URI (str) --
    # -----------------------------
    #
    # A configuration URI pointing to the desired cache backend.
    #
    # For instance, for a simple Redis-based cache, use:
    #
    #     redis://localhost:6379/mycachepath

    CACHE_STORAGE_URI="memory://"


### Modular apps & signals

Inspired by Django's `AppConfig`, `convoke` provides an abstraction called
"bases":

In `foo.py`:

    from convoke.bases import Base
    from convoke.configs import BaseConfig, env_field
    from convoke.signals import Signal


    class FOO(Signal):
        pass


    class FooConfig(BaseConfig):
        BAR: str = env_field(default="baz")


    class Main(Base):
        config_class = FooConfig

        foos: list[FOO.Message] = Base.field(init=False)

        # Circular dependency!
        dependencies = ["baz"]

        def on_init(self):
            self.foos = []

        @Base.responds(FOO)
        def on_foo(self, obj: FOO.Message):  # pragma: nocover
            self.foos.append(obj)


In `bar.py`:

    from convoke.bases import Base
    from convoke.signals import Signal


    class BAR(Signal):
        pass


    class Main(Base):
        dependencies = ["baz"]

        bars: list[BAR.Message] = Base.field(default_factory=list)

        @Base.responds(BAR)
        async def on_bar(self, obj):  # pragma: nocover
            self.bars.append(obj)


In `baz.py`:

    from typing import Callable

    from convoke.bases import Base
    from convoke.mountpoints import Mountpoint
    from convoke.signals import Signal


    class BAZ(Signal):
        pass


    class ThingyMadoodle(Mountpoint):
        pass


    class Main(Base):
        # Circular dependency!
        dependencies = ["foo"]

        things: list[str] = Base.field(default_factory=list)
        other_things: list[str] = Base.field(default_factory=list)

        @Base.responds(BAZ)
        def on_baz(self, obj: BAZ.Message):
            for thinger in self.thingers:
                thinger(obj.value)

        @property
        def thingers(self) -> list[Callable[[str], None]]:
            return list(self.hq.mountpoints[ThingyMadoodle].mounted)

        @ThingyMadoodle.register
        def do_a_thing(self, value):
            self.things.append(value)

        @ThingyMadoodle.register
        def do_another_thing(self, value):
            self.other_things.append(value)


Each `Base` provides a platform for building a modular app upon, with
interdependencies between Bases. Dependencies are allowed to be circular,
because bases are instantiated separately from import time by the "main base"
known as the HQ:

    >>> hq = HQ(config=config)

    >>> hq.load_dependencies(dependencies=["foo", "bar"])


The HQ manages loading and instantiating bases, connecting signal handlers,
etc. The main application can maintain a reference to the HQ. The `HQ` class
also maintains an `HQ.current_hq` context variable which contains a reference to
the HQ instance for the current thread, if one exists.


### Signals

Convoke signals are presently async-only.

Unlike most signals frameworks (e.g. `blinker` or `Django`), signals are not
global. Instead, signals are passed within the network of bases established by
the HQ:

    >>> from foo import FOO

    >>> await FOO.send(value='blah', using=hq)

    >>> await FOO.send(value='blah')  # <-- uses HQ.current_hq


Contribute
----------

- Source Code: https://github.com/eykd/convoke
- Issue Tracker: https://github.com/eykd/convoke/issues


License
-------

The project is licensed under the BSD 3-clause license.
