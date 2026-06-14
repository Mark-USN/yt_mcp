""" This Frame holds the YouTube Tools and Prompt Frames being exercised and handles the chaining
    from the output of one to the input of the next, if desired.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections.abc import Callable
from mcp.types import CallToolResult
from yt_lib.utils.app_context import RuntimeContext
from modules.mcp_clients.client_mods.tk_async import AsyncTkBridge
from modules.mcp_clients.client_mods.tk_output import TkOutput
from modules.mcp_clients.client_mods.mcp_client import McpClient
from modules.mcp_clients.client_mods.gui.prompt_section import PromptSection
from modules.mcp_clients.client_mods.gui.search_section import SearchSection
from modules.mcp_clients.client_mods.gui.transcript_section import TranscriptSection
from modules.mcp_clients.client_mods.gui.audio_transcript_section import AudioTranscriptSection
from modules.utils.client_prompt_data import NormalizedQuery


class ExamplesFrame(ttk.LabelFrame):
    """ Holds the Frames for the examples being run and supports the chaining from one to another.
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
        """ Create the ExampleFrame class
            Args: 
                parent: The parent Tk widget.
                root: The root Tk instance.
                ctx:  The app's context providing directory information.
                start_row: The starting row for placing this widget.
                async_bridge: The asynchronous bridge for running tasks.
                output: The output sink for displaying messages.
                get_client: The callback to use to obtain the MCP Client instance.
        """

        super().__init__(parent, text="Examples")

        self.root = root
        self.ctx = ctx
        self.async_bridge = async_bridge
        self.output = output
        self.get_client = get_client

        self.build_frame(ctx=ctx, start_row=start_row)



    def build_frame(self, ctx: RuntimeContext, start_row: int) -> None:
        """ Create the TK objects and the controls within this frame.
            Args:
                ctx: RuntimeContext,
                start_row: int,
        """

        self.grid(row=start_row, column=0, sticky="ew", padx=8, pady=4)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        row = 0
        self.prompt_section = PromptSection(
                        parent = self,
                        root = self.root,
                        start_row = row,
                        async_bridge = self.async_bridge,
                        output = self.output,
                        get_client = self.get_client,
                        chain_search = self.chain_search,
                    )
        row += 1
        self.search_section = SearchSection(
                        parent = self,
                        root = self.root,
                        start_row = row,
                        async_bridge = self.async_bridge,
                        output = self.output,
                        get_client = self.get_client,
                        on_chain_transcript = self.chain_transcript,
                    )
        row += 1

        self.transcript_section = TranscriptSection(
                                            parent = self,
                                            root = self.root,
                                            ctx = ctx,
                                            start_row = row,
                                            async_bridge = self.async_bridge,
                                            output = self.output,
                                            get_client = self.get_client,
                                        )
        row += 1

        self.audio_transcript_section = AudioTranscriptSection(
                                            parent = self,
                                            root = self.root,
                                            ctx = ctx,
                                            start_row = row,
                                            async_bridge = self.async_bridge,
                                            output = self.output,
                                            get_client = self.get_client,
                                        )
 
    def _parse_url_list(self, value: str) -> list[str]:
        """ Parse one or more URLs from a comma/newline/space separated field. """

        raw_parts = value.replace(",", "\n").splitlines()
        urls: list[str] = []

        for part in raw_parts:
            urls.extend(piece.strip() for piece in part.split())

        return [url for url in urls if url]

     
        
    def chain_search(
                        self,
                        use_chain_search: bool= False,
                        ai_query_results: NormalizedQuery | None = None
                    ) -> None:
        """ Populate the Search input with the Prompts output and execute the search 
            Args:
                use_chain_search: bool - whether to chain the search or not.
                ai_query_results: NormalizedQuery | None - the results from the Prompt example to 
                                  use as input for the Search example.
        """
        if ai_query_results is None:
            return
        self.output.section("Chained Prompt Results")
        self.output.line(f"Place AI query {ai_query_results.query} in the search entry.")
        self.search_section.search_string_var.set(ai_query_results.query)
        self.search_section.run(use_chain_search, ai_query_results)

    def chain_transcript(self, search_results: CallToolResult) -> None:
        """ Populate the Transcript input with the Search output and execute the transcript
            example. Writing the transcript(s) to file(s) in the user's ~/Documents/Transcripts
            directory.
            Args:
                search_results: CallToolResult - the results from the Search example to use as
                                input for the Transcript example.
        """
        self.output.section("Chained Search Results")
        self.output.line(f"Resulting YouTubes {search_results}")
        # Update the transcript section with the URLs from the search results.
        self.transcript_section.set_urls(search_results.data)
        # self.transcript_section.set_urls([result.url for result in search_results])
        self.transcript_section.run()


