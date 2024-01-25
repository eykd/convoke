# ruff: noqa: D100, D101, D102, D103
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from convoke.bases import HQ, Base
from convoke.configs import BaseConfig

PATH = Path(__file__).absolute().parent


class TestBase:
    def test_it_should_have_a_config(self, config: BaseConfig):
        class Main(Base):
            pass

        base = Main(hq=Mock(config=config))
        assert base.config.TESTING is True

    def test_it_should_get_the_current_base(self, config: BaseConfig):
        class Main(Base):
            pass

        base = Main(hq=Mock(config=config))

        assert Main.get_current() is base


class TestHQ:
    @pytest.fixture(autouse=True)
    def fakemodules(self):
        with BaseConfig.fresh_plugins():
            fakepath = str(PATH / "fakemodules")
            sys.path.insert(0, fakepath)
            yield

        sys.path.pop(sys.path.index(fakepath))
        for name in ("foo", "bar", "baz"):
            if name in sys.modules:
                del sys.modules[name]

    @pytest.fixture
    def hq(self, hq_base: HQ, config):
        hq = HQ(config=config)
        hq.load_dependencies(dependencies=["foo", "bar"])
        yield hq
        del hq
        hq_base.reset()

    def test_hq_should_have_a_config(self, hq: HQ):
        assert hq.config.TESTING is True

    def test_it_should_load_dependencies(self, hq: HQ):
        assert list(hq.bases) == ["foo", "baz", "bar"]  # <-- baz is a subdependency
        assert list(hq.bases["foo"].bases) == ["baz"]
        assert list(hq.bases["bar"].bases) == ["baz"]
        assert list(hq.bases["bar"].bases["baz"].bases) == ["foo"]

        assert isinstance(hq.bases["foo"], Base)
        assert hq.bases["foo"].config.BAR == "baz"

        assert isinstance(hq.bases["bar"], Base)
        assert hq.bases["foo"].config.TESTING is True

    def test_it_should_get_the_current_hq(self, hq: HQ):
        assert HQ.get_current() is hq
        assert True

    def test_it_should_reset(self, hq: HQ):
        HQ.current_instance.set("foo")
        hq.reset()
        assert HQ.current_instance.get() is hq
        assert hq.get_current() is hq

    async def test_it_should_send_a_sync_signal(self, hq: HQ):
        import foo

        await foo.FOO.send(value="foo", using=hq)
        foo_base = foo.Main.get_current()
        await asyncio.sleep(0)
        assert foo_base.foos == [foo.FOO.Message(value="foo")]

    async def test_it_should_send_an_async_signal(self, hq: HQ):
        import bar

        await bar.BAR.send(value="bar", using=hq)
        bar_base = bar.Main.get_current()
        await asyncio.sleep(0)
        assert bar_base.bars == [bar.BAR.Message(value="bar")]

    async def test_it_should_disconnect_a_signal(self, hq: HQ):
        import foo

        foo_base = foo.Main.get_current()
        hq.disconnect_signal_receiver(foo.FOO, foo_base.on_foo)
        await foo.FOO.send(value="foo", using=hq)
        assert foo_base.foos == []

    async def test_it_should_use_mountpoints(self, hq: HQ):
        import baz

        baz_base = baz.Main.get_current()
        await baz.BAZ.send(value="a thing", using=hq)
        await asyncio.sleep(0)
        assert baz_base.things == ["a thing"]
        assert baz_base.other_things == ["a thing"]
