"""Utilities for managing signals and signal handlers"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from convoke import current_hq

if TYPE_CHECKING:  # pragma: nocover
    from convoke.bases import HQ

Receiver = Callable[..., None]


class Signal:
    """A Signal provides a typed interface for sending messages through the current HQ.

    To define a signal, subclass and provide a member class `Message`,
    which defines the keyword arguments that may be sent through the
    signal.

    """

    @dataclass
    class Message:
        """The default message type for signals.

        Define your own Message dataclass on each Signal for type-safe signals.
        """

        value: str

    @classmethod
    def connect(cls, receiver: Receiver, using: HQ | None = None):
        """Connect a callable to this signal."""
        if using is None:
            using = current_hq.get()
        using.connect_signal_receiver(cls, receiver)

    @classmethod
    def disconnect(cls, receiver: Receiver, using: HQ | None = None):
        """Disconnect a previously-connected callable."""
        if using is None:
            using = current_hq.get()
        using.disconnect_signal_receiver(cls, receiver)

    @classmethod
    async def send(cls, *, using: HQ | None = None, **kwargs):
        """Send a message over this Signal.

        Messages are sent asynchronously. Do not depend on side
        effects to happen immediately.

        """
        msg = cls.Message(**kwargs)
        if using is None:
            using = current_hq.get()
        await using.send_signal(cls, msg)
