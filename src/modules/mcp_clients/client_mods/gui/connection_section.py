""" GUI section for managing the MCP client connection."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections.abc import Callable
from modules.mcp_clients.client_mods.tk_async import AsyncTkBridge
from modules.mcp_clients.client_mods.tk_output import TkOutput
from modules.mcp_clients.client_mods.mcp_client import McpClient

# pylint: disable=too-many-ancestors, too-many-instance-attributes
class ConnectionSection(ttk.LabelFrame):
    """ Class for managing the MCP client's GUI connection arguments and connection. """
    client: McpClient | None = None

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
        host: str,
        port: int,
        async_bridge: AsyncTkBridge,
        output: TkOutput,
        on_connected: Callable[[McpClient], None],
        on_disconnected: Callable[[], None],
    ) -> None:
        """ Initialize the connection section.
            Args:
                parent: The parent Tk widget.
                root: The root Tk instance.
                row: The starting row for placing this widget.
                host: The default host for the MCP client.
                port: The default port for the MCP client.
                async_bridge: The asynchronous bridge for running tasks.
                output: The output sink for displaying messages.
                on_connected: Callback when the client is connected.
                on_disconnected: Callback when the client is disconnected.
        """
        super().__init__(parent, text="Connection")

        self.root = root
        self.async_bridge = async_bridge
        self.output = output
        self.on_connected = on_connected
        self.on_disconnected = on_disconnected
        host = host if host is not None else "127.0.0.1"
        port = port if port is not None else 8085
        self.host_var = tk.StringVar(value=host)
        self.port_var = tk.StringVar(value=str(port))
        self.connection_status_var = tk.StringVar(value="Not connected")

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
        """ Build the always-enabled server connection GUI controls.
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

        row = 0
        ttk.Label(self, text="Host:").grid(
            row=row,
            column=0,
            sticky="w",
            padx=4,
            pady=4,
        )

        ttk.Entry(self, textvariable=self.host_var).grid(
            row=row,
            column=1,
            sticky="ew",
            padx=4,
            pady=4,
        )

        ttk.Label(self, text="Port:").grid(
            row=row,
            column=2,
            sticky="w",
            padx=4,
            pady=4,
        )

        ttk.Entry(self, textvariable=self.port_var, width=8).grid(
            row=row,
            column=3,
            padx=4,
            pady=4,
        )
        row += 1

        ttk.Label(self, textvariable=self.connection_status_var).grid(
            row=row,
            column=0,
            columnspan=3,
            sticky="w",
            padx=4,
            pady=4,
        )

        ttk.Button(self, text="Connect", command=self.on_connect).grid(
            row=row,
            column=2,
            padx=4,
            pady=4,
        )

        ttk.Button(self, text="Disconnect", command=self.on_disconnect).grid(
            row=row,
            column=3,
            padx=4,
            pady=4,
        )


    def _parse_port(self) -> int | None:
        """Parse and validate the port entry."""

        port_text = self.port_var.get().strip()

        try:
            port = int(port_text)
        except ValueError:
            self.connection_status_var.set("Port must be a number.")
            return None

        if not 1 <= port <= 65_535:
            self.connection_status_var.set("Port must be between 1 and 65535.")
            return None

        return port

    def on_connect(self) -> None:
        """ Attempt to connect to the MCP server using the provided host and port. """

        host = self.host_var.get().strip()
        port = self._parse_port()

        if not host:
            self.connection_status_var.set("Host is required.")
            return

        if port is None:
            self.connection_status_var.set("Port is required.")
            return

        client = McpClient(host, port)
        self.connection_status_var.set(f"Connecting to {host}:{port}...")

        self.async_bridge.submit(
            client.ping_server(),
            on_done=lambda result: self._on_connect_ok(client, result),
            on_error=self._on_error,
            tk_after=self.root.after,
        )




    def _on_connect_ok(self, client: McpClient, result: bool) -> None:
        """ Handle successful connection to the MCP server. Pass the active client to the
            penultimate App class via the on_connected callback.
            Args:
                client: The connected MCP client instance.
                result: The result of the ping_server call (not used here).
        """
        self.connection_status_var.set("Connected")
        # Tell the App we connected and give it the client to work with.
        self.on_connected(client)
        self.output.section("Connected")
        self.output.line(result)


    def _on_error(self, exc: BaseException) -> None:
        """ Handle errors that occur during connection attempts.
            Args:
                exc: The exception that occurred.
        """
        self.client = None
        self.connection_status_var.set("Connection failed")
        self.output.section("Connection Error")
        self.output.line(f"{type(exc).__name__}: {exc}")


    def on_disconnect(self) -> None:
        """ Handle disconnection from the MCP server. Clear the client and update the status. """
        self.on_disconnected()
        self.connection_status_var.set("Not connected")

    # def update_connection_status(self, status):
    #     self.connection_status_var.set(f"Connection Status: {status}")
