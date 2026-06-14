""" Provides a thread-safe output mechanism for Tkinter applications."""

from __future__ import annotations

from functools import partial
import tkinter as tk
from tkinter.scrolledtext import ScrolledText


class TkOutput:
    """ A thread-safe output mechanism for Tkinter applications, allowing messages to be written
        to a ScrolledText widget from any thread.
    """
    def __init__(self, root: tk.Tk, text: ScrolledText) -> None:
        """ Initialize the TkOutput instance.
            Args:
                root: The root Tkinter window, used for scheduling thread-safe updates.
                text: The ScrolledText widget where messages will be displayed.
        """
        self.root = root
        self.text = text

    def write_threadsafe(self, message: str) -> None:
        """ Write a message to the output widget in a thread-safe manner.
            Args:
                message: The message to be written to the output widget.
        """
        self.root.after(0, lambda: self._write(message))

    def line_threadsafe(self, message: str = "") -> None:
        """ Write a line to the output widget in a thread-safe manner.
            Args:
                message: The message to be written to the output widget.
        """
        self.write_threadsafe(f"{message}\n")

    def section_threadsafe(self, title: str) -> None:
        """ Write a section header to the output widget in a thread-safe manner.
            Args:
                title: The title of the section.
        """
        self.write_threadsafe(
            "\n"
            f"{'=' * 72}\n"
            f"{title}\n"
            f"{'=' * 72}\n"
        )

    def _write(self, message: str) -> None:
        """ Write a message to the output widget. This method should only be called from the main
            thread.
            Args:
                message: The message to be written to the output widget.
        """
        self.text.configure(state="normal")
        self.text.insert(tk.END, message)
        self.text.see(tk.END)
        self.text.configure(state="normal")

    def section(self, title: str) -> None:
        """ Write a section header to the output widget. This method should only be called from the main
            thread.
            Args:
                title: The title of the section.
        """
        self._write(
            "\n"
            f"{'=' * 72}\n"
            f"{title}\n"
            f"{'=' * 72}\n"
        )

    def line(self, message: object = "") -> None:
        """ Write a line to the output widget. This method should only be called from the main
            thread.
            Args:
                message: The message to be written to the output widget.
        """
        self._write(f"{message}\n")



class TkAfterOutputSink:
    """ An output sink that schedules messages to be written to a TkOutput instance in a
        thread-safe manner.
    """
    def __init__(self, root: tk.Tk, output: TkOutput) -> None:
        """ Initialize the TkAfterOutputSink instance.
            Args:
                root: The root Tkinter window, used for scheduling thread-safe updates.
                output: The TkOutput instance where messages will be written.
        """
        self.root = root
        self.output = output

    def __call__(self, message: str = "") -> None:
        """ Schedule a message to be written to the output widget in a thread-safe manner.
            Args:
                message: The message to be written to the output widget.
        """
        self.root.after(0, partial(self.output.line, message))
