""" Transcript controls for MCP client GUI. """

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections.abc import Callable
from fastmcp.client.client import CallToolResult
from yt_lib.utils.app_info import RuntimeInfo
from modules.mcp_clients.client_mods.tk_async import AsyncTkBridge
from modules.mcp_clients.client_mods.tk_output import TkOutput, TkAfterOutputSink
from modules.mcp_clients.client_mods.mcp_client import McpClient
from modules.mcp_clients.client_mods.examples.transcript_example import TranscriptExample

# pylint: disable=too-many-ancestors, too-many-instance-attributes
class TranscriptSection(ttk.LabelFrame):
    """ Class Tx Frame containing controls for running the Transcript example. """

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
        """ Initialize the TranscriptSection frame.
            Args:
                parent: The parent widget.
                root: The root Tkinter window.
                info: The runtime info.
                row: The starting row for grid placement.
                async_bridge: The asynchronous bridge for Tkinter.
                output: The output widget for displaying results.
                get_client: A callable that returns the MCP client or None.
        """
        super().__init__(parent, text="Transcript")
        self.root = root
        self.info = info
        self.async_bridge = async_bridge
        self.output = output
        self.get_client = get_client
        self.transcript_urls_var = tk.StringVar(value="")

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
        """ Build transcript controls.
            Args:
                row: The starting row for grid placement.

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
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # Important: your Text widget is on internal row 3, not row 1.
        self.rowconfigure(3, weight=1)

        row = 0

        ttk.Label(self, text="Transcript URLs:").grid(
            row=row,
            column=0,
            sticky="w",
            padx=4,
            pady=4,
        )
        row += 1

        self.urls_text = tk.Text(
            self,
            height=8,
            width=80,
            wrap="none",
        )
        self.urls_text.grid(
            row=row,
            column=0,
            columnspan=4,
            sticky="nsew",
        )

        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.urls_text.yview,
        )
        self.scrollbar.grid(
            row=row,
            column=4,
            sticky="ns",
        )

        self.urls_text.configure(yscrollcommand=self.scrollbar.set)

        row += 1
        ttk.Button(
            self,
            text="Run Transcript",
            command=self.run,
        ).grid(
            row=row,
            column=3,
            padx=4,
            pady=4,
            sticky="e",
        )

    def get_urls(self) -> list[str]:
        """ Get the list of URLs from the text field, stripping whitespace and ignoring empty
            lines.
            Returns:
                A list of URLs.
        """
        text = self.urls_text.get("1.0", "end").strip()

        return [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

    def set_urls(self, urls: list[str]) -> None:
        """ Set the URLs in the text field, replacing any existing content.
            Args:
                urls: A list of URLs to set in the text field.
        """
        old_state = str(self.urls_text.cget("state"))

        self.urls_text.configure(state="normal")
        self.urls_text.delete("1.0", "end")
        self.urls_text.insert("1.0", "\n".join(urls))

        self.urls_text.configure(state=old_state)

    def set_enabled(self, enabled: bool) -> None:
        """ Enable or disable the URL input field and Run button.
            Args:
                enabled: A boolean indicating whether to enable or disable the controls.
        """
        state = "normal" if enabled else "disabled"
        self.urls_text.configure(state=state)


    def run(self) -> None:
        """ Run the transcript example with the provided URLs. If successful,
            writes the results to the output section. If an error occurs, writes the error message
            to the output section.
        """
        client = self.get_client()
        if client is None:
            self.output.section("Transcript Example")
            self.output.line("No valid MCP client available.")
            return


        urls = self.get_urls()
        if not urls:
            self.output.section("Transcript Example")
            self.output.line("At least one URL is required.")
            return

        self.output.section("Run Transcript Example")
        self.output.line(f"URLs: {urls}")

        example = TranscriptExample(
                                    mcp_client = client,
                                    doc_dir_provider = self.info,
                                    emit=TkAfterOutputSink(self.root, self.output),
                                )

        self.async_bridge.submit(
            example.run(urls),
            on_done=self._on_done,
            on_error=self._on_error,
            tk_after=self.root.after,
        )

    def _on_done(self, _result: CallToolResult | None) -> None:
        """ Handle successful completion of the transcript example by writing a success message
            to the output section.
                Args:
                    _result: The result of the transcript operation, if any. This example does not
                            return a result, so this argument is ignored.
        """
        self.output.line("Transcript completed successfully.")

    def _on_error(self, error: Exception) -> None:
        """ Handle an error from the transcript example by writing the error message to the
            output section.
            Args:
                error: The exception raised during the transcript example execution.
        """
        self.output.line(f"Transcript failed: {error}")
