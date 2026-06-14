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

class PromptSection(ttk.LabelFrame):
    """ Class and GUI Frame for running a prompt example and optionally chaining results into a
        search example.
    """

    def __init__(
        self,
        parent: tk.Widget,
        *,
        root: tk.Tk,
        start_row: int,
        async_bridge: AsyncTkBridge,
        output: TkOutput,
        get_client: Callable[[], McpClient | None],
        chain_search: Callable[[NormalizedQuery], None],
    ) -> None:
        """ Initialize the PromptSection frame.
            Args:
                parent: The parent widget.
                root: The root Tkinter window.
                start_row: The starting row for placing this widget.
                async_bridge: The AsyncTkBridge instance for handling async tasks.
                output: The TkOutput instance for writing output.
                get_client: A callable that returns the current MCP client or None.
                chain_search: A callable that takes the results of the prompt example and runs a
                              search example with them.
        """
        super().__init__(parent, text="Ping")
        self.root = root
        self.async_bridge = async_bridge
        self.output = output
        self.get_client = get_client
        self.chain_search = chain_search

        self.prompt_search_string_var = tk.StringVar(
            value="Find English language videos on python list comprehensions"
        )
        self.use_chain_search_var = tk.BooleanVar(value=False)


        self.build_frame(start_row=start_row)


    def build_frame(self, start_row: int) -> None:
        """ Build prompt example controls.
            Args:
                start_row: The starting row for placing this widget.
        """
        self.grid(row=start_row, column=0, sticky="ew", padx=8, pady=4)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        row=0
        ttk.Separator(self, orient="horizontal").grid(
            row=row,
            column=0,
            columnspan=5,
            sticky="ew",
            padx=4,
            pady=8,
        )
        row += 1
        ttk.Label(self, text="Prompt Example").grid(
            row=row,
            column=0,
            columnspan=5,
            sticky="w",
            padx=4,
            pady=(8, 2),
        )
        row += 1
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
            text="Chain Prompt resultsinto Search example",
            variable=self.use_chain_search_var,
        ).grid(
            row=row,
            column=0,
            columnspan=3,
            sticky="w",
            padx=4,
            pady=2,
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
        self.output.write(f"Prompt failed: {error}")

