""" Output section of the GUI, containing a scrolling text area for output display."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from modules.mcp_clients.client_mods.tk_output import TkOutput


class OutputSection(ttk.LabelFrame):
    """ The output section of the GUI, containing a scrolling text area for output display. """

    def __init__(
        self,
        parent: tk.Widget,
        *,
        root: tk.Tk,
        start_row: int,
    ) -> None:
        """ Initialize the output section.

            Args:
                parent: The parent widget.
                root: The root Tkinter window.
                start_row: The starting row for placing this widget.
        """

        super().__init__(parent, text="Output")

        self.root = root
        self.build_frame(start_row=start_row)


    def build_frame(self, start_row: int) -> None:
        """ Build the scrolling output text area.

            Args:
                start_row: The starting row for placing this widget.
        """
        self.grid(row=start_row, column=0, sticky="nsew", padx=8, pady=4)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.output_text = ScrolledText(self, wrap="word", height=24)
        self.output_text.grid(row=0, column=0, sticky="nsew")

        self.output = TkOutput(self.root, self.output_text)

    def get_output(self) -> TkOutput:
        """ Get the TkOutput instance, which provides a thread-safe way to write to the output text area.

            Returns:
                The TkOutput instance.
        """
        return self.output

