# ruff: noqa: D103
"""Global pytest fixtures"""
import os
import tempfile
from pathlib import Path
import pytest

from convoke import current_hq
from convoke.configs import BaseConfig
from convoke.bases import HQ


@pytest.fixture(scope="session", autouse=True)
def auto_env_base():
    old_environ = dict(os.environ)
    os.environ.clear()
    for key, value in old_environ.items():
        if key.startswith("PYTEST"):
            os.environ[key] = value

    os.environ.update(
        {
            "DEBUG": "True",
            "TESTING": "True",
        }
    )
    yield os.environ
    os.environ.clear()
    os.environ.update(old_environ)


@pytest.fixture
def tempdir() -> str:
    with tempfile.TemporaryDirectory() as tempdir:
        yield Path(tempdir)


@pytest.fixture
def config(tempdir) -> BaseConfig:
    return BaseConfig()


@pytest.fixture(scope="session")
def hq_base(auto_env_base) -> HQ:
    hq = HQ()
    token = current_hq.set(hq)
    hq.load_dependencies([])
    yield hq
    current_hq.reset(token)
    del hq
