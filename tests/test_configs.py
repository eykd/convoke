# ruff: noqa: D100, D101, D102, D103
import collections.abc
import os
import textwrap
import unittest.mock
from collections.abc import Sequence
from pathlib import Path
from typing import Optional, Union
from unittest.mock import patch

import pytest
from funcy import project

from convoke.configs import UNDEFINED, BaseConfig, Secret, env_field, generate_dot_env


class TestEnvField:
    def test_it_should_accept_a_default_config_str(self):
        class Config(BaseConfig):
            FOO: str = env_field(default="bar")

        config = Config()
        assert config.FOO == "bar"

    def test_it_should_override_a_default_config_str_with_env(self):
        class Config(BaseConfig):
            FOO: str = env_field(default="bar")

        with patch.dict(os.environ, {"FOO": "blah"}):
            config = Config()

        assert config.FOO == "blah"

    def test_it_should_override_env_with_direct_value(self):
        class Config(BaseConfig):
            FOO: str = env_field(default="bar")

        with patch.dict(os.environ, {"FOO": "blah"}):
            config = Config(FOO="banana")

        assert config.FOO == "banana"

    def test_it_should_accept_a_default_config_bool(self):
        class Config(BaseConfig):
            FOO: bool = env_field(default=False)

        config = Config()
        assert config.FOO is False

    def test_it_should_override_a_default_config_bool_with_env(self):
        class Config(BaseConfig):
            FOO: bool = env_field(default=True)

        with patch.dict(os.environ, {"FOO": "False"}):
            config = Config()

        assert config.FOO is False

    def test_it_should_accept_a_default_config_int(self):
        class Config(BaseConfig):
            FOO: int = env_field(default=10)

        config = Config()
        assert config.FOO == 10

    def test_it_should_override_a_default_config_int_with_env(self):
        class Config(BaseConfig):
            FOO: int = env_field(default=10)

        with patch.dict(os.environ, {"FOO": "11"}):
            config = Config()

        assert config.FOO == 11

    def test_it_should_accept_a_classvar_str(self):
        class Config(BaseConfig):
            FOO: str = "bar"

        config = Config()
        assert config.FOO == "bar"

    def test_it_should_NOT_override_a_classvar_str_with_env(self):
        class Config(BaseConfig):
            FOO: str = "bar"

        with patch.dict(os.environ, {"FOO": "blah"}):
            config = Config()

        # If no env_field is used, we don't pull from the environment.
        assert config.FOO == "bar"

    def test_it_should_accept_an_optional_config_str(self):
        class Config(BaseConfig):
            FOO: Optional[str] = env_field(default=None)

        config = Config()
        assert config.FOO is None

    def test_it_should_accept_an_optional_config_cast(self):
        class Config(BaseConfig):
            FOO: Optional[int] = env_field(default=None)

        with patch.dict(os.environ, {"FOO": "5000"}):
            config = Config()
        assert config.FOO == 5000

    def test_it_should_accept_an_optional_union_config_cast(self):
        class Config(BaseConfig):
            FOO: Union[None, int] = env_field(default=None)

        with patch.dict(os.environ, {"FOO": "5000"}):
            config = Config()
        assert config.FOO == 5000

    def test_it_should_accept_an_optional_union_config_w_default(self):
        class Config(BaseConfig):
            FOO: Union[int, None] = env_field(default=None)

        config = Config()
        assert config.FOO is None

    def test_it_should_reject_an_optional_union_config_w_only_none(self):
        class Config(BaseConfig):
            FOO: Union[None]

        with pytest.raises(TypeError):
            Config()

    def test_it_should_fail_if_missing_a_config_value(self):
        class Config(BaseConfig):
            FOO: str = env_field()

        with pytest.raises(RuntimeError):
            Config()

    def test_it_should_fail_on_bad_boolean_value(self):
        class Config(BaseConfig):
            FOO: bool = env_field()

        with patch.dict(os.environ, {"FOO": "blah"}):
            with pytest.raises(ValueError):
                Config()


class TestTupleEnvField:
    def test_it_should_accept_a_default_config_str(self):
        class Config(BaseConfig):
            FOO: tuple[str] = env_field(default="bar,blah")

        config = Config()
        assert config.FOO == ("bar", "blah")

    def test_it_should_accept_a_default_config_tuple(self):
        class Config(BaseConfig):
            FOO: tuple[str] = env_field(default=("bar", "blah"))

        config = Config()
        assert config.FOO == ("bar", "blah")

    def test_it_should_override_a_default_config_str_with_env(self):
        class Config(BaseConfig):
            FOO: tuple[str] = env_field(default="bar,blah")

        with patch.dict(os.environ, {"FOO": "blah, bar"}):
            config = Config()

        assert config.FOO == ("blah", "bar")

    def test_it_should_assume_strings_with_no_inner_type(self):
        class Config(BaseConfig):
            FOO: tuple = env_field(default="bar,blah")

        with patch.dict(os.environ, {"FOO": "blah, bar"}):
            config = Config()

        assert config.FOO == ("blah", "bar")

    def test_it_should_override_env_with_direct_value(self):
        class Config(BaseConfig):
            FOO: tuple[str] = env_field(default="bar,blah")

        with patch.dict(os.environ, {"FOO": "blah,bar"}):
            config = Config(FOO=("bar", "banana"))

        assert config.FOO == ("bar", "banana")

    def test_it_should_accept_a_default_config_bool(self):
        class Config(BaseConfig):
            FOO: tuple[bool] = env_field(default="False,True")

        config = Config()
        assert config.FOO == (False, True)

    def test_it_should_override_a_default_config_bool_with_env(self):
        class Config(BaseConfig):
            FOO: tuple[bool] = env_field(default="False,True")

        with patch.dict(os.environ, {"FOO": "True,False"}):
            config = Config()

        assert config.FOO == (True, False)

    def test_it_should_accept_a_default_config_int(self):
        class Config(BaseConfig):
            FOO: tuple[int] = env_field(default="10")

        config = Config()
        assert config.FOO == (10,)

    def test_it_should_override_a_default_config_int_with_env(self):
        class Config(BaseConfig):
            FOO: tuple[int] = env_field(default="10,11")

        with patch.dict(os.environ, {"FOO": "11,12"}):
            config = Config()

        assert config.FOO == (11, 12)

    def test_it_should_accept_a_classvar_str(self):
        class Config(BaseConfig):
            FOO: tuple[str] = ("bar", "blah")

        config = Config()
        assert config.FOO == ("bar", "blah")

    def test_it_should_NOT_override_a_classvar_str_with_env(self):
        class Config(BaseConfig):
            FOO: tuple[str] = ("bar", "blah")

        with patch.dict(os.environ, {"FOO": "blah,bleh"}):
            config = Config()

        # If no env_field is used, we don't pull from the environment.
        assert config.FOO == ("bar", "blah")

    def test_it_should_use_tuple_for_abstract_sequence(self):
        class Config(BaseConfig):
            FOO: Sequence[str] = env_field()

        with patch.dict(os.environ, {"FOO": "blah,bleh"}):
            config = Config()

        assert config.FOO == ("blah", "bleh")

    def test_it_should_reject_a_sequence_with_multiple_inner_types(self):
        class Config(BaseConfig):
            FOO: tuple[str, int] = env_field(default=("bar", 1))

        with pytest.raises(TypeError):
            Config()


class TestSecrets:
    def test_it_should_hold_a_secret(self):
        value = "s3kr1t"
        secret = Secret(value)
        assert secret == value

    def test_it_should_repr_a_secret_secretly(self):
        value = "s3kr1t"
        secret = Secret(value)
        assert repr(secret) == "Secret('**********')"


class TestBaseConfigGet:
    @pytest.fixture
    def Config(self):
        class Config(BaseConfig):
            BOOL: bool = env_field(default=True)

        return Config

    def test_it_should_get_an_undefined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("FOO", "true")
        assert Config().get("FOO") == "true"

    def test_it_should_get_an_undefined_env_value_default(self, Config, monkeypatch):
        assert Config().get("FOO", "true") == "true"

    def test_it_should_get_a_defined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("BOOL", "false")
        assert Config().get("BOOL") is False

    def test_it_should_raise_on_missing_value(self, Config, monkeypatch):
        with pytest.raises(KeyError):
            assert Config().get("FOO")


class TestBaseConfigGetTuple:
    @pytest.fixture
    def Config(self):
        class Config(BaseConfig):
            BOOLS: tuple[bool] = env_field(default=(True,))

        return Config

    def test_it_should_get_an_undefined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("FOO", "true")
        assert Config().get_tuple("FOO") == ("true",)

    def test_it_should_get_an_undefined_env_value_default(self, Config, monkeypatch):
        assert Config().get_tuple("FOO", "true") == ("true",)

    def test_it_should_get_a_defined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("BOOLS", "true,false")
        assert Config().get_tuple("BOOLS") == (True, False)

    def test_it_should_raise_on_missing_value(self, Config, monkeypatch):
        with pytest.raises(KeyError):
            assert Config().get_tuple("FOO")


class TestBaseConfigAsBool:
    @pytest.fixture
    def Config(self):
        class Config(BaseConfig):
            BOOL: bool = env_field(default=True)

        return Config

    def test_it_should_get_an_undefined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("FOO", "true")
        assert Config().as_bool("FOO") is True

    def test_it_should_get_an_undefined_env_value_default(self, Config, monkeypatch):
        assert Config().as_bool("FOO", True) is True

    def test_it_should_get_a_defined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("BOOL", "false")
        assert Config().as_bool("BOOL") is False

    def test_it_should_raise_on_missing_value(self, Config, monkeypatch):
        with pytest.raises(KeyError):
            assert Config().as_bool("FOO")


class TestBaseConfigAsBoolTuple:
    @pytest.fixture
    def Config(self):
        class Config(BaseConfig):
            BOOLS: tuple[bool] = env_field(default=(True,))

        return Config

    def test_it_should_get_an_undefined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("FOO", "true")
        assert Config().as_bool_tuple("FOO") == (True,)

    def test_it_should_get_an_undefined_env_value_default(self, Config, monkeypatch):
        assert Config().as_bool_tuple("FOO", (True,)) == (True,)

    def test_it_should_get_a_defined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("BOOLS", "true,false")
        assert Config().as_bool_tuple("BOOLS") == (True, False)

    def test_it_should_raise_on_missing_value(self, Config, monkeypatch):
        with pytest.raises(KeyError):
            assert Config().as_bool_tuple("FOO")


class TestBaseConfigAsInt:
    @pytest.fixture
    def Config(self):
        class Config(BaseConfig):
            INT: int = env_field(default=42)

        return Config

    def test_it_should_get_an_undefined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("FOO", "17")
        assert Config().as_int("FOO") == 17

    def test_it_should_get_an_undefined_env_value_default(self, Config, monkeypatch):
        assert Config().as_int("FOO", 17) == 17

    def test_it_should_get_a_defined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("INT", "17")
        assert Config().as_int("INT") == 17

    def test_it_should_raise_on_missing_value(self, Config, monkeypatch):
        with pytest.raises(KeyError):
            assert Config().as_int("FOO")


class TestBaseConfigAsIntTuple:
    @pytest.fixture
    def Config(self):
        class Config(BaseConfig):
            INTS: tuple[int] = env_field(default=(1, 2, 3))

        return Config

    def test_it_should_get_an_undefined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("FOO", "1,2,3")
        assert Config().as_int_tuple("FOO") == (1, 2, 3)

    def test_it_should_get_an_undefined_env_value_default(self, Config, monkeypatch):
        assert Config().as_int_tuple("FOO", (1, 2)) == (1, 2)

    def test_it_should_get_a_defined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("INTS", "1,2")
        assert Config().as_int_tuple("INTS") == (1, 2)

    def test_it_should_raise_on_missing_value(self, Config, monkeypatch):
        with pytest.raises(KeyError):
            assert Config().as_int_tuple("FOO")


class TestBaseConfigAsFloat:
    @pytest.fixture
    def Config(self):
        class Config(BaseConfig):
            FLOAT: float = env_field(default=42.0)

        return Config

    def test_it_should_get_an_undefined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("FOO", "17.0")
        assert Config().as_float("FOO") == 17.0

    def test_it_should_get_an_undefined_env_value_default(self, Config, monkeypatch):
        assert Config().as_float("FOO", 17.0) == 17.0

    def test_it_should_get_a_defined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("FLOAT", "17.0")
        assert Config().as_float("FLOAT") == 17.0

    def test_it_should_raise_on_missing_value(self, Config, monkeypatch):
        with pytest.raises(KeyError):
            assert Config().as_float("FOO")


class TestBaseConfigAsFloatTuple:
    @pytest.fixture
    def Config(self):
        class Config(BaseConfig):
            FLOATS: tuple[float] = env_field(default=(1.0, 2.0, 3.0))

        return Config

    def test_it_should_get_an_undefined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("FOO", "1.0,2.0,3.0")
        assert Config().as_float_tuple("FOO") == (1.0, 2.0, 3.0)

    def test_it_should_get_an_undefined_env_value_default(self, Config, monkeypatch):
        assert Config().as_float_tuple("FOO", (1.0, 2.0)) == (1.0, 2.0)

    def test_it_should_get_a_defined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("FLOATS", "1.0,2.0")
        assert Config().as_float_tuple("FLOATS") == (1.0, 2.0)

    def test_it_should_raise_on_missing_value(self, Config, monkeypatch):
        with pytest.raises(KeyError):
            assert Config().as_float_tuple("FOO")


class TestBaseConfigAsPath:
    @pytest.fixture
    def Config(self):
        class Config(BaseConfig):
            PATH: Path = env_field(default=Path("/foo/bar"))

        return Config

    def test_it_should_get_an_undefined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("FOO", "/foo")
        assert Config().as_path("FOO") == Path("/foo")

    def test_it_should_get_an_undefined_env_value_default(self, Config, monkeypatch):
        assert Config().as_path("FOO", "/foo") == Path("/foo")

    def test_it_should_get_a_defined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("PATH", "/foo")
        assert Config().as_path("PATH") == Path("/foo")

    def test_it_should_raise_on_missing_value(self, Config, monkeypatch):
        with pytest.raises(KeyError):
            assert Config().as_path("FOO")


class TestBaseConfigAsPathTuple:
    @pytest.fixture
    def Config(self):
        class Config(BaseConfig):
            PATHS: tuple[Path] = env_field(default=(Path("/foo"), Path("/bar")))

        return Config

    def test_it_should_get_an_undefined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("FOO", "/foo,/bar,/baz")
        assert Config().as_path_tuple("FOO") == (Path("/foo"), Path("/bar"), Path("/baz"))

    def test_it_should_get_an_undefined_env_value_default(self, Config, monkeypatch):
        assert Config().as_path_tuple("FOO", (Path("/foo"), Path("/bar"))) == (Path("/foo"), Path("/bar"))

    def test_it_should_get_a_defined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("PATHS", "/foo")
        assert Config().as_path_tuple("PATHS") == (Path("/foo"),)

    def test_it_should_raise_on_missing_value(self, Config, monkeypatch):
        with pytest.raises(KeyError):
            assert Config().as_path_tuple("FOO")


class TestBaseConfigAsSecret:
    @pytest.fixture
    def Config(self):
        class Config(BaseConfig):
            SECRET: Secret = env_field(default=Secret("/foo/bar"))

        return Config

    def test_it_should_get_an_undefined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("FOO", "/foo")
        assert Config().as_secret("FOO") == Secret("/foo")

    def test_it_should_get_an_undefined_env_value_default(self, Config, monkeypatch):
        assert Config().as_secret("FOO", "/foo") == Secret("/foo")

    def test_it_should_get_a_defined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("SECRET", "/foo")
        assert Config().as_secret("SECRET") == Secret("/foo")

    def test_it_should_raise_on_missing_value(self, Config, monkeypatch):
        with pytest.raises(KeyError):
            assert Config().as_secret("FOO")


class TestBaseConfigAsSecretTuple:
    @pytest.fixture
    def Config(self):
        class Config(BaseConfig):
            SECRETS: tuple[Secret] = env_field(default=(Secret("/foo"), Secret("/bar")))

        return Config

    def test_it_should_get_an_undefined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("FOO", "/foo,/bar,/baz")
        assert Config().as_secret_tuple("FOO") == (Secret("/foo"), Secret("/bar"), Secret("/baz"))

    def test_it_should_get_an_undefined_env_value_default(self, Config, monkeypatch):
        assert Config().as_secret_tuple("FOO", (Secret("/foo"), Secret("/bar"))) == (Secret("/foo"), Secret("/bar"))

    def test_it_should_get_a_defined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("SECRETS", "/foo")
        assert Config().as_secret_tuple("SECRETS") == (Secret("/foo"),)

    def test_it_should_raise_on_missing_value(self, Config, monkeypatch):
        with pytest.raises(KeyError):
            assert Config().as_secret_tuple("FOO")


class TestBaseConfigAsPackageImport:
    @pytest.fixture
    def Config(self):
        class Config(BaseConfig):
            PACKAGE: str = env_field(default="unittest.mock")

        return Config

    def test_it_should_get_an_undefined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("FOO", "unittest.mock")
        assert Config().as_package_import("FOO") == unittest.mock

    def test_it_should_get_an_undefined_env_value_default(self, Config, monkeypatch):
        assert Config().as_package_import("FOO", "unittest.mock") == unittest.mock

    def test_it_should_get_a_defined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("PACKAGE", "collections.abc")
        assert Config().as_package_import("PACKAGE") == collections.abc

    def test_it_should_raise_on_missing_value(self, Config, monkeypatch):
        with pytest.raises(KeyError):
            assert Config().as_package_import("FOO")


class TestBaseConfigAsPackageImportTuple:
    @pytest.fixture
    def Config(self):
        class Config(BaseConfig):
            PACKAGES: tuple[str] = env_field(default=("unittest.mock",))

        return Config

    def test_it_should_get_an_undefined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("FOO", "unittest.mock,collections.abc")
        assert Config().as_package_import_tuple("FOO") == (unittest.mock, collections.abc)

    def test_it_should_get_an_undefined_env_value_default(self, Config, monkeypatch):
        assert Config().as_package_import_tuple("FOO", ("unittest.mock", "collections.abc")) == (
            unittest.mock,
            collections.abc,
        )

    def test_it_should_get_a_defined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("PACKAGES", "collections.abc")
        assert Config().as_package_import_tuple("PACKAGES") == (collections.abc,)

    def test_it_should_raise_on_missing_value(self, Config, monkeypatch):
        with pytest.raises(KeyError):
            assert Config().as_package_import_tuple("FOO")


class TestBaseConfigAsObjectImport:
    @pytest.fixture
    def Config(self):
        class Config(BaseConfig):
            PACKAGE: str = env_field(default="unittest.mock.patch")

        return Config

    def test_it_should_get_an_undefined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("FOO", "unittest.mock.patch")
        assert Config().as_object_import("FOO") == patch

    def test_it_should_get_an_undefined_env_value_default(self, Config, monkeypatch):
        assert Config().as_object_import("FOO", "unittest.mock.patch") == patch

    def test_it_should_get_a_defined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("PACKAGE", "collections.abc:Sequence")
        assert Config().as_object_import("PACKAGE") == Sequence

    def test_it_should_raise_on_poorly_formed_import(self, Config, monkeypatch):
        monkeypatch.setenv("PACKAGE", "foo/bar")
        with pytest.raises(ValueError):
            assert Config().as_object_import("PACKAGE")

    def test_it_should_raise_on_missing_value(self, Config, monkeypatch):
        with pytest.raises(KeyError):
            assert Config().as_object_import("FOO")


class TestBaseConfigAsObjectImportTuple:
    @pytest.fixture
    def Config(self):
        class Config(BaseConfig):
            PACKAGES: tuple[str] = env_field(default=("unittest.mock.patch",))

        return Config

    def test_it_should_get_an_undefined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("FOO", "unittest.mock:patch,collections.abc.Sequence")
        assert Config().as_object_import_tuple("FOO") == (patch, Sequence)

    def test_it_should_get_an_undefined_env_value_default(self, Config, monkeypatch):
        assert Config().as_object_import_tuple("FOO", ("unittest.mock.patch", "collections.abc:Sequence")) == (
            patch,
            Sequence,
        )

    def test_it_should_get_a_defined_env_value(self, Config, monkeypatch):
        monkeypatch.setenv("PACKAGES", "collections.abc.Sequence")
        assert Config().as_object_import_tuple("PACKAGES") == (Sequence,)

    def test_it_should_raise_on_missing_value(self, Config, monkeypatch):
        with pytest.raises(KeyError):
            assert Config().as_object_import_tuple("FOO")


class TestBaseConfigAsDict:
    def test_it_should_convert_to_a_dict(self):
        class Config(BaseConfig):
            FOO: int = env_field(default=10)
            BAR: int = env_field(default=20)

        config = Config()

        assert config.asdict() == {"FOO": 10, "BAR": 20, "DEBUG": True, "TESTING": True}

    def test_it_should_convert_to_a_dict_with_specific_fields(self):
        class Config(BaseConfig):
            FOO: int = env_field(default=10)
            BAR: int = env_field(default=20)
            BAZ: int = env_field(default=30)

        config = Config()

        assert config.asdict(("FOO", "BAR")) == {"FOO": 10, "BAR": 20}


class TestConfigForwardRefs:
    def test_it_should_handle_forward_refs(self, monkeypatch):
        monkeypatch.setenv("FOO", "10")

        class Config(BaseConfig):
            FOO: "tuple[int]" = env_field()

        with pytest.raises(TypeError):
            # FIXME: We actually can't handle forward refs yet. :(
            Config()

        # assert config.FOO == 10


class TestReportSettings:
    def test_it_should_report_settings(self):
        class MyConfig(BaseConfig):
            """My configuration, not yours"""

            FOO: int = env_field(default=10, doc="Foo value")
            BAR: str = env_field(doc="Bar value")

        result = MyConfig.report_settings()
        expected = {
            "doc": "My configuration, not yours",
            "settings": {
                "DEBUG": {
                    "type": bool,
                    "default": False,
                    "doc": "Development mode?",
                },
                "TESTING": {
                    "type": bool,
                    "default": False,
                    "doc": "Testing mode?",
                },
                "FOO": {
                    "type": int,
                    "default": 10,
                    "doc": "Foo value",
                },
                "BAR": {
                    "type": str,
                    "default": UNDEFINED,
                    "doc": "Bar value",
                },
            },
        }
        assert result == expected


class TestGatherSettings:
    def test_it_should_gather_settings(self):
        class MyConfig(BaseConfig):
            """My configuration, not yours"""

            FOO: int = env_field(default=10, doc="Foo value")
            BAR: str = env_field(doc="Bar value")

        all_results = BaseConfig.gather_settings()
        result = project(all_results, ("convoke.configs.BaseConfig", "test_configs.MyConfig"))
        expected = {
            "convoke.configs.BaseConfig": {
                "doc": "Base settings common to all configurations",
                "settings": {
                    "DEBUG": {
                        "type": bool,
                        "default": False,
                        "doc": "Development mode?",
                    },
                    "TESTING": {
                        "type": bool,
                        "default": False,
                        "doc": "Testing mode?",
                    },
                },
            },
            "test_configs.MyConfig": {
                "doc": "My configuration, not yours",
                "settings": {
                    "FOO": {
                        "type": int,
                        "default": 10,
                        "doc": "Foo value",
                    },
                    "BAR": {
                        "type": str,
                        "default": UNDEFINED,
                        "doc": "Bar value",
                    },
                },
            },
        }
        assert result == expected


class TestGenerateDotEnv:
    @pytest.fixture(autouse=True)
    def secrets(self):
        with patch("secrets.token_urlsafe", return_value="toomanysecretsmarty"):
            yield

    @pytest.fixture
    def summary(self):
        return {
            "convoke.configs.BaseConfig": {
                "doc": "Base settings common to all configurations",
                "settings": {
                    "DEBUG": {
                        "type": bool,
                        "default": False,
                        "doc": "Development mode?",
                    },
                    "TESTING": {
                        "type": bool,
                        "default": False,
                        "doc": "Testing mode?",
                    },
                },
            },
            "test_configs.MyConfig": {
                "doc": "My configuration, not yours",
                "settings": {
                    "FOO": {
                        "type": int,
                        "default": 10,
                        "doc": "Foo value",
                    },
                    "BAR": {
                        "type": str,
                        "default": UNDEFINED,
                        "doc": "Bar value",
                    },
                    "BAZ": {
                        "type": tuple[str],
                        "default": ("baz", "bogey"),
                        "doc": "",
                    },
                    "BLAH_SECRET": {
                        "type": Secret,
                        "default": UNDEFINED,
                        "doc": "This must not get out.",
                    },
                },
            },
            "test_configs.NoDocConfig": {
                "doc": "",
                "settings": {
                    "FOO": {
                        "type": int,
                        "default": 10,
                        "doc": "Foo value",
                    },
                    "BAR": {
                        "type": str,
                        "default": UNDEFINED,
                        "doc": "Bar value",
                    },
                },
            },
            "test_configs.RedundantConfig": {
                "doc": "",
                "settings": {
                    "BAR": {
                        "type": str,
                        "default": UNDEFINED,
                        "doc": "Bar value",
                    },
                },
            },
        }

    def test_it_should_generate_a_dot_env(self, summary):
        result = generate_dot_env(summary)
        expected = (
            textwrap.dedent(
                """
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
                ## test_configs.MyConfig ##
                ###########################
                ##
                ## My configuration, not yours

                # ---------------
                # -- FOO (int) --
                # ---------------
                #
                # Foo value

                # This setting is also used in:
                # - test_configs.NoDocConfig
                FOO="10"

                # -----------------------------
                # -- BAR (str) **Required!** --
                # -----------------------------
                #
                # Bar value

                # This setting is also used in:
                # - test_configs.NoDocConfig
                # - test_configs.RedundantConfig
                BAR=""

                # -----------------
                # -- BAZ (tuple) --
                # -----------------

                BAZ="baz,bogey"

                # ----------------------------------------
                # -- BLAH_SECRET (Secret) **Required!** --
                # ----------------------------------------
                #
                # This must not get out.

                BLAH_SECRET="toomanysecretsmarty"


                ##############################
                ## test_configs.NoDocConfig ##
                ##############################
                # ---------------
                # -- FOO (int) --
                # ---------------
                #
                # Foo value

                # This setting is also used in:
                # - test_configs.MyConfig
                # and is already set above.
                #    FOO="10"

                # -----------------------------
                # -- BAR (str) **Required!** --
                # -----------------------------
                #
                # Bar value

                # This setting is also used in:
                # - test_configs.MyConfig
                # - test_configs.RedundantConfig
                # and is already set above in test_configs.MyConfig.
                #    BAR=""


                ##################################
                ## test_configs.RedundantConfig ##
                ##################################
                # -----------------------------
                # -- BAR (str) **Required!** --
                # -----------------------------
                #
                # Bar value

                # This setting is also used in:
                # - test_configs.MyConfig
                # - test_configs.NoDocConfig
                # and is already set above in test_configs.MyConfig.
                #    BAR=""
                """
            ).strip()
            + "\n"
        )
        assert result == expected

    def test_it_should_generate_a_dot_env_with_only_required(self, summary):
        result = generate_dot_env(summary, required_only=True)
        expected = (
            textwrap.dedent(
                """
                ###########################
                ## test_configs.MyConfig ##
                ###########################
                ##
                ## My configuration, not yours

                # -----------------------------
                # -- BAR (str) **Required!** --
                # -----------------------------
                #
                # Bar value

                # This setting is also used in:
                # - test_configs.NoDocConfig
                # - test_configs.RedundantConfig
                BAR=""

                # ----------------------------------------
                # -- BLAH_SECRET (Secret) **Required!** --
                # ----------------------------------------
                #
                # This must not get out.

                BLAH_SECRET="toomanysecretsmarty"


                ##############################
                ## test_configs.NoDocConfig ##
                ##############################
                # -----------------------------
                # -- BAR (str) **Required!** --
                # -----------------------------
                #
                # Bar value

                # This setting is also used in:
                # - test_configs.MyConfig
                # - test_configs.RedundantConfig
                # and is already set above in test_configs.MyConfig.
                #    BAR=""


                ##################################
                ## test_configs.RedundantConfig ##
                ##################################
                # -----------------------------
                # -- BAR (str) **Required!** --
                # -----------------------------
                #
                # Bar value

                # This setting is also used in:
                # - test_configs.MyConfig
                # - test_configs.NoDocConfig
                # and is already set above in test_configs.MyConfig.
                #    BAR=""
                """
            ).strip()
            + "\n"
        )
        assert result == expected
