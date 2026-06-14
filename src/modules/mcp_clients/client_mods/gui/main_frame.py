
""" Main frame for MCP client operations, containing sections for pinging, listing, and examples.
    And disabled until a connection is established.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections.abc import Callable
from yt_lib.utils.app_context import RuntimeContext
from modules.mcp_clients.client_mods.tk_async import AsyncTkBridge
from modules.mcp_clients.client_mods.tk_output import TkOutput
from modules.mcp_clients.client_mods.mcp_client import McpClient
from modules.mcp_clients.client_mods.gui.ping_section import PingSection
from modules.mcp_clients.client_mods.gui.listing_section import ListingSection
from modules.mcp_clients.client_mods.gui.examples_frame import ExamplesFrame


class MainFrame(ttk.LabelFrame):
    """ The main frame for MCP client operations, containing sections for pinging, listing, and
        examples. Everything except the root Frame, the Connection Section and the Output Section 
        is a child of this Frame.  The child widgets can be easily managed and disabled until a
        connection is established.
    """

    def __init__(
        self,
        parent: tk.Widget,
        *,
        root: tk.Tk,
        ctx: RuntimeContext,
        start_row: int,
        async_bridge: AsyncTkBridge,
        output: TkOutput,
        get_client: Callable[[], McpClient | None],
    ) -> None:
        """ Initialize the main frame for MCP client operations.

            Args:
                parent: The parent widget.
                root: The root Tkinter window.
                ctx: The runtime context, providing access to app directories and other shared
                     resources.
                start_row: The starting row for placing this widget.
                async_bridge: The asynchronous bridge for Tkinter.
                output: The output widget.
                get_client: A callable that returns the MCP client or None.
        """

        super().__init__(parent, text="MCP Client Operations")

        self.root = root
        self.async_bridge = async_bridge
        self.output = output
        self.get_client = get_client

        self.build_frame(ctx=ctx, start_row=start_row)



    def build_frame(self, ctx: RuntimeContext, start_row: int) -> None:
        """ Build the server ping and listing sections and contain the Examples frame.
            Args:
                ctx: The runtime context, providing access to app directories and other shared
                     resources.
                start_row: The starting row for placing this widget.
        """

        self.grid(row=start_row, column=0, sticky="nsew")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        row = 0

        self.ping_section = PingSection(
                                parent = self,
                                root = self.root,
                                start_row = row,
                                async_bridge = self.async_bridge,
                                output = self.output,
                                get_client = self.get_client,
                           )
        row += 1

        self.listing_section = ListingSection(
                                parent = self,
                                root = self.root,
                                start_row = row,
                                async_bridge = self.async_bridge,
                                output = self.output,
                                get_client = self.get_client,
                            )
        row += 1
        self.examples_frame = ExamplesFrame(
                                parent = self,
                                root = self.root,
                                ctx = ctx,
                                start_row = row,
                                async_bridge = self.async_bridge,
                                output = self.output,
                                get_client = self.get_client,
                            )


    def set_gui_state(self, enabled: bool) -> None:
        """ Enable or disable all controls that require an MCP client.

            Args:
                enabled: A boolean indicating whether to enable or disable the controls.
        """

        state = "normal" if enabled else "disabled"

        for child in self.winfo_children():
            self._set_widget_tree_state(child, state)


    def _set_widget_tree_state(self, widget: tk.Widget, state: str) -> None:
        """ Recursively set widget state where supported.

            Args:
                widget: The widget whose state is to be set.
                state: The state to set ("normal" or "disabled").
        """

        try:
            widget.configure(state=state)
        except tk.TclError:
            pass

        for child in widget.winfo_children():
            self._set_widget_tree_state(child, state)

