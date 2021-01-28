import importlib
import os
import pathlib
import sys
from collections.abc import Iterable

import pendulum as pn
from configobj import ConfigObj
from path import Path

from ._version import get_versions

__version__ = get_versions()['version']

del get_versions


class UNDEFINED:
    pass


MSYS2 = sys.platform.startswith("win") and ("GCC" in sys.version)
APP_ENGINE = "APPENGINE_RUNTIME" in os.environ and "Development/" in os.environ.get(
    "SERVER_SOFTWARE", ""
)
WIN = sys.platform.startswith("win") and not APP_ENGINE and not MSYS2


def _slugify(name):
    return "-".join(name.split()).lower()


def _identity(_):
    return _


def get_app_dir(app_name, roaming=True, force_posix=False):
    r"""Returns the config folder for the application.  The default behavior
    is to return whatever is most appropriate for the operating system.
    To give you an idea, for an app called ``"Foo Bar"``, something like
    the following folders could be returned:
    Mac OS X:
      ``~/Library/Application Support/Foo Bar``
    Mac OS X (POSIX):
      ``~/.foo-bar``
    Unix:
      ``~/.config/foo-bar``
    Unix (POSIX):
      ``~/.foo-bar``
    Win XP (roaming):
      ``C:\Documents and Settings\<user>\Local Settings\Application Data\Foo Bar``
    Win XP (not roaming):
      ``C:\Documents and Settings\<user>\Application Data\Foo Bar``
    Win 7 (roaming):
      ``C:\Users\<user>\AppData\Roaming\Foo Bar``
    Win 7 (not roaming):
      ``C:\Users\<user>\AppData\Local\Foo Bar``
    .. versionadded:: 2.0
    :param app_name: the application name.  This should be properly capitalized
                     and can contain whitespace.
    :param roaming: controls if the folder should be roaming or not on Windows.
                    Has no affect otherwise.
    :param force_posix: if this is set to `True` then on any POSIX system the
                        folder will be stored in the home folder with a leading
                        dot instead of the XDG config home or darwin's
                        application support folder.
    """
    # Based on https://github.com/pallets/click/blob/1784558ed7c75c65764d2a434bd9cbb206ca939d/src/click/utils.py#L380-L430
    if WIN:
        key = "APPDATA" if roaming else "LOCALAPPDATA"
        folder = Path(os.environ.get(key, "~"))
        return folder.expanduser() / app_name
    if force_posix:
        return Path(f"~/.{_slugify(app_name)}").expanduser()
    if sys.platform == "darwin":
        return Path("~/Library/Application Support").expanduser() / app_name
    return Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser() / _slugify(
        app_name
    )


class Settings:
    Path = Path

    def __init__(self, app_name, config=None, **overrides):
        self.app_name = app_name
        self.overrides = overrides
        self.config = {}

        self.app_dir = self.as_path('app_dir', get_app_dir(app_name))

        config = self.config = self.resolve_config(config)

    @property
    def debug(self):
        return self.as_bool("debug", default=False)

    @property
    def data_dir(self):
        return self.as_path(
            "data_dir",
            default=Path(self.config.filename).parent
            if self.config.filename
            else self.app_dir,
        )

    def __getitem__(self, name):
        value = self.overrides.get(
            name, os.environ.get(name.upper(), self.config.get(name, UNDEFINED))
        )
        if value is UNDEFINED:
            raise KeyError(name)
        return value

    def get(self, name, default=UNDEFINED, cast=_identity):
        try:
            return self.apply_cast(self[name], cast)
        except KeyError:
            if default is not UNDEFINED:
                return self.apply_cast(default, cast)
            raise

    def get_list(self, name, default=UNDEFINED, cast=_identity):
        try:
            values = self[name]
        except KeyError:
            if default is UNDEFINED:
                raise
            else:
                values = default
        if values is None:
            values = []
        if not isinstance(values, Iterable):
            raise TypeError(f'Unknown type {type(values)} for "{name}"')
        if isinstance(values, str):
            values = (s.strip() for s in values.split(','))

        return [self.apply_cast(v, cast) for v in values]

    def as_bool(self, name, default=UNDEFINED):
        return self.get(name, default=default, cast=bool)

    def as_bool_list(self, name, default=UNDEFINED):
        return self.get_list(name, default=default, cast=bool)

    def as_int(self, name, default=UNDEFINED):
        return self.get(name, default=default, cast=int)

    def as_int_list(self, name, default=UNDEFINED):
        return self.get_list(name, default=default, cast=int)

    def as_float(self, name, default=UNDEFINED):
        return self.get(name, default=default, cast=float)

    def as_float_list(self, name, default=UNDEFINED):
        return self.get_list(name, default=default, cast=float)

    def as_path(self, name, default=UNDEFINED):
        return self.get(name, default=default, cast=Path).expanduser().abspath()

    def as_package_import(self, name, default=UNDEFINED):
        path = self.get(name, default=default)
        return importlib.import_module(path)

    def as_package_import_list(self, name, default=UNDEFINED):
        paths = self.get_list(name, default=default)
        return [importlib.import_module(path) for path in paths]

    def as_object_import(self, name, default=UNDEFINED):
        path = self.get(name, default=default)
        return self.import_object(path)

    def as_object_import_list(self, name, default=UNDEFINED):
        paths = self.get_list(name, default=default)
        return [self.import_object(path) for path in paths]

    def apply_cast(self, value, cast):
        if cast is bool and isinstance(value, str):
            if value.lower() in ("true", "1"):
                return True
            elif value.lower() in ("false", "0"):
                return False
            else:
                raise ValueError(value)
        return cast(value)

    def import_object(self, path):
        try:
            path, name = path.rsplit('.', 1)
        except ValueError:
            raise ValueError(f'{path} is not a dotted path')
        package = importlib.import_module(path)
        return getattr(package, name)

    def resolve_config(self, config):
        if isinstance(config, (pathlib.Path, Path)):
            config = str(config)
        if isinstance(config, str):
            config = Path(config).expanduser()
            if not config.exists():
                config.touch()
            config = ConfigObj(config)

        if not isinstance(config, ConfigObj):
            default_path = self.app_dir / 'config.ini'
            config = ConfigObj(default_path)

        return config

    def get_timezone(self):
        return self.get("timezone", pn.local_timezone().name)

    def now(self, timezone=None):
        if timezone is None:
            timezone = self.get_timezone()
        return pn.now(tz=timezone)

    def utcnow(self):
        return self.now(timezone="UTC")


def get_settings(app_name, settings_class=Settings, **kwargs):
    settings = settings_class(app_name, **kwargs)
    global get_settings
    get_settings = lambda _=None, **kw: settings  # noqa: E731
    return settings
