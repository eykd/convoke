"""Tools for parsing configuration values from the environment"""
import dataclasses as dc
import importlib
import inspect
import os
import secrets
from collections import defaultdict
from collections.abc import Sequence
from inspect import isabstract
from pathlib import Path
from types import GenericAlias
from typing import Any, Callable, Type, TypeVar, Union, _UnionGenericAlias

import funcy as fn
from funcy import omit

from convoke.docs import comment_lines, format_docstring, format_object_docstring
from convoke.plugins import ABCPluginMount
from convoke.sentinels import UNDEFINED, TUndefined

TRUE_VALUES = {"y", "yes", "t", "true", "on", "1"}
FALSE_VALUES = {"n", "no", "f", "false", "off", "0"}


class Secret(str):
    """A string value that should not be revealed in logs, tracebacks, etc."""

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}('**********')"


TIdentity = TypeVar("T")


def identity(_: TIdentity) -> TIdentity:
    """Default caster for returning the original config value (a str) as such"""
    return _


def import_object(path):
    """Treat a config value as an importable string.

    Valid values include:

    - dotted paths (e.g. `path.to.module.Object`)
    - dotted paths with colon object notation (e.g. `path.to.module:Object`)

    Both examples are equivalent to `from path.to.module import Object`.
    """
    try:
        path, name = path.rsplit(":", 1)
    except ValueError:
        try:
            path, name = path.rsplit(".", 1)
        except ValueError:
            raise ValueError(f"{path} is not a properly formed object import path: `module.obj` or `module:obj` ")
    package = importlib.import_module(path)
    return getattr(package, name)


def strtobool(value):
    """Treat a config value as a boolean

    Valid truthy values include:

        {"y", "yes", "t", "true", "on", "1"}

    Valid falsey values include:

        {"n", "no", "f", "false", "off", "0"}

    """
    if isinstance(value, bool):
        return value
    value = value.lower()

    if value in TRUE_VALUES:
        return True
    elif value in FALSE_VALUES:
        return False

    raise ValueError("Invalid truth value: " + value)


def get_sequence_parser(inner_caster: Callable, seq_type: Sequence) -> Callable:
    """Return a config value parser that returns a sequence type of the inner caster type.

    :param inner_caster Callable: any callable that parses a string value as a particular type
    :param seq_type Sequence: the sequence type for the parser to return
    """

    def parse_sequence(value: Sequence[Any]) -> Sequence[Any]:
        if isinstance(value, str):
            value = [inner_caster(v.strip()) for v in value.split(",")]
        return seq_type(value)

    return parse_sequence


def get_sequence_type(the_type: Type[Sequence]) -> Callable[[str], Any]:
    """Return the given sequence type, or `tuple` if the type is abstract."""
    if isabstract(the_type):
        seq_type = tuple
    else:
        seq_type = the_type
    return seq_type


def get_casting_type(name: str, the_type: Type) -> Callable[[str], Any]:
    """Determine a casting type from a type annotation.

    FIXME: This doesn't work with string annotations yet.
    """
    if isinstance(the_type, _UnionGenericAlias):
        # i.e. Optional[<type>]
        # One of the args is None, the other is a type:
        for inner_type in the_type.__args__:
            if inner_type is not type(None):
                return get_casting_type(name, inner_type)
        else:
            raise TypeError(f"{name!r} has an unrecognizable type annotation {the_type}")  # pragma: nocover
    elif isinstance(the_type, GenericAlias) and issubclass(the_type.__origin__, Sequence):
        # e.g. tuple[str]
        if len(the_type.__args__) > 1:
            # e.g. tuple[str, int]
            raise TypeError(f"{name!r} is a sequence config field, but can only have one inner type annotation")
        inner_cast = the_type.__args__[0]
        if inner_cast is bool:
            inner_cast = strtobool
        caster = get_sequence_parser(inner_cast, get_sequence_type(the_type.__origin__))
    elif issubclass(the_type, Sequence) and not issubclass(the_type, str):
        caster = get_sequence_parser(str, get_sequence_type(the_type))
    else:
        if the_type is bool:
            caster = strtobool
        else:
            caster = the_type

    return caster


def get_env(name: str, the_type: Type = str, default: Any = dc.MISSING):
    """Return a parsed value of `the_type` from the environment."""
    # By convention, if the annotation is a plain tuple, we
    # cast values as str.
    caster = get_casting_type(name, the_type)
    raw_value = os.environ.get(name, default)
    if raw_value is dc.MISSING:
        raise RuntimeError(f"No configured value for {name!r}")
    if raw_value is not None:
        return caster(raw_value)
    return raw_value


class ConfigField(dc.Field):
    """Special-purpose dataclass field that defaults to pulling from the environment."""

    def __init__(self, default, init, repr, hash, compare, metadata, kw_only, doc=""):
        super().__init__(
            default=dc.MISSING,
            default_factory=self.get_default_factory(default),
            init=init,
            repr=repr,
            hash=hash,
            compare=compare,
            metadata=metadata,
            kw_only=kw_only,
        )
        self.__config_default__ = default
        self.__doc__ = doc

    def get_default_factory(self, default):
        """Build a default factory that will pull from the environment."""

        def make_default():
            # By convention, if the annotation is a plain tuple, we
            # cast values as str.
            return get_env(self.name, the_type=self.type, default=default)

        return make_default


def env_field(
    *,
    default=dc.MISSING,
    init=True,
    repr=True,
    hash=None,
    compare=True,
    metadata=None,
    kw_only=dc.MISSING,
    doc="",
):
    """Define a field that pulls config values from the environment.

    Fields with missing defaults will be assumed to be required, and if missing will produce an error.

    :param Any default: the default value to use, if any, of the expected type. If this is omitted, the field will be required.
    :param str doc: a docstring describing the use of the configuration value, used in generating .env files

    """
    return ConfigField(default, init, repr, hash, compare, metadata, kw_only, doc)


def configclass(cls):
    """Prepare a config class as a dataclass.

    Examines PEP 526 __annotations__ to determine fields.

    If init is true, an __init__() method is added to the class. If repr
    is true, a __repr__() method is added. If order is true, rich
    comparison dunder methods are added. If unsafe_hash is true, a
    __hash__() method is added. If frozen is true, fields may not be
    assigned to after instance creation. If match_args is true, the
    __match_args__ tuple is added. If kw_only is true, then by default
    all fields are keyword-only. If slots is true, a new class with a
    __slots__ attribute is returned.
    """
    return dc.dataclass(
        cls,
        init=True,
        repr=True,
        eq=True,
        order=False,
        unsafe_hash=True,
        frozen=True,
        match_args=True,
        kw_only=True,
        slots=False,
        # weakref_slot=False,
    )


T = TypeVar("T", bound="BaseConfig")


class BaseConfigMeta(ABCPluginMount):
    """Automatically wrap BaseConfig subclasses with @configclass"""

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        configclass(cls)


class BaseConfig(metaclass=BaseConfigMeta):
    """Base settings common to all configurations"""

    DEBUG: bool = env_field(default=False, doc="Development mode?")
    TESTING: bool = env_field(default=False, doc="Testing mode?")

    env_field = env_field

    @classmethod
    def from_config(cls: Type[T], config: "BaseConfig") -> T:
        """Derive an instance of this config class from another configuration.

        This is really only useful if the passed configuration has
        overridden (non-environment-derived) values.

        """
        valid_params = set(inspect.signature(cls).parameters)
        kwargs = {k: v for k, v in dc.asdict(config).items() if k in valid_params}
        return cls(**kwargs)

    @classmethod
    def gather_settings(cls) -> dict:
        """Gather settings from all loaded configurations."""
        base = BaseConfig.report_settings()
        base_settings = set(base["settings"].keys())
        all_settings = {f"{BaseConfig.__module__}.{BaseConfig.__name__}": base}
        for config in cls.plugins_by_name.values():
            settings = config.report_settings()
            all_settings[f"{config.__module__}.{config.__name__}"] = {
                "doc": settings["doc"],
                "settings": omit(settings["settings"], base_settings),
            }

        return all_settings

    @classmethod
    def report_settings(cls) -> dict:
        """Prepare a datastructure reporting on this configuration class's settings."""
        return {
            "doc": format_object_docstring(cls),
            "settings": {
                fd.name: {
                    "type": fd.type,
                    "default": (
                        UNDEFINED
                        if (default := getattr(fd, "__config_default__", dc.MISSING)) is dc.MISSING
                        else default
                    ),
                    "doc": getattr(fd, "__doc__", ""),
                }
                for fd in dc.fields(cls)
            },
        }

    def __getitem__(self, name: str) -> str:
        if hasattr(self, name):
            return getattr(self, name)

        return os.environ[name]

    def get(self, name: str, default: Any = UNDEFINED, caster: Union[Type, TUndefined] = UNDEFINED) -> Any:
        """Return the named configuration environment value, optionally casting it as specified.

        :param str name: The name of the configuration value, as defined on this object or in the environment.
        :param Any default: A default value, already the expected type.
        :param Type caster: A type to cast the string value to, if any.
        """
        if caster is UNDEFINED:
            caster = identity
        else:
            caster = get_casting_type(name, caster)
        try:
            value = self[name]
        except KeyError:
            if default is UNDEFINED:
                raise
            else:
                value = default

        return caster(value)

    def asdict(self, keys=()) -> dict:
        """Return a dictionary with the defined settings"""
        if keys:
            return fn.project(dc.asdict(self), keys)
        else:
            return dc.asdict(self)

    def get_tuple(
        self, name: str, default: Union[tuple[Any], TUndefined] = UNDEFINED, caster: Type = tuple[str]
    ) -> tuple[Any]:
        """Return the named configuration environment value as a sequence, optionally casting internal values as specified.

        :param str name: The name of the configuration value, as defined on this object or in the environment.
        :param Any default: A default value, already the expected type.
        :param Type caster: A type to cast the internal string values to, if any.
        """
        return self.get(name, default=default, caster=caster)

    def as_secret(self, name: str, default: Secret = UNDEFINED) -> Secret:
        """Return the named configuration environment value as a Secret string.

        :param str name: The name of the configuration value, as defined on this object or in the environment.
        :param Any default: A default value, already a Secret.
        """
        return self.get(name, default=default, caster=Secret)

    def as_secret_tuple(self, name: str, default: Union[tuple[Secret], TUndefined] = UNDEFINED) -> tuple[Secret]:
        """Return the named configuration environment value as a sequence of Secret strings.

        :param str name: The name of the configuration value, as defined on this object or in the environment.
        :param Any default: A default value, already a tuple of Secrets.
        """
        return self.get_tuple(name, default=default, caster=tuple[Secret])

    def as_bool(self, name: str, default: Union[bool, TUndefined] = UNDEFINED) -> bool:
        """Return the named configuration environment value as a boolean value.

        :param str name: The name of the configuration value, as defined on this object or in the environment.
        :param Any default: A default value, already a boolean.
        """
        return self.get(name, default=default, caster=bool)

    def as_bool_tuple(self, name: str, default: Union[tuple[bool], TUndefined] = UNDEFINED) -> tuple[bool]:
        """Return the named configuration environment value as a tuple of boolean values.

        :param str name: The name of the configuration value, as defined on this object or in the environment.
        :param Any default: A default value, already a tuple of booleans.
        """
        return self.get_tuple(name, default=default, caster=tuple[bool])

    def as_int(self, name: str, default: Union[int, TUndefined] = UNDEFINED) -> int:
        """Return the named configuration environment value as an int.

        :param str name: The name of the configuration value, as defined on this object or in the environment.
        :param Any default: A default value, already an int.
        """
        return self.get(name, default=default, caster=int)

    def as_int_tuple(self, name: str, default: Union[tuple[int], TUndefined] = UNDEFINED) -> tuple[int]:
        """Return the named configuration environment value as a tuple of ints.

        :param str name: The name of the configuration value, as defined on this object or in the environment.
        :param Any default: A default value, already a tuple of ints.
        """
        return self.get_tuple(name, default=default, caster=tuple[int])

    def as_float(self, name: str, default: Union[float, TUndefined] = UNDEFINED) -> float:
        """Return the named configuration environment value as a float.

        :param str name: The name of the configuration value, as defined on this object or in the environment.
        :param Any default: A default value, already a float.
        """
        return self.get(name, default=default, caster=float)

    def as_float_tuple(self, name: str, default: Union[tuple[float], TUndefined] = UNDEFINED) -> tuple[float]:
        """Return the named configuration environment value as a tuple of floats.

        :param str name: The name of the configuration value, as defined on this object or in the environment.
        :param Any default: A default value, already a tuple of floats.
        """
        return self.get_tuple(name, default=default, caster=tuple[float])

    def as_path(self, name: str, default: Union[Path, TUndefined] = UNDEFINED) -> Path:
        """Return the named configuration environment value as a Path.

        :param str name: The name of the configuration value, as defined on this object or in the environment.
        :param Any default: A default value, already a Path.
        """
        return self.get(name, default=default, caster=Path)

    def as_path_tuple(self, name: str, default: Union[tuple[float], TUndefined] = UNDEFINED) -> tuple[Path]:
        """Return the named configuration environment value as a tuple of Paths.

        :param str name: The name of the configuration value, as defined on this object or in the environment.
        :param Any default: A default value, already a tuple of Paths.
        """
        return self.get(name, default=default, caster=tuple[Path])

    def as_package_import(self, name: str, default: Union[Any, TUndefined] = UNDEFINED) -> Any:
        """Return the named configuration environment value as an imported module.

        :param str name: The name of the configuration value, as defined on this object or in the environment.
        :param Any default: A default value, already a module.
        """
        path = self.get(name, default=default)
        return importlib.import_module(path)

    def as_package_import_tuple(self, name: str, default: Union[tuple[Any], TUndefined] = UNDEFINED) -> tuple[Any]:
        """Return the named configuration environment value as a tuple of imported modules.

        :param str name: The name of the configuration value, as defined on this object or in the environment.
        :param Any default: A default value, already a tuple of modules.
        """
        paths = self.get_tuple(name, default=default)
        return tuple(importlib.import_module(path) for path in paths)

    def as_object_import(self, name: str, default: Union[Any, TUndefined] = UNDEFINED) -> Any:
        """Return the named configuration environment value as an imported object.

        :param str name: The name of the configuration value, as defined on this object or in the environment.
        :param Any default: A default value, already an object.
        """
        path = self.get(name, default=default)
        return import_object(path)

    def as_object_import_tuple(self, name: str, default: Union[tuple[Any], TUndefined] = UNDEFINED):
        """Return the named configuration environment value as a tuple of imported objects.

        :param str name: The name of the configuration value, as defined on this object or in the environment.
        :param Any default: A default value, already a tuple of objects.
        """
        paths = self.get_tuple(name, default=default)
        return tuple(import_object(path) for path in paths)


def generate_dot_env(settings_summary: dict, generate_secrets=True, required_only=False):  # noqa: C901
    """Generate a .env-friendly summary string of all extant BaseConfig subclasses.

    All desired Config objects should be loaded into memory, e.g. by
    instantiating an HQ and loading its dependencies.

    :param dict settings_summary: a dictionary summary as generated by `BaseConfig.gather_settings()`.
    :param bool generate_secrets: generate secure tokens for any secret values?
    :param bool required_only: only output required settings?
    """
    out = []
    seen_also_in = defaultdict(list)
    for config_name, report in settings_summary.items():
        for name in report["settings"]:
            seen_also_in[name].append(config_name)

    seen = set()
    for config_name, report in settings_summary.items():
        if required_only:
            any_required = any(meta["default"] is UNDEFINED for meta in report["settings"].values())
            if not any_required:
                continue
        # Config section heading:
        section_title = f"## {config_name} ##"
        out.append("#" * len(section_title))
        out.append(section_title)
        out.append("#" * len(section_title))
        # Config section docstring:
        if report["doc"]:
            out.append("##")
            out.append(comment_lines(format_docstring(report["doc"], wrap=70), comment="##"))
            out.append("")
        for name, meta in report["settings"].items():
            is_required = meta["default"] is UNDEFINED
            if required_only and not is_required:
                continue
            # Setting section heading:
            mtype = getattr(meta["type"], "__name__", meta["type"])
            setting_title = f"# -- {name} ({mtype})" + (" **Required!**" if is_required else "") + " --"
            out.append("# " + ("-" * (len(setting_title) - 2)))
            out.append(setting_title)
            out.append("# " + ("-" * (len(setting_title) - 2)))
            # Setting docstring:
            if meta["doc"]:
                out.append("#")
                out.append(comment_lines(format_docstring(meta["doc"], wrap=70)))
            out.append("")

            # Add note about duplication, if needed
            if len(seen_also_in[name]) > 1:
                others = list(fn.without(seen_also_in[name], config_name))
                out.append("# This setting is also used in:")
                for other in others:
                    out.append(f"# - {other}")
            if name in seen:
                if len(others) == 1:
                    out.append("# and is already set above.")
                else:
                    out.append(f"# and is already set above in {fn.first(others)}.")

            # Get default value to emit:
            default = meta["default"] if "default" in meta and meta["default"] is not UNDEFINED else ""
            if not isinstance(default, str) and isinstance(default, Sequence):
                default = ",".join(default)
            elif generate_secrets and meta["type"] == Secret and "SECRET" in name and default == "":
                default = secrets.token_urlsafe(40)

            # Emit the default setting:
            if name in seen:
                out.append(f'#    {name}="{default}"')
            else:
                out.append(f'{name}="{default}"')
            out.append("")

            seen.add(name)
        out.append("")

    return "\n".join(out).rstrip() + "\n"
