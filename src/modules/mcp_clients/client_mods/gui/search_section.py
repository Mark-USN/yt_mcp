""" GUI section for search example controls."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections.abc import Callable
from fastmcp.client.client import CallToolResult
from modules.mcp_clients.client_mods.tk_async import AsyncTkBridge
from modules.mcp_clients.client_mods.tk_output import TkOutput
from modules.mcp_clients.client_mods.mcp_client import McpClient
from modules.mcp_clients.client_mods.examples.search_example import SearchExample
from modules.utils.client_prompt_data import NormalizedQuery

DEFAULT_RESULTS = 5             # Default value for max results in search example the actual max
                                # is 50, but start with a lower default to encourage testing with
                                # smaller numbers.


# pylint: disable=too-many-ancestors, too-many-instance-attributes
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
        row: int,
        column: int = 0,
        rowspan: int = 1,
        columnspan: int = 1,
        sticky: str = "ew",
        async_bridge: AsyncTkBridge,
        output: TkOutput,
        get_client: Callable[[], McpClient | None],
        on_chain_change: Callable[[bool], None],
        chain_transcript: Callable[[CallToolResult], None],
    ) -> None:
        """ Initialize the SearchSection frame.
            Args:
                parent: The parent widget.
                root: The root Tkinter window.
                row: The starting row for placing this widget.
                async_bridge: The asynchronous bridge for handling async tasks.
                output: The output widget for displaying results.
                get_client: A callable that returns the MCP client.
                on_chain_change: A callable that handles changes to the chain search option.
                                     transcript example.
        """
        super().__init__(parent, text="Search")
        self.root = root
        self.async_bridge = async_bridge
        self.output = output
        self.search_string_var = tk.StringVar(value="")
        self.max_results_var = tk.StringVar(value=str(DEFAULT_RESULTS))
        self.chain_transcript_var = tk.BooleanVar(value=False)
        self.video_search_var = tk.BooleanVar(value=True)
        self.playlist_search_var = tk.BooleanVar(value=False)
        self.get_client = get_client
        self.on_chain_changed = on_chain_change
        self.chain_transcript = chain_transcript
        self.chain_enable_list: list[tk.Widget] = []
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
        """ Build search example controls.
            Args:
                row: The starting row for placing this widget.

            This frame is inside main_controls, so it starts disabled until connected.
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

        row = 0

        ttk.Label(self, text="Search:").grid(
            row=row,
            column=0,
            sticky="w",
            padx=4,
            pady=4,
        )

        self.url_entry = ttk.Entry(self, textvariable=self.search_string_var)
        self.url_entry.grid(
            row=row,
            column=1,
            columnspan=3,
            sticky="ew",
            padx=4,
            pady=4,
        )

        widget = ttk.Label(self, text="Max:")
        widget.grid(
            row=row,
            column=4,
            sticky="e",
            padx=4,
            pady=4,
        )
        self.chain_enable_list.append(widget)

        widget = ttk.Spinbox(
            self,
            from_=1,
            to=50,
            textvariable=self.max_results_var,
            width=5,
        )
        widget.grid(
            row=row,
            column=5,
            sticky="e",
            padx=4,
            pady=4,
        )
        self.chain_enable_list.append(widget)
        row += 1

        widget = ttk.Checkbutton(
            self,
            text="Link to transcript.",
            variable=self.chain_transcript_var,
        )
        widget.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            padx=4,
            pady=2,
        )
        self.chain_enable_list.append(widget)

        self.chain_transcript_var.trace_add(
            "write",
            self._handle_chain_transcript_changed,
        )

        widget = ttk.Checkbutton(
            self,
            text="Videos",
            variable=self.video_search_var,
        )
        widget.grid(
            row=row,
            column=2,
            sticky="w",
            padx=4,
            pady=2,
        )
        self.chain_enable_list.append(widget)

        widget = ttk.Checkbutton(
            self,
            text="Playlist",
            variable=self.playlist_search_var,
        )
        widget.grid(
            row=row,
            column=3,
            sticky="w",
            padx=4,
            pady=2,
        )
        self.chain_enable_list.append(widget)

        ttk.Button(
            self,
            text="Run Search",
            command=self.run,
        ).grid(
            row=row,
            column=4,
            columnspan=2,
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


    def enable_chained_widgets(self) -> None:
        """ Enable the chaining control.
            Used when the search example is run as part of a chain and should allow chaining to
            the transcript example.
        """
        for widget in self.chain_enable_list:
            widget.config(state="normal")

    def _handle_chain_transcript_changed(
                                            self,
                                            *_args: object,
                                        ) -> None:
        self.on_chain_changed(self.chain_transcript_var.get())


    def run(
                self,
                ai_query_results: NormalizedQuery | None = None
            ) -> None:
        """ Run the search example with the provided search string and max results. If successful,
            writes the results to the output section. If an error occurs, writes the error message
            to the output section.
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

        if self.video_search_var.get() and self.playlist_search_var.get():
            kinds = "both"
        elif self.video_search_var.get():
            kinds = "video"
        elif self.playlist_search_var.get():
            kinds = "playlist"
        else:
            kinds = "video"

        video_str = "True" if self.video_search_var.get() else "False"
        playlist_str = "True" if self.playlist_search_var.get() else "False"

        self.output.section("Run Search Example")
        self.output.line(f"Search string: {search_string}")
        self.output.line(f"Max results: {max_results}")
        self.output.line(f"Chain transcript: {chain_transcript}")
        self.output.line(f"Search for Videos: {video_str}")
        self.output.line(f"Search for Playlists: {playlist_str}")

        example = SearchExample(
            client,
            emit=self.output.line_threadsafe,
        )
        if ai_query_results:
            coro = example.run_ai(ai_query_results, max_results, kinds)
        else:
            coro = example.run(search_string, max_results, kinds)

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
            self.chain_transcript(search_results)


    def _on_error(self, error: Exception) -> None:
        """ Handle an error from the search example by writing the error message to output.
                Args:
                    error: The exception raised during the search example execution.
        """
        self.output.line(f"Search failed: {error}")
