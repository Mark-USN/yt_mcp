""" Prompt section containing GUI elements and controls for running a prompt example and
    optionally chaining results into a search example.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections.abc import Callable
from modules.mcp_clients.client_mods.tk_async import AsyncTkBridge
from modules.mcp_clients.client_mods.tk_output import TkOutput, TkAfterOutputSink
from modules.mcp_clients.client_mods.mcp_client import McpClient
from modules.mcp_clients.client_mods.examples.prompt_example import PromptExample
from modules.utils.client_prompt_data import NormalizedQuery

# pylint: disable=too-many-ancestors, too-many-instance-attributes
class PromptSection(ttk.LabelFrame):
    """ Class and GUI Frame for running a prompt example and optionally chaining results into a
        search example.
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
        on_chain_change: Callable[[bool], None],
        chain_search: Callable[[NormalizedQuery], None],
    ) -> None:
        """ Initialize the PromptSection frame.
            Args:
                parent: The parent widget.
                root: The root Tkinter window.
                row: The starting row for placing this widget.
                async_bridge: The AsyncTkBridge instance for handling async tasks.
                output: The TkOutput instance for writing output.
                get_client: A callable that returns the current MCP client or None.
                chain_search: A callable that takes the results of the prompt example and runs a
                              search example with them.
        """
        super().__init__(parent, text="Prompt")
        self.root = root
        self.async_bridge = async_bridge
        self.output = output
        self.get_client = get_client
        self.on_chain_change = on_chain_change
        self.chain_search = chain_search

        self.prompt_search_string_var = tk.StringVar(
            value="Find English language videos on python list comprehensions"
        )
        self.use_chain_search_var = tk.BooleanVar(value=False)


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
        """ Build prompt example controls.
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
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        row=0
        ttk.Label(self, text="Search string:").grid(
            row=row,
            column=0,
            sticky="w",
            padx=4,
            pady=4,
        )

        ttk.Entry(self, textvariable=self.prompt_search_string_var).grid(
            row=row,
            column=1,
            columnspan=3,
            sticky="ew",
            padx=4,
            pady=4,
        )
        row += 1

        ttk.Checkbutton(
            self,
            text="Link to Search.",
            variable=self.use_chain_search_var,
        ).grid(
            row=row,
            column=0,
            columnspan=3,
            sticky="w",
            padx=4,
            pady=2,
        )

        self.use_chain_search_var.trace_add(
            "write",
            self._handle_chain_search_changed,
        )



        ttk.Button(
            self,
            text="Run Prompt",
            command=self.run,
        ).grid(
            row=row,
            column=3,
            padx=4,
            pady=4,
            sticky="e",
        )


    def _handle_chain_search_changed(
                                            self,
                                            *_args: object,
                                        ) -> None:
        self.on_chain_change(self.use_chain_search_var.get())



    def run(self) -> None:
        """ Run the prompt example with the provided search string. If successful, writes the
            results to the output section. If an error occurs, writes the error message to the
            output section.
        """
        client = self.get_client()
        if client is None:
            self.output.section("Prompt Example")
            self.output.line("No valid MCP client available.")
            return


        search_string = self.prompt_search_string_var.get().strip()
        if not search_string:
            self.output.section("Prompt Example")
            self.output.line("Search string is required.")
            return

        self.output.section("Run Prompt Example")

        # self.safe_out_sync = TkAfterOutputSink(root=self.root, output=self.output)

        example = PromptExample(
            client,
            emit=TkAfterOutputSink(self.root, self.output),
        )

        self.async_bridge.submit(
            example.run(search_string),      # <- async coroutine submitted here
            on_done=self._on_done,
            on_error=self._on_error,
            tk_after=self.root.after,
        )

    def _on_done(self, ai_query_results) -> None:
        """ Handle successful completion of the prompt example by writing results to output and
            optionally chaining the results into a search example.
            Args:
                ai_query_results: The results returned from the prompt example, which may be used
        """
        use_chain_search = self.use_chain_search_var.get()
        if use_chain_search and self.chain_search is not None:
            self.chain_search(ai_query_results)

    def _on_error(self, error: Exception) -> None:
        """ Handle an error from the prompt example by writing the error message to output.
            Args:
                error: The exception raised during the prompt example execution.
        """
        self.output.line(f"Prompt failed: {error}")
