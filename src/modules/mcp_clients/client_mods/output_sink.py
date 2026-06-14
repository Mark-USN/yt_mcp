""" Defines the OutputSink protocol, which represents a callable that can be used to send output
    messages to a UI or other output target. Also provides a NullOutputSink that does nothing
    when called.
"""
from __future__ import annotations

from typing import Protocol


class OutputSink(Protocol):
    """ Protocol representing a callable that can be used to send output messages to a UI or other
        output target.
    """
    def __call__(self, message: str = "") -> None:
        """Send a line of output to the current UI/output target."""


NullOutputSink: OutputSink = lambda message="": None