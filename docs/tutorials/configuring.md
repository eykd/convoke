# Tutorial: Configuring Your Application

In this tutorial, we'll see how to use `convoke` to configure a simple Starlette
web application.

We'll start with a very simple Starlette web app:

```python
# app.py
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

templates = Jinja2Templates(directory='templates')


async def homepage(request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "DEBUG": request.app.debug}
    )


def create_app():
    return Starlette(debug=True, routes=[
        Route('/', homepage),
    ])
```


## Built-in configuration settings

Now, of course, we don't want to always be in debug mode. Let's add a
configuration by subclassing `convoke.configs.BaseConfig`:

``` python
# app.py
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from convoke.configs import BaseConfig, env_field

# ...

class WebAppConfig(BaseConfig):
    """Configuration for our web application."""


def create_app():
    config = WebAppConfig()

    return Starlette(debug=config.DEBUG, routes=[
        Route('/', homepage),
    ])

```

Every instance of `BaseConfig` has two built-in settings: `DEBUG` and `TESTING`,
both booleans with a default value of `False`. So, if we run our application, it
will default to production mode:

``` shell
$ uvicorn --factory app.create_app
```

But if we set the environment variable `DEBUG=True`, it will run in development
mode:

``` shell
$ DEBUG=True uvicorn --factory app.create_app
```

`DEBUG=true` and `DEBUG=TRUE` would also work, but `tRuE` would not. Likewise,
with equivalent cases of `DEBUG=False`.


## Custom configuration settings

Now, to improve our application, we'll want our users to be able to login, and
for that, we'll need sessions:

``` python
# app.py
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
# ...

def create_app():
    config = WebAppConfig()

    return Starlette(
        debug=config.DEBUG,
        routes=[
            Route('/', homepage),
        ],
        middleware=[
            Middleware(
                SessionMiddleware,
                secret_key="supers3kr1t",
                https_only=not config.DEBUG)
        ],
    )
```

We see how the configuration is already making our lives easier: in production
we want secure sessions, which requires HTTPS, but in development we don't want
to bother with HTTPS, so we use `https_only=not config.DEBUG` to only require
HTTPS in production.


## Protecting secrets

However, we have another problem: our secret key is stored in plain text in our
Python source. Anyone who can read this file can discover our secret and hack
our users! What to do?

Let's move our secret key to the environment:

``` python
# app.py
# ...

class WebAppConfig(BaseConfig):
    """Configuration for our web application."""

    SECRET_KEY: str = env_field()


def create_app():
    config = WebAppConfig()

    return Starlette(
        # ...
        middleware=[
            Middleware(
                SessionMiddleware,
                secret_key=config.SECRET_KEY,
                https_only=not config.DEBUG)
        ],
    )

```

We use all caps `SECRET_KEY` by convention, and the corresponding environment
variable:

``` shell
$ DEBUG=True SECRET_KEY="supers3kr1t"  uvicorn --factory app.create_app
```

Now, one problem is that if we ever print our configuration to the console, we
get our secret in plain text again:

``` python
$ DEBUG=True SECRET_KEY="supers3kr1t"  python
>>> from app import WebAppConfig

>>> print(WebAppConfig())
WebAppConfig(DEBUG=True, TESTING=False, SECRET_KEY='supers3kr1t')
```

Let's fix that by using the `Secret` type:

``` python
# app.py
# ...
from convoke.configs import BaseConfig, env_field, Secret
# ...

class WebAppConfig(BaseConfig):
    """Configuration for our web application."""

    SECRET_KEY: Secret = env_field()

```

Now, when we print to the console, our secret is safe:

``` python
$ DEBUG=True SECRET_KEY="supers3kr1t"  python
>>> from app import WebAppConfig

>>> print(WebAppConfig())
WebAppConfig(DEBUG=True, TESTING=False, SECRET_KEY=Secret('**********'))
```

But when we use the secret as a string, we get the plain-text value:

``` python
>>> str(WebAppConfig().SECRET_KEY)
'supers3kr1t'
```


## Other configuration field types

Since we're considering security, let's consider our session age. Starlette's
default session age is 2 weeks (1,209,600 seconds), but say that for our
application, we require that a user session must be refreshed by authentication
every 24 hours (86,400 seconds). As a business policy, this may change in the
future, so let's make it a configurable value:

``` python
# app.py
# ...
from convoke.configs import BaseConfig, env_field, Secret
# ...

class WebAppConfig(BaseConfig):
    """Configuration for our web application."""

    SECRET_KEY: Secret = env_field()
    SESSION_COOKIE_MAX_AGE: int = env_field(default=86_400)


def create_app():
    config = WebAppConfig()

    return Starlette(
        # ...
        middleware=[
            Middleware(
                SessionMiddleware,
                secret_key=config.SECRET_KEY,
                https_only=not config.DEBUG,
                max_age=config.SESSION_COOKIE_MAX_AGE,
            ),
        ],
    )

```

By annotating the type of the configuration field, we tell `convoke` how to
parse the environment string. This works for floats and booleans too:

``` python
class MyConfig(BaseConfig):
    VALUE_OF_PI: float = env_field(default=3.14)
    USE_ANTIGRAVITY: bool = env_field(default=False)
```


### Configuration fields with multiple values

Now, to really make sure our application is secure, let's configure Starlette's
`TrustedHostMiddleware`:

``` python
# app.py
# ...
from starlette.middleware.trustedhost import TrustedHostMiddleware
# ...

class WebAppConfig(BaseConfig):
    """Configuration for our web application."""

    SECRET_KEY: Secret = env_field()
    SESSION_COOKIE_MAX_AGE: int = env_field(default=86_400)
    ALLOWED_HOSTS: tuple[str] = env_field(default=('127.0.0.1', 'localhost'))


def create_app():
    config = WebAppConfig()

    return Starlette(
        # ...
        middleware=[
            # ...
            Middleware(
                TrustedHostMiddleware,
                allowed_hosts=config.ALLOWED_HOSTS,
            ),
        ],
    )
```

By using the type annotation `tuple[str]`, we tell `convoke` to parse the value
as a comma-separated list of strings, resulting in a tuple of strings:

``` shell
$ DEBUG=True SECRET_KEY="supers3kr1t" ALLOWED_HOSTS="example.com,*.example.com"  uvicorn --factory app.create_app
```

We could also use `tuple[int]` for a setting that uses a sequence of integers, etc.

### Prefer immutability

For that matter, we could also use `ALLOWED_HOSTS: list[str]` give us a list of
strings instead of a tuple, but Config instances are immutable, and it's best to
use immutable types for configuration values as well.


## Generating a .env file

As we've added more configuration values, our `uvicorn` invocation has been
getting longer and longer. Web applications can have tens if not hundreds of
configuration values, and we don't want to type these out every time we start up
the dev server! Let's fix that:

``` python
# app.py
# ...
from convoke.configs import BaseConfig, env_field, generate_dot_env, Secret
# ...

if __name__ == "__main__":
    print(generate_dot_env(BaseConfig.gather_settings()))
```

Then, in the shell:

```
$ python app.py > .env
$ cat .env
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

DEBUG="False"

# --------------------
# -- TESTING (bool) --
# --------------------
#
# Testing mode?

TESTING="False"


###########################
## __main__.WebAppConfig ##
###########################
##
## Configuration for our web application.

# ---------------------------------------
# -- SECRET_KEY (Secret) **Required!** --
# ---------------------------------------

SECRET_KEY="6BIW_mb496YHiptQ1E4WVm-7b_YBW1zQFqZnBKmcsDpTlb1Qb8uZ8w"

# ---------------------------
# -- SESSION_COOKIE_MAX_AGE (int) --
# ---------------------------

SESSION_COOKIE_MAX_AGE="86400"

# ---------------------------
# -- ALLOWED_HOSTS (tuple) --
# ---------------------------

ALLOWED_HOSTS="127.0.0.1,localhost"
```

A few things to note here:

- Default values are included
- Secrets are assigned a securely-generated value
- Configuration values have documentation!

## Documenting configuration values

Let's add some documentation to our config values:

``` python
# app.py
# ...

class WebAppConfig(BaseConfig):
    """Configuration for our web application."""

    SECRET_KEY: Secret = env_field(
        doc="""
            Secret used to cryptographically sign session cookies.

            This should be set to a unique, unpredictable value and kept safe
            from prying eyes.
        """,
    )
    SESSION_COOKIE_MAX_AGE: int = env_field(
        default=86_400,
        doc="""
            The maximum age of session cookies, in seconds.

            Defaults to 24 hours.
        """,
    )
    ALLOWED_HOSTS: tuple[str] = env_field(
        default=('127.0.0.1', 'localhost'),
        doc="""
            A list of strings representing the host/domain names that this site can serve.
        """
    )
```

And now, if we generate a `.env` file again, we see our new documentation:

```
$ python app.py
# ...
###########################
## __main__.WebAppConfig ##
###########################
##
## Configuration for our web application.

# ---------------------------------------
# -- SECRET_KEY (Secret) **Required!** --
# ---------------------------------------
#
# Secret used to cryptographically sign session cookies.
#
# This should be set to a unique, unpredictable value and kept safe from
# prying eyes.

SECRET_KEY="6rlnXtlxeggkgaG1Y4EsEitfRTGjUxu8zbdtZ8GpwfbwCmi0J2Tb3w"

# ----------------------------------
# -- SESSION_COOKIE_MAX_AGE (int) --
# ----------------------------------
#
# The maximum age of session cookies, in seconds.
#
# Defaults to 24 hours.

SESSION_COOKIE_MAX_AGE="86400"

# ---------------------------
# -- ALLOWED_HOSTS (tuple) --
# ---------------------------
#
# A list of strings representing the host/domain names that this site can serve.

ALLOWED_HOSTS="127.0.0.1,localhost"
```

## Conclusion

With that, you should now understand the basics of configuring a Starlette
application with `convoke`, including how to keep secrets safe, and how to
document your settings.
