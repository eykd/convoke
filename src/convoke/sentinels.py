"""Sentinel values for the convoke web framework"""
from typing import Type


class UNDEFINED:
    """Sentinel for undefined values; never instantiated"""

    def __init__(self):  # pragma: nocover
        raise NotImplementedError


TUndefined = Type[UNDEFINED]
