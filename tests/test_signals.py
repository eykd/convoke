# ruff: noqa: D100, D101, D102, D103, D106
import asyncio
from dataclasses import dataclass, field
from unittest.mock import Mock

import pytest

from convoke import current_hq
from convoke.bases import HQ
from convoke.signals import Signal


class MY_SIGNAL(Signal):
    """This is my signal. There are many like it, but this one is mine."""

    @dataclass
    class Message:
        zoom: int = field(default=10)


@pytest.fixture(autouse=True)
def hq(config):
    """Simple HQ, no dependencies."""
    hq = HQ(config=config)
    token = current_hq.set(hq)
    yield hq
    current_hq.reset(token)
    del hq


async def test_it_should_broadcast_a_message_to_an_async_handler():
    signal = MY_SIGNAL()
    mock = Mock()

    async def handler(msg):
        mock(msg)

    signal.connect(handler)

    await signal.send(zoom=5)
    await asyncio.sleep(0)

    mock.assert_called_once_with(MY_SIGNAL.Message(zoom=5))


async def test_it_should_broadcast_a_message_to_a_sync_handler():
    signal = MY_SIGNAL()
    mock = Mock()

    def handler(msg):
        mock(msg)

    signal.connect(handler)

    await signal.send(zoom=5)
    await asyncio.sleep(0)

    mock.assert_called_once_with(MY_SIGNAL.Message(zoom=5))


async def test_it_should_connect_and_disconnect():
    signal = MY_SIGNAL()
    mock1 = Mock()
    mock2 = Mock()

    async def handler1(msg):
        mock1(msg)

    async def handler2(msg):
        mock2(msg)

    signal.connect(handler1)
    signal.connect(handler2)
    signal.disconnect(handler1)

    await signal.send(zoom=5)
    await asyncio.sleep(0)

    mock1.assert_not_called()
    mock2.assert_called_once_with(MY_SIGNAL.Message(zoom=5))


async def test_it_should_connect_and_disconnect_using(hq: HQ):
    signal = MY_SIGNAL()
    mock1 = Mock()
    mock2 = Mock()

    async def handler1(msg):
        mock1(msg)

    async def handler2(msg):
        mock2(msg)

    signal.connect(handler1, using=hq)
    signal.connect(handler2, using=hq)
    signal.disconnect(handler1, using=hq)

    await signal.send(zoom=5, using=hq)
    await asyncio.sleep(0)

    mock1.assert_not_called()
    mock2.assert_called_once_with(MY_SIGNAL.Message(zoom=5))
