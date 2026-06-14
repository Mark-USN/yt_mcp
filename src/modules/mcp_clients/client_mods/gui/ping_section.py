""" This module defines the PingSection class, which is a GUI component for pinging the MCP server
    and displaying the results.
    The FastMCP Client's ping method returns a boolean value only, no timing is provided.
"""

from __future__ import annotations

import datetime
import time
import tkinter as tk
from tkinter import ttk
from collections.abc import Callable
from modules.mcp_clients.client_mods.tk_async import AsyncTkBridge
from modules.mcp_clients.client_mods.tk_output import TkOutput
from modules.mcp_clients.client_mods.mcp_client import McpClient

class PingSection(ttk.LabelFrame):
    """ The Tkinter section for pinging the MCP server and displaying results. """
    def __init__(
        self,
        parent: tk.Widget,
        *,
        root: tk.Tk,
        start_row: int,
        async_bridge: AsyncTkBridge,
        output: TkOutput,
        get_client: Callable[[], McpClient | None],
    ) -> None:
        """ Initialize the PingSection frame.

            Args:
                parent: The parent widget.
                root: The root Tkinter window.
                start_row: The starting row for placing this widget.
                async_bridge: The AsyncTkBridge instance for handling async tasks.
                output: The TkOutput instance for writing output.
                get_client: A callable that returns the current MCP client or None.
        """
        super().__init__(parent, text="Ping")
        self.root = root
        self.async_bridge = async_bridge
        self.output = output
        self.get_client = get_client
        self.ping_status_var = tk.StringVar(value="Not pinged")
        self.last_ping_var = tk.StringVar(value="Never")

        self.build_frame(start_row=start_row)


    def build_frame(self, start_row: int) -> None:
        """ Build ping controls.
            Args:
                start_row: The starting row for placing this widget.
        """
        self.grid(row=start_row, column=0, sticky="ew", padx=8, pady=4)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        row = 0
        ttk.Button(self, text="Ping", command=self.on_ping).grid(
            row=row,
            column=0,
            padx=4,
            pady=4,
        )

        ttk.Label(self, text="Status:").grid(
            row=row,
            column=1,
            sticky="e",
            padx=4,
            pady=4,
        )

        ttk.Label(self, textvariable=self.ping_status_var).grid(
            row=row,
            column=2,
            sticky="w",
            padx=4,
            pady=4,
        )

        ttk.Label(self, text="Last ping:").grid(
            row=row,
            column=3,
            sticky="e",
            padx=4,
            pady=4,
        )

        ttk.Label(self, textvariable=self.last_ping_var).grid(
            row=row,
            column=4,
            sticky="w",
            padx=4,
            pady=4,
        )


    def on_ping(self) -> None:
        """ Handle the Ping button click by pinging the server and updating the status. """
        client = self.get_client()
        if client is None:
            self.output.section("Ping")
            self.output.line("No valid MCP client available.")
            return
        
        start = time.perf_counter()
        self.async_bridge.submit(
            client.ping_server(),
            on_done=lambda result: self._on_ping_ok(start, result),
            on_error=self._on_ping_error,
            tk_after=self.root.after,
        )

    def _on_ping_ok(self, start: float, result: bool) -> None:
        """ Handle a successful ping result by updating the output and status.
            Args:
                start: The timestamp when the ping was initiated, used to calculate latency.
                result: The result of the ping operation, True if successful, False otherwise.
        """
        if not result:
            self._on_ping_error(Exception("Ping returned False"))
            return
        latency = (time.perf_counter() - start) * 1000
        self.output.write(f"Ping successful! Latency: {latency:.2f} ms")
        self.ping_status_var.set("Success")
        self.last_ping_var.set(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    def _on_ping_error(self, error: Exception) -> None:
        """ Handle a ping error by updating the output and status.
            Args:
                error: The exception raised during the ping operation.
        """
        self.output.write(f"Ping failed: {error}")
        self.ping_status_var.set("Failed")
        self.last_ping_var.set(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))





