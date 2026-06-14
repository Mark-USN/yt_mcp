""" GUI section for search example controls."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections.abc import Callable
from mcp.types import CallToolResult
from modules.mcp_clients.client_mods.tk_async import AsyncTkBridge
from modules.mcp_clients.client_mods.tk_output import TkOutput
from modules.mcp_clients.client_mods.mcp_client import McpClient
from modules.mcp_clients.client_mods.examples.search_example import SearchExample
from modules.utils.client_prompt_data import NormalizedQuery

DEFAULT_RESULTS = 10            # Default value for max results in search example the actual max
                                # is 50, but start with a lower default to encourage testing with
                                # smaller numbers.


class SearchSection(ttk.LabelFrame):
    """ Class that represents the GUI section for search example controls. """

    search_string_var: tk.StringVar
    max_results_var: tk.StringVar
    chain_transcript_var: tk.BooleanVar

    def __init__(
        self,
        parent: tk.Widget,
        *,
        root: tk.Tk,
        start_row: int,
        async_bridge: AsyncTkBridge,
        output: TkOutput,
        get_client: Callable[[], McpClient | None],
        on_chain_transcript: Callable[[CallToolResult], None],
    ) -> None:
        """ Initialize the SearchSection frame.
            Args:
                parent: The parent widget.
                root: The root Tkinter window.
                start_row: The starting row for placing this widget.
                async_bridge: The asynchronous bridge for handling async tasks.
                output: The output widget for displaying results.
                get_client: A callable that returns the MCP client.
                on_chain_transcript: A callable that handles chaining search results into a transcript example.
        """
        super().__init__(parent, text="Search")
        self.root = root
        self.async_bridge = async_bridge
        self.output = output
        self.search_string_var = tk.StringVar(value="Dihydrogen Monoxide risks and mitigation strategies")
        self.max_results_var = tk.StringVar(value=str(DEFAULT_RESULTS))
        self.get_client = get_client
        self.on_chain_transcript = on_chain_transcript
        self.build_frame(start_row=start_row)


    def build_frame(self, start_row: int) -> None:
        """ Build search example controls.
            Args:
                start_row: The starting row for placing this widget.

            This frame is inside main_controls, so it starts disabled until connected.
        """

        self.grid(row=start_row, column=0, sticky="ew", padx=8, pady=4)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        row = 0
        ttk.Separator(self, orient="horizontal").grid(
            row=row,
            column=0,
            columnspan=5,
            sticky="ew",
            padx=4,
            pady=8,
        )
        row += 1

        ttk.Label(self, text="Search Example").grid(
            row=row,
            column=0,
            columnspan=5,
            sticky="w",
            padx=4,
            pady=(4, 2),
        )
        row += 1

        ttk.Label(self, text="Search:").grid(
            row=row,
            column=0,
            sticky="w",
            padx=4,
            pady=4,
        )

        ttk.Entry(self, textvariable=self.search_string_var).grid(
            row=row,
            column=1,
            sticky="ew",
            padx=4,
            pady=4,
        )

        ttk.Label(self, text="Max:").grid(
            row=row,
            column=2,
            sticky="e",
            padx=4,
            pady=4,
        )

        ttk.Spinbox(
            self,
            from_=1,
            to=50,
            textvariable=self.max_results_var,
            width=5,
        ).grid(
            row=row,
            column=3,
            sticky="w",
            padx=4,
            pady=4,
        )
        row += 1

        ttk.Checkbutton(
            self,
            text="Chain search results into transcript example",
            variable=self.chain_transcript_var,
        ).grid(
            row=row,
            column=1,
            columnspan=4,
            sticky="w",
            padx=4,
            pady=2,
        )

        ttk.Button(
            self,
            text="Run Search",
            command=self.run,
        ).grid(
            row=row,
            column=4,
            padx=4,
            pady=4,
            sticky="e",
        )

    def _parse_url_list(self, value: str) -> list[str]:
        """ Parse one or more URLs from a comma/newline/space separated field.
            Args:
                value: The input string containing URLs separated by commas, newlines, or spaces.
            Returns:
                A list of parsed URLs.
        """

        raw_parts = value.replace(",", "\n").splitlines()
        urls: list[str] = []

        for part in raw_parts:
            urls.extend(piece.strip() for piece in part.split())

        return [url for url in urls if url]


    def _parse_max_results(self) -> int | None:
        """ Parse the max results value from the input field, ensuring it's a valid integer
            between 1 and 50.
            Returns:
                The parsed max results as an integer, or None if the input is invalid.
        """
        text = self.max_results_var.get().strip()

        try:
            max_results = int(text)
        except ValueError:
            self.output.section("Search Example")
            self.output.line("Max results must be a number.")
            return None

        if not 1 <= max_results <= 50:
            self.output.section("Search Example")
            self.output.line("Max results must be between 1 and 50.")
            return None

        return max_results


    def run(self,use_chain_search: bool= False, ai_query_results: NormalizedQuery | None = None) -> None:
        """ Run the search example with the provided search string and max results. If successful,
            writes the results to the output section. If an error occurs, writes the error message to the
            output section.
            Args:
                use_chain_search: Whether to use the results from a previous AI query.
                ai_query_results: The results from a previous AI query, if any. 
        """
        client = self.get_client()
        if client is None:
            self.output.section("Search Example")
            self.output.line("No valid MCP client available.")
            return


        max_results = self._parse_max_results()
        if max_results is None:
            self.output.section("Search Example")
            self.output.line("Max results must be a number between 1 and 50.")
            return

        search_string = self.search_string_var.get().strip()
        if not search_string:
            self.output.section("Search Example")
            self.output.line("Search string is required.")
            return

        chain_transcript = self.chain_transcript_var.get()

        self.output.section("Run Search Example")
        self.output.line(f"Search string: {search_string}")
        self.output.line(f"Max results: {max_results}")
        self.output.line(f"Chain transcript: {chain_transcript}")

        example = SearchExample(
            client,
            emit=self.output.line_threadsafe,
        )
        if use_chain_search:
            coro = example.run_ai(ai_query_results, max_results)
        else:
            coro = example.run(search_string, max_results)

        self.async_bridge.submit(
            coro,
            on_done=self._on_done,
            on_error=self._on_error,
            tk_after=self.root.after,
        )

    def _on_done(self, search_results: CallToolResult) -> None:
        """ Handle successful completion of the search example by writing results to output and
            optionally handling chain transcript if available.
            Args:
                search_results: The results of the search example.
        """
        chain_transcript = self.chain_transcript_var.get()
        if chain_transcript:
            self.on_chain_transcript(search_results)


    def _on_error(self, error: Exception) -> None:
        """ Handle an error from the search example by writing the error message to output.
                Args:
                    error: The exception raised during the search example execution.
        """
        self.output.write(f"Search failed: {error}")


