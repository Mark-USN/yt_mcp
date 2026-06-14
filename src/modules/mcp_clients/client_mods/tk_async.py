""" Run asyncio work on a background loop and return results to Tkinter."""
from __future__ import annotations

import asyncio
import threading
from collections.abc import Awaitable, Callable
from concurrent.futures import Future
from typing import TypeVar

T = TypeVar("T")


class AsyncTkBridge:
    """Run asyncio work on a background loop and return results to Tkinter."""

    def __init__(self) -> None:
        """ Initialize the AsyncTkBridge by starting a background thread with an asyncio event
            loop.
        """
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="mcp-async-loop",
            daemon=True,
        )
        self._thread.start()

    def _run_loop(self) -> None:
        """ Target function for the background thread that runs the asyncio event loop. """
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def submit(
        self,
        coro: Awaitable[T],
        *,
        on_done: Callable[[T], None],
        on_error: Callable[[BaseException], None],
        tk_after: Callable[[int, Callable[[], None]], object],
    ) -> Future[T]:
        """ Submit a coroutine to be run on the background event loop, with callbacks for when it's
            done.
            Args:
                coro: The coroutine to run.
                on_done: Callback to be called with the result when the coroutine completes successfully.
                on_error: Callback to be called with the exception if the coroutine raises an error.
                tk_after: Function to schedule a callback to be run on the Tkinter main thread.
        """
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)

        def done_callback(done: Future[T]) -> None:
            try:
                result = done.result()
            except BaseException as exc:                    # pylint: disable=broad-except
                tk_after(0, lambda: on_error(exc))
            else:
                tk_after(0, lambda: on_done(result))

        future.add_done_callback(done_callback)
        return future

    def close(self) -> None:
        """ Cleanly shut down the background event loop and thread. """

        self._loop.call_soon_threadsafe(self._loop.stop)
