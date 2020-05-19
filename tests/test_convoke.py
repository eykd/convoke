import pathlib
from unittest.mock import patch

import pytest
from path import Path

import convoke


@pytest.fixture
def env(tmpdir):
    with patch("os.environ", {}) as env:
        env["DATA_DIR"] = str(tmpdir)
        yield env


@pytest.fixture
def cfg(env):
    return convoke.Settings('convoke')


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


def test_it_should_return_a_value_as_bool(env, cfg):
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


def test_it_should_return_a_value_as_int(env, cfg):
    env["FOO"] = "5"
    result = cfg.as_int("foo")
    assert result == 5


def test_it_should_return_a_value_as_float(env, cfg):
    env["FOO"] = "5.0"
    result = cfg.as_float("foo")
    assert result == 5.0
