""" Audio Transcript Section for MCP Client GUI.
    Handles user input for audio URLs, runs the AudioTranscriptExample, displays results in the
    output section and writes the results to a file in the users ~/Documents/transcripts directory.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections.abc import Callable
from mcp.types import CallToolResult
from yt_lib.utils.app_context import RuntimeContext
from modules.mcp_clients.client_mods.tk_async import AsyncTkBridge
from modules.mcp_clients.client_mods.tk_output import TkOutput, TkAfterOutputSink
from modules.mcp_clients.client_mods.mcp_client import McpClient
from modules.mcp_clients.client_mods.examples.audio_transcript_example import AudioTranscriptExample


class AudioTranscriptSection(ttk.LabelFrame):
    """ Section for running the Audio Transcript example wrapped in a Tk Frame. """

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
        """ Initialize the Audio Transcript section.

        Args:
            parent: The parent Tk widget.
            root: The root Tk instance.
            ctx: The runtime context, providing access to the user's document directory.
            start_row: The starting row for placing this widget.
            async_bridge: The asynchronous bridge for running tasks.
            output: The output sink for displaying messages.
            get_client: A callable that returns an MCP client or None.
        """
        super().__init__(parent, text="Audio to Transcript")
        self.root = root
        self.ctx = ctx
        self.async_bridge = async_bridge
        self.output = output
        self.get_client = get_client
        self.url_var = tk.StringVar(value="")

        self.build_frame(start_row=start_row)


    def build_frame(self, start_row: int) -> None:
        """ Build audio transcript controls.
            Args:
                start_row: The starting row for placing this widget.

            Note:
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

        ttk.Label(self, text="Audio Transcript Example").grid(
            row=row,
            column=0,
            columnspan=5,
            sticky="w",
            padx=4,
            pady=(4, 2),
        )
        row += 1

        ttk.Label(self, text="URL:").grid(
            row=row,
            column=0,
            sticky="w",
            padx=4,
            pady=4,
        )

        ttk.Entry(self, textvariable=self.url_var).grid(
            row=row,
            column=1,
            columnspan=3,
            sticky="ew",
            padx=4,
            pady=4,
        )

        ttk.Button(
            self,
            text="Run Transcript",
            command=self.run,
        ).grid(
            row=row,
            column=4,
            padx=4,
            pady=4,
            sticky="e",
        )


    def run(self) -> None:
        """ Run the audio transcript example with the provided URL. If successful, writes the
            transcript to a file in the user's ~/Documents/Transcripts directory.
        """

        client = self.get_client()
        if client is None:
            self.output.section("Audio Transcript Example")
            self.output.line("No valid MCP client available.")
            return

        url = self.url_var.get()
        if not url:
            self.output.section("Audio Transcript Example")
            self.output.line("At least one URL is required.")
            return

        self.output.section("Run Audio Transcript Example")
        self.output.line(f"URL: {url}")

        example = AudioTranscriptExample(
                                    mcp_client = client,
                                    doc_dir_provider = self.ctx,
                                    emit=TkAfterOutputSink(self.root, self.output)
                                )

        self.async_bridge.submit(
            example.run(url),
            on_done=self._on_done,
            on_error=self._on_error,
            tk_after=self.root.after,
        )

    def _on_done(self, _result: CallToolResult | None) -> None:
        """ Handle successful completion of the audio transcript example."""
        self.output.line("Audio transcript completed successfully.")

    def _on_error(self, error: Exception) -> None:
        """ Handle errors that occur during the audio transcript example."""
        self.output.write(f"Transcript failed: {error}")
