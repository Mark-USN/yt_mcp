""" Main GUI client for MCP. """

from __future__ import annotations

import sys
import argparse
from pathlib import Path
from collections.abc import Callable

import tkinter as tk
from tkinter import ttk

from yt_lib.utils.app_info import RuntimeInfo, create_user_info
from modules.mcp_clients.client_mods.mcp_client import McpClient
from modules.mcp_clients.client_mods.tk_async import AsyncTkBridge
from modules.mcp_clients.client_mods.gui.output_section import OutputSection
from modules.mcp_clients.client_mods.gui.connection_section import ConnectionSection
from modules.mcp_clients.client_mods.gui.main_frame import MainFrame

# pylint: disable=too-many-ancestors, too-many-instance-attributes
class McpClientFrame(ttk.Frame):
    """ Main GUI Frame for the MCP Client application. Contains the connection section, output
        section, and main controls frame which includes the ping, prompt, search, and transcript
        sections.
    """

    def __init__(self, parent: tk.Tk, host: str, port: int) -> None:
        """ Initialize the MCP Client Frame.
            Args:
                parent: The parent Tkinter window.
                host: The host address for the MCP server.
                port: The port number for the MCP server.
        """
        super().__init__(parent)
        self.root = parent
        self.async_bridge = AsyncTkBridge()
        self.client: McpClient | None = None
        self.info = RuntimeInfo(
                info=create_user_info(
                    app_name="MCP GUI Client",
                    app_author="ChickenScratch",
                    app_dir=Path(__file__).resolve().parent,
                )
        )

        self._build_ui(host, port)


    def _build_ui(self, host: str, port: int) -> None:
        """ Build the full GUI via composition of the main sections: connection, output, and main
            controls which includes the ping, prompt, search, and transcript sections.
            Args:
                host: The host address for the MCP server.
                port: The port number for the MCP server.


        Layout:

        New layout:

            self
            ├── connection_frame    row 0
            ├── main_frame          row 1
            |     col 0                                     col 1
            |       ├── ping_frame        row 0               ├── transcript_frame row 0
            |       ├── listings_frame    row 1               └── audio_transcript_frame row 3
            |       ├── prompt_frame      row 2
            |       └── search_frame      row 3 
            |           
            └── output_frame        row 2

        """

        self.grid(row=0, column=0, sticky="nsew")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        # Build the OutputSection first, since the main GUI and other sections need self.output.
        self.output_section = OutputSection(
                        parent = self,
                        root = self.root,
                        row = 2,
                        column = 0,
                        rowspan = 1,
                        columnspan = 1,
                        sticky = "ew",
                    )
        self.output = self.output_section.output

        # The connection section will supply self.mcp_client through the on_connected callback.
        self.connection_section = ConnectionSection(
                                parent = self,
                                root = self.root,
                                row = 0,
                                host = host,
                                port = port,
                                async_bridge = self.async_bridge,
                                output = self.output,
                                on_connected = self._on_connected,
                                on_disconnected = self._on_disconnected
                            )

        self.main_frame = MainFrame(
                                parent = self,
                                root = self.root,
                                info = self.info,
                                row = 1,
                                async_bridge = self.async_bridge,
                                output = self.output,
                                get_client = self.get_client,
                            )

        self.main_frame.set_gui_state(False)

    def get_client(self) -> McpClient | None:
        """ Getter for the current MCP client instance. Returns None if not connected. """
        return self.client

    def _on_connected(self, client: McpClient) -> None:
        """ Callback for when the ConnectionSection establishes a connection and creates an MCP
            client. 
            Args:
                client: The connected MCP client instance.
        """
        self.client = client
        self.main_frame.set_gui_state(True)

    def _on_disconnected(self) -> None:
        """ Callback for when the ConnectionSection disconnects and cleans up the MCP client. """
        self.client = None
        self.main_frame.set_gui_state(False)

    def close(self, on_closed: Callable[[], None]) -> None:
        """Cleanly shut down GUI-owned resources before Tk exits.
            Args:
                on_closed: A callable to call after resources are closed.
        """

        client = self.client
        self.client = None

        if client is not None:
            self.async_bridge.submit(
                client.close(),
                on_done=lambda _result: self._finish_close(on_closed),
                on_error=lambda exc: self._finish_close(on_closed),
                tk_after=self.root.after,
            )
        else:
            self._finish_close(on_closed)


    def _finish_close(self, on_closed: Callable[[], None]) -> None:
        """ Finish closing resources and call the on_closed callback.
            Args:
                on_closed: A callable to call after resources are closed.
        """
        self.async_bridge.close()
        on_closed()


class McpClientApp:
    """ Main application class for the MCP Client GUI. Initializes the root Tk window and the main
            client frame, and starts the Tk main loop.
    """
    def __init__(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 8085,
        # auto_connect: bool = False,
    ) -> None:
        """ Initialize the MCP Client application. 
            Args:
                host: The host address for the MCP server (default "127.0.0.1").
                port: The port number for the MCP server (default 8085).
                geometry: The geometry of the Tk window (default "1000x700").
        """
        self.root = tk.Tk()
        self.root.title("MCP Client")

        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.frame = McpClientFrame(
            self.root,
            host=host,
            port=port,
            # auto_connect=auto_connect,
        )
        # self.frame.grid(row=0, column=0, sticky="nsew")
        self.set_initial_geometry()

        self.root.protocol("WM_DELETE_WINDOW", self.close)


    def set_initial_geometry(self) -> None:
        """Size the window to fit its requested contents, limited by screen size."""

        self.root.update_idletasks()

        req_width = self.root.winfo_reqwidth()
        req_height = self.root.winfo_reqheight()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        max_width = int(screen_width * 0.90)
        max_height = int(screen_height * 0.90)

        width = min(req_width, max_width)
        height = min(req_height, max_height)

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(min(req_width, max_width), min(req_height, max_height))


    def run(self) -> None:
        """ Start the Tk main loop. """
        self.root.mainloop()

    def close(self) -> None:
        """ Cleanly shut down the application by closing the main frame and then destroying the
            root Tk window.
        """
        self.frame.close(self.root.destroy)


def port_type(value: str) -> int:
    """ 20251101 MMH port_type
        Custom argparse type that validates a TCP port number.
    """
    try:
        port = int(value)
    except ValueError as err:
        # logger.error("Port must be an integer.\n%s Port = %s.",
        #     str(value), err)
        raise SystemExit(f"Port must be an integer.\n{value} Port = {err}") from err
    if not 1 <= port <= 65535:
        # logger.error("Port number must be between 1 and 65535 (got {port!r})")
        raise SystemExit(
            f"Port number must be between 1 and 65535!. Port = {port}.") from err
    return port



def main() -> None:
    """ Main entry point: parse arguments and run client. """    
    parser = argparse.ArgumentParser(
        description="Create and run an Tk MCP client."
    )

    parser.add_argument("--host", type=str, default="127.0.0.1",
                        help="Host name or IP address (default 127.0.0.1).")
    parser.add_argument("--port", type=port_type, default=8085,
                        help="TCP port to bind/connect (default 8085).")
    args = parser.parse_args()

    # 20251215 MMH Show help if no arguments are given
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)  # Exit with an error code

    app = McpClientApp(host=args.host, port=args.port,)
    app.run()

if __name__ == "__main__":
    main()
