
""" Main frame for MCP client operations, containing sections for pinging, listing, and examples.
    And disabled until a connection is established.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections.abc import Callable
from fastmcp.client.client import CallToolResult
from yt_lib.utils.app_info import RuntimeInfo
from modules.mcp_clients.client_mods.tk_async import AsyncTkBridge
from modules.mcp_clients.client_mods.tk_output import TkOutput
from modules.mcp_clients.client_mods.mcp_client import McpClient
from modules.mcp_clients.client_mods.gui.ping_section import PingSection
from modules.mcp_clients.client_mods.gui.listing_section import ListingSection
from modules.mcp_clients.client_mods.gui.prompt_section import PromptSection
from modules.mcp_clients.client_mods.gui.search_section import SearchSection
from modules.mcp_clients.client_mods.gui.transcript_section import TranscriptSection
from modules.mcp_clients.client_mods.gui.audio_transcript_section import AudioTranscriptSection
from modules.utils.client_prompt_data import NormalizedQuery

# pylint: disable=too-many-ancestors, too-many-instance-attributes
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
        info: RuntimeInfo,
        row: int,
        column: int = 0,
        rowspan: int = 1,
        columnspan: int = 1,
        sticky: str = "ew",
        async_bridge: AsyncTkBridge,
        output: TkOutput,
        get_client: Callable[[], McpClient | None],
    ) -> None:
        """ Initialize the main frame for MCP client operations.

            Args:
                parent: The parent widget.
                root: The root Tkinter window.
                info: The runtime info, providing access to app directories and other shared
                     resources.
                row: The starting row for placing this widget.
                async_bridge: The asynchronous bridge for Tkinter.
                output: The output widget.
                get_client: A callable that returns the MCP client or None.
        """

        super().__init__(parent, text="MCP Client Operations")

        self.root = root
        self.async_bridge = async_bridge
        self.output = output
        self.get_client = get_client

        self.build_frame(
                            info=info,
                            row=row,
                            column=column,
                            rowspan=rowspan,
                            columnspan=columnspan,
                            sticky=sticky,
                        )



    def build_frame(
                        self,
                        info: RuntimeInfo,
                        row: int,
                        column: int = 0,
                        rowspan: int = 1,
                        columnspan: int = 1,
                        sticky: str = "ew",
                    ) -> None:
        """ Build the main frame for MCP client operations. 
            Args:
                info: The runtime info, providing access to app directories and other shared
                     resources.
                row: The starting row for placing this widget.
                column: The starting column for placing this widget (default 0).
                rowspan: The number of rows to span (default 1).
                columnspan: The number of columns to span (default 1).
                sticky: The sticky option for grid placement (default "ew").
        """
        self.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, sticky=sticky)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=1)

        self.ping_section = PingSection(
            parent=self,
            root=self.root,
            row=0,
            column=0,
            async_bridge=self.async_bridge,
            output=self.output,
            get_client=self.get_client,
        )

        self.listing_section = ListingSection(
            parent=self,
            root=self.root,
            row=1,
            column=0,
            async_bridge=self.async_bridge,
            output=self.output,
            get_client=self.get_client,
        )

        self.prompt_section = PromptSection(
            parent=self,
            root=self.root,
            row=2,
            column=0,
            async_bridge=self.async_bridge,
            output=self.output,
            get_client=self.get_client,
            on_chain_change=self.on_chain_search_change,
            chain_search=self.chain_search,
        )

        self.search_section = SearchSection(
            parent=self,
            root=self.root,
            row=3,
            column=0,
            async_bridge=self.async_bridge,
            output=self.output,
            get_client=self.get_client,
            on_chain_change=self.on_chain_transcript_change,
            chain_transcript=self.chain_transcript,
        )

        self.transcript_section = TranscriptSection(
            parent=self,
            root=self.root,
            info=info,
            row=0,
            column=1,
            rowspan=3,
            sticky="nsew",
            async_bridge=self.async_bridge,
            output=self.output,
            get_client=self.get_client,
        )

        self.audio_transcript_section = AudioTranscriptSection(
            parent=self,
            root=self.root,
            info=info,
            row=3,
            column=1,
            async_bridge=self.async_bridge,
            output=self.output,
            get_client=self.get_client,
        )

    def set_gui_state(self, enabled: bool, *, section:ttk.LabelFrame = None) -> None:
        """ Enable or disable all controls that require an MCP client.

            Args:
                enabled: A boolean indicating whether to enable or disable the controls.
        """

        if section is None:
            section = self

        state = "normal" if enabled else "disabled"

        for child in section.winfo_children():
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

    def _parse_url_list(self, value: str) -> list[str]:
        """ Parse one or more URLs from a comma/newline/space separated field. """

        raw_parts = value.replace(",", "\n").splitlines()
        urls: list[str] = []

        for part in raw_parts:
            urls.extend(piece.strip() for piece in part.split())

        return [url for url in urls if url]

    def on_chain_search_change(self, use_chain_search: bool) -> None:
        """ Handle changes to the "chain search" option in the Prompt section. If chaining is
            enabled, run the chain_search method with the current prompt results.
            Args:
                use_chain_search: A boolean indicating whether chaining is enabled.
        """
        if use_chain_search:
            self.set_gui_state(False, section=self.search_section)
            # Allow toggling of the chaining from search to transcript, even if the prompt section
            # is suppling the search input.
            self.search_section.enable_chained_widgets()
        else:
            self.set_gui_state(True, section=self.search_section)


    def chain_search(
                        self,
                        ai_query_results: NormalizedQuery | None = None
                    ) -> None:
        """ Populate the Search input with the Prompts output and execute the search 
            Args:
                ai_query_results: NormalizedQuery | None - the results from the Prompt example to 
                                    use as input for the Search example.
        """
        if ai_query_results is None:
            return
        self.output.section("Chained Prompt Results")
        self.output.line(f"Place AI query {ai_query_results.query} in the search entry.")
        self.search_section.search_string_var.set(ai_query_results.query)
        self.search_section.run(ai_query_results)


    def on_chain_transcript_change(self, use_chain_transcript: bool) -> None:
        """ Handle changes to the "chain transcript" option in the Transcript section. If chaining
            is enabled, run the chain_transcript method with the current search results.
            Args:
                use_chain_transcript: A boolean indicating whether chaining is enabled.
        """
        if use_chain_transcript:
            self.set_gui_state(False, section=self.transcript_section)
        else:
            self.set_gui_state(True, section=self.transcript_section)

    def chain_transcript(self, search_results: CallToolResult) -> None:
        """Populate the Transcript input with the Search output and execute the transcript example."""

        data = search_results.data

        if not isinstance(data, dict):
            self.output.line(f"Unexpected search result data type: {type(data).__name__}")
            return

        items = data.get("items", [])

        transcript_urls = [
            item["url"]
            for item in items
            if isinstance(item, dict) and "url" in item
        ]

        self.output.section("Chained Search Results")

        if not transcript_urls:
            self.output.line("No resulting YouTubes")
            return

        self.output.line("Resulting YouTubes:")
        url_lines = "\n".join(transcript_urls)
        self.output.line(f"{url_lines}")
        self.transcript_section.set_urls(transcript_urls)
        self.transcript_section.run()
