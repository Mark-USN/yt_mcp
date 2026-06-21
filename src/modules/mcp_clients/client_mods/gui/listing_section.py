""" GUI section for listing server capabilities like tools, resources, templates, and prompts."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk
from fastmcp.client.client import CallToolResult
from modules.mcp_clients.client_mods.tk_async import AsyncTkBridge
from modules.mcp_clients.client_mods.tk_output import TkOutput
from modules.mcp_clients.client_mods.mcp_client import McpClient

LIST_TYPES = ("tools", "resources", "templates", "prompts")

# pylint: disable=too-many-ancestors
class ListingSection(ttk.LabelFrame):
    """ Section (Frame)for listing server capabilities like tools, resources, templates, and
        prompts.
    """

    def __init__(
        self,
        parent: tk.Widget,
        *,
        root: tk.Tk,
        row: int,
        column: int = 0,
        rowspan: int = 1,
        columnspan: int = 1,
        sticky: str = "ew",
        async_bridge: AsyncTkBridge,
        output: TkOutput,
        get_client: Callable[[], McpClient | None],
    ) -> None:
        """ Create and initialize the ListingSection frame.

        Args:
            parent: The parent Tk widget.
            root: The root Tk instance.
            row: The starting row for placing this widget.
            async_bridge: The asynchronous bridge for running tasks.
            output: The output sink for displaying messages.
            get_client: A callable that returns an MCP client or None.
        """

        super().__init__(parent, text="Server Capabilities Listings")
        self.root = root
        self.async_bridge = async_bridge
        self.output = output
        self.get_client = get_client

        self.grid(row=1, column=0, sticky="ew", padx=8, pady=4)
        self.list_vars = {name: tk.BooleanVar(value=True) for name in LIST_TYPES}
        self.build_frame(
                            row=row,
                            column=column,
                            rowspan=rowspan,
                            columnspan=columnspan,
                            sticky=sticky,
                        )


    def build_frame(
                        self,
                        row: int,
                        column: int = 0,
                        rowspan: int = 1,
                        columnspan: int = 1,
                        sticky: str = "ew",
                    ) -> None:
        """ Build the GUI's server listing controls.

            Args:
                row: The starting row for placing this widget.
        """
        self.grid(
                    row=row,
                    column=column,
                    rowspan=rowspan,
                    columnspan=columnspan,
                    sticky=sticky,
                    padx=8,
                    pady=4,
                )
        self.columnconfigure(2, weight=1)
        self.rowconfigure(1, weight=1)

        row = 0
        for index, name in enumerate(LIST_TYPES):
            ttk.Checkbutton(
                self,
                text=name,
                variable=self.list_vars[name],
            ).grid(
                row=row,
                column=index,
                padx=4,
                pady=4,
                sticky="w",
            )
        row += 1

        ttk.Button(
            self,
            text="Select All",
            command=self.select_all_lists,
        ).grid(
            row=row,
            column=0,
            padx=4,
            pady=4,
            sticky="w",
        )

        ttk.Button(
            self,
            text="Clear All",
            command=self.clear_all_lists,
        ).grid(
            row=row,
            column=1,
            padx=4,
            pady=4,
            sticky="w",
        )

        ttk.Button(
            self,
            text="List Items",
            command=self.on_list_items,
        ).grid(
            row=row,
            column=3,
            padx=4,
            pady=4,
            sticky="e",
        )

    def selected_list_types(self) -> set[str]:
        """ Return the currently selected MCP server components to list. """

        return { name for name, var in self.list_vars.items() if var.get() }


    def select_all_lists(self) -> None:
        """ Select all MCP listing checkboxes."""

        for var in self.list_vars.values():
            var.set(True)


    def clear_all_lists(self) -> None:
        """ Clear all MCP listing checkboxes."""

        for var in self.list_vars.values():
            var.set(False)


    def on_list_items(self) -> None:
        """ Actually query the MCP server for the selected listing types and display the
            results.
        """

        client = self.get_client()
        if client is None:
            self.output.section("Server Capabilities Listings")
            self.output.line("No valid MCP client available.")
            return


        selected = self.selected_list_types()
        if selected is None:
            return

        self.output.section(f"List MCP items: {', '.join(sorted(selected))}")

        self.async_bridge.submit(
            client.list_selected(selected),
            on_done=self._show_list_results,
            on_error=self._on_error,
            tk_after=self.root.after,
        )


    def _show_list_results(self, results: dict[str, CallToolResult]) -> None:
        """ Display the results of the MCP server listing query in the output pane.
            Args:
                results: A dictionary mapping listing types (e.g. "tools") to lists of items
                returned by the MCP server. 
        """
        for list_type, list_results in results.items():
            self.output.section(list_type.title())

            for item in list_results:
                name = (
                    getattr(item, "name", None)
                    or getattr(item, "uri", None)
                    or getattr(item, "uriTemplate", None)
                    or repr(item)
                )
                self.output.line(f"- {name}")


    def _on_error(self, error: Exception) -> None:
        """ Display an error message in the output pane if the listing query fails. """
        self.output.line(f"Server Capabilities Listing failed: {error}")
