""" 20260516 MMH mcp_server.py — Move into a class MCPServer that can be instantiated and
    launched from a CLI or imported and used in other contexts. 
    Based on https://gofastmcp.com/servers/server
    Added code to automatically register tools and prompts from their packages.
        from the 'tools' package,
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from enum import StrEnum, auto
from fastmcp import FastMCP
# from fastmcp.dependencies import CurrentContext
# from fastmcp.server.context import Context
from yt_lib.utils.log_utils import (
    Logger,
    LogConfig,
    FileLogConfig,
    configure_logging,
    get_logger
)
from yt_lib.utils.app_info import RuntimeInfo, create_user_info, create_service_info
from modules.utils.modules_registrar import PyRegistrar, PromptRegistrar, ResourcesRegistrar



class ServerRuntime(StrEnum):
    """ Specifies the runtime mode for the MCP server, which determines the type of application
        info created. 
    """
    USER = auto()
    SERVICE = auto()

class MCPServer:
    """ Class-based implementation of the MCP server. 
        Implements the dynamic discovery and registration of tools, prompts and resources from
        their respective packages.
    """
    mcp: FastMCP
    info: RuntimeInfo
    logger: Logger
    lib_root: Path
    tools_root: Path
    prompts_root: Path
    resources_root: Path


    def __init__(
            self,
            mode: ServerRuntime = ServerRuntime.USER,
            server_name: str = "MCP_Server",
            app_author: str = "ChickenScratch",
            app_dir: Path | None = None,
            lib_root: Path | None = None,
        ) -> None:

        # -----------------------------
        # info setup
        # -----------------------------
        if mode == ServerRuntime.USER:
            self.info = RuntimeInfo(
                info=create_user_info(
                    app_name=server_name,
                    app_author=app_author,
                    app_dir=app_dir or Path(__file__).resolve().parent,
                )
            )
        else:
            self.info = RuntimeInfo(
                info=create_service_info(
                    app_name=server_name,
                    app_author=app_author,
                    app_dir=app_dir or Path(__file__).resolve().parent,
                )
            )


        # -----------------------------
        # Logging setup
        # -----------------------------
        configure_logging(
                        LogConfig(self.info.app_name, log_level="WARNING"),
                        force=True,
                        file_log_conf=FileLogConfig(log_file=self.info.log_path),
                        tee_console=False,
                    )
        self.logger = get_logger(server_name)

        # -----------------------------
        # MCP setup
        # -----------------------------
        self.mcp = FastMCP(
                name=server_name,
                on_duplicate="error",
                # tasks=True,
            )

        # -----------------------------
        # Directory tree setup
        # -----------------------------
        self.lib_root = lib_root or self.info.app_dir.parent
        self.tools_root = self.lib_root / "tools"
        self.prompts_root = self.lib_root / "prompts"
        self.resources_root = self.lib_root / "resources"
        self.logger.info("MCPServer initialized with\n\ttools_root=%s,"
                         "\n\tprompts_root=%s,\n\tresources_root=%s",
                         self.tools_root, self.prompts_root, self.resources_root)

    def purge_server_cache(self, days: int = 1) -> None:
        """ Purge transcript cache files older than `days` days.
            Args:
                days (int): Number of days to keep cache files. Default is 1 day.
        """
        cutoff = time.time() - (days * 86400)

        for f in self.info.transcript_dir.iterdir():
            if f.is_file() and f.stat().st_atime < cutoff:
                f.unlink(missing_ok=True)


    # -----------------------------------------
    # Attach everything to FastMCP at startup
    # -----------------------------------------
    def attach_everything(self) -> None:
        """ 20251101 MMH attach_everything registers all tools, prompts and resources to the
            FastMCP server.
            Warning: The server will pull in all the code from a tool or prompt package.
            Any error in a file will cause the tools or prompts in that package to be ignored.
            Make sure you trust the code in those packages!
        """
        try:
            self.logger.info("Attaching tools, prompts and resources to MCP server...")
            # Purge old cache files on server startup
            self.purge_server_cache(days=1)
            PyRegistrar(
                            mcp=self.mcp,
                            app_info=self.info,
                            module_dir=self.tools_root,
                        ).register()
            self.logger.info("Tools registered.")

            PromptRegistrar(
                                mcp=self.mcp,
                                app_info=self.info,
                                module_dir=self.prompts_root,
                            ).register()
            self.logger.info("Prompt functions registered.")
            self.logger.info("Markdown files parsed and prompts registered.")

            ResourcesRegistrar(
                                    mcp=self.mcp,
                                    app_info=self.info,
                                    module_dir=self.resources_root,
                                ).register()
            self.logger.info("Resources registered.")
        except Exception as exc:
            self.logger.error("Error attaching tools, prompts or resources: %s", exc)
            raise SystemExit(f"Error attaching tools, prompts or resources: {exc}") from exc


    def run(self, host:str="127.0.0.1", port:int=8085) -> None:
        """ 20251101 MMH launch_server
            The entry point to start the FastMCP server. 
            Launch the FastMCP server with all tools and prompts attached. 
        """
        try:
            self.logger.info("mcp_server config tools, prompts, and templates.")
            self.attach_everything()
            self.logger.info("MCP Server starting on http://%s:%d", host, port)
            self.mcp.run(transport="http", host=host, port=port)
        except Exception as exc:
            self.logger.error("Error running MCP server: %s", exc)
            raise SystemExit(f"Error running MCP server: {exc}") from exc

# -----------------------------
# CLI (kept as before)
# -----------------------------
def port_type(value: str) -> int:
    """ 20251101 MMH port_type
        Custom argparse type that validates a TCP port number.
    """
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Port must be an integer (got {value!r})") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError(f"Port number must be between 1 and 65535 (got {port})")
    return port


def launch(
        mode: ServerRuntime = ServerRuntime.USER,
        host: str = "127.0.0.1",
        port: int = 8085,
    ) ->None:
    """ 20260517 MMH launch_server
        Launch the MCP server with the given mode, host and port.
        Used within a python module or script to start the server without using the CLI.
        Args:
            mode (ServerRuntime): The runtime mode for the server (USER or SERVICE).
            host (str): The host name or IP address to bind to (default "127.0.0.1").
            port (int): The TCP port to bind to (default 8085).
    """
    server = MCPServer(mode=mode)
    server.run(host, port)

def main() -> None:
    """ 20251101 MMH main
        Main entry point when launched "stand alone" 
        Parse arguments and start the server. 
    """
    parser = argparse.ArgumentParser(description="Create and run an MCP server.")
    parser.add_argument(
        "--runtime",
        type=str.lower,
        choices=[r.value for r in ServerRuntime],
        default=ServerRuntime.USER.value,
        help="Runtime mode for the MCP server: user or service.",
    )
    parser.add_argument("--host", type=str, default="127.0.0.1",
                        help="Host name or IP address (default 127.0.0.1).")
    parser.add_argument("--port", type=port_type, default=8085,
                        help="TCP port to bind/connect (default 8085).")
    args = parser.parse_args()

    server = MCPServer(mode=args.runtime)

    server.run(args.host, args.port)

if __name__ == "__main__":
    main()
