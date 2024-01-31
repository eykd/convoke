# `convoke.bases`

Decentralized module dependency declaration and initialization

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


## convoke.bases.HQ

::: convoke.bases.HQ
    options:
      heading_level: 3


## convoke.bases.Base

::: convoke.bases.Base
    options:
      heading_level: 3
