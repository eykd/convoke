import pathlib
from unittest.mock import patch

import convoke
import pytest
from path import Path

import pendulum as pn


@pytest.fixture
def env(tmpdir):
    with patch("os.environ", {}) as env:
        env["DATA_DIR"] = str(tmpdir)
        yield env


@pytest.fixture
def cfg(env):
    return convoke.Settings('convoke')


def test_slugify():
    result = convoke._slugify('Foo Bar blaB')
    assert result == 'foo-bar-blab'


def test_debug_via_default(cfg, env):
    assert cfg.debug is False


def test_debug_via_env(env, cfg):
    env["DEBUG"] = "True"
    assert cfg.debug is True


def test_data_dir_via_default(cfg, tmpdir, env):
    assert cfg.data_dir == tmpdir


def test_data_dir_via_env(cfg, env, tmpdir):
    env["DATA_DIR"] = str(tmpdir / "foo")
    assert cfg.data_dir == tmpdir / "foo"


def test_resolve_convoke_should_handle_a_pathlib_path(tmpdir, env):
    convoke_file = pathlib.Path(tmpdir) / "convoke.ini"
    with open(convoke_file, "w") as fo:
        fo.write("debug=true")
    cfg = convoke.Settings('convoke', convoke_file)
    assert cfg.debug is True


def test_resolve_convoke_should_handle_a_missing_convoke(tmpdir, env):
    convoke_file = Path(tmpdir) / "convoke.ini"
    cfg = convoke.Settings('convoke', convoke_file)
    assert convoke_file.exists()
    assert cfg.debug is False


def test_get_should_raise_key_error_if_no_value_and_no_default_provided(cfg):
    with pytest.raises(KeyError):
        cfg.get("foo")


def test_get_should_return_a_default_if_no_value(cfg):
    result = cfg.get("foo", "bar")
    assert result == "bar"


def test_get_list_should_raise_key_error_if_no_value_and_no_default_provided(cfg):
    with pytest.raises(KeyError):
        cfg.get_list("foo")


def test_get_list_should_return_a_default_if_no_value(cfg):
    result = cfg.get_list("foo", ["bar"])
    assert result == ["bar"]


def test_get_list_should_return_a_default_list_if_only_string_provided(cfg):
    result = cfg.get_list("foo", "bar")
    assert result == ["bar"]


def test_get_list_should_raise_typeerror_if_non_iterablle_value(cfg):
    cfg.overrides['foo'] = 6
    with pytest.raises(TypeError):
        cfg.get_list("foo")


def test_as_bool_should_return_a_value_as_bool(env, cfg):
    for value in ('true', 'True', 'TRUE', '1'):
        env["FOO"] = value
        result = cfg.as_bool("foo")
        assert result is True
    for value in ('false', 'False', 'FALSE', '0'):
        env["FOO"] = value
        result = cfg.as_bool("foo")
        assert result is False


def test_as_bool_should_raise_for_a_non_boolean_value(env, cfg):
    env["FOO"] = "blah"
    with pytest.raises(ValueError):
        cfg.as_bool("foo")


def test_as_bool_should_read_none_as_false(cfg):
    result = cfg.as_bool("foo", None)
    assert result is False


def test_as_bool_list_should_return_a_value_as_bool_list(env, cfg):
    env["FOO"] = 'true,True,TRUE,1,false,False,FALSE,0'
    result = cfg.as_bool_list("foo")
    assert result == [True, True, True, True, False, False, False, False]


def test_as_bool_list_should_return_a_single_value_as_bool_list(env, cfg):
    env["FOO"] = 'true'
    result = cfg.as_bool_list("foo")
    assert result == [True]


def test_as_bool_list_should_raise_for_a_non_boolean_value(env, cfg):
    env["FOO"] = "foo,blah"
    with pytest.raises(ValueError):
        cfg.as_bool_list("foo")


def test_as_bool_list_should_read_none_default_as_empty_list(cfg):
    result = cfg.as_bool_list("foo", default=None)
    assert result == []


def test_as_int_should_return_a_value_as_int(env, cfg):
    env["FOO"] = "5"
    result = cfg.as_int("foo")
    assert result == 5


def test_as_int_list_should_return_a_value_as_int_list(env, cfg):
    env["FOO"] = "5,6"
    result = cfg.as_int_list("foo")
    assert result == [5, 6]


def test_as_float_should_return_a_value_as_float(env, cfg):
    env["FOO"] = "5.0"
    result = cfg.as_float("foo")
    assert result == 5.0


def test_as_float_list_should_return_a_value_as_float_list(env, cfg):
    env["FOO"] = "5.0,6.0"
    result = cfg.as_float_list("foo")
    assert result == [5.0, 6.0]


def test_get_timezone_should_return_it(env, cfg):
    expected = "America/Los_Angeles"
    with patch("pendulum.local_timezone") as patched:
        patched.return_value.name = expected
        result = cfg.get_timezone()
        assert result == expected


def test_utcnow_should_return_utcnow(env, cfg):
    expected = pn.now(tz="UTC")
    with patch("pendulum.now", return_value=expected) as patched:
        result = cfg.utcnow()
        assert result == expected
        patched.assert_called_once_with(tz="UTC")


def test_now_should_return_now_with_local_timezone(env, cfg):
    expected = pn.now()
    with patch("pendulum.now", return_value=expected) as patched:
        result = cfg.now()
        assert result == expected
        patched.assert_called_once_with(tz=pn.local_timezone().name)


def test_as_package_import_should_return_a_value_as_imported_package(env, cfg):
    env["PACKAGE"] = "pathlib"
    result = cfg.as_package_import("package")
    assert result is pathlib


def test_as_package_import_list_should_return_a_value_as_list_of_imported_packages(env, cfg):
    env["PACKAGE"] = "pathlib,pytest"
    result = cfg.as_package_import_list("package")
    assert result == [pathlib, pytest]


def test_as_object_import_should_return_a_value_as_imported_object(env, cfg):
    env["PACKAGE"] = "pathlib.Path"
    result = cfg.as_object_import("package")
    assert result is pathlib.Path


def test_as_object_import_should_raise_valueerror_for_bad_path(env, cfg):
    env["PACKAGE"] = "pathlib"
    with pytest.raises(ValueError):
        cfg.as_object_import("package")


def test_as_object_import_list_should_return_a_value_as_list_of_imported_objects(env, cfg):
    env["PACKAGE"] = "pathlib.Path,pytest.fixture"
    result = cfg.as_object_import_list("package")
    assert result == [pathlib.Path, pytest.fixture]
