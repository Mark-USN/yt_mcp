""" 20260516 MMH mcp_server.py — Move into a class MCPServer that can be instantiated and
    launched from a CLI or imported and used in other contexts. 
    Based on https://gofastmcp.com/servers/server
    Added code to automatically register tools and prompts from their packages.
        from the 'tools' package,
"""

# pylint: disable=global-statement

from __future__ import annotations

import argparse
import time
from pathlib import Path
from fastmcp import FastMCP
from yt_lib.utils.log_utils import (
    Logger,
    LogConfig,
    FileLogConfig,
    configure_logging,
    get_logger
)
from yt_lib.utils.app_context import RuntimeContext, create_service_context
from lib.utils.modules_registrar import PyRegistrar, PromptRegistrar, ResourcesRegistrar


class MCPServer:
    """ Class-based implementation of the MCP server. 
        Implements the dynamic discovery and registration of tools, prompts and resources from
        their respective packages.
    """
    mcp: FastMCP
    ctx: RuntimeContext
    logger: Logger
    lib_root: Path
    tools_root: Path
    prompts_root: Path
    resources_root: Path


    def __init__(
            self,
            server_name: str = "MCP_Server",
            app_author: str = "HenCode",
            app_dir: Path | None = None,
            lib_root: Path | None = None,
        ) -> None:
        # -----------------------------
        # context setup
        # -----------------------------
        self.ctx = RuntimeContext(
            create_service_context(
                app_name=server_name,
                app_author=app_author,
                app_dir=app_dir or Path(__file__).resolve().parent,
            )
        )

        # -----------------------------
        # Logging setup
        # -----------------------------
        configure_logging(
                        LogConfig(self.ctx.app_name, log_level="INFO"),
                        force=True,
                        file_log_conf=FileLogConfig(log_file=self.ctx.log_path()),
                        tee_console=True,
                    )
        self.logger = get_logger(server_name)

        # -----------------------------
        # MCP setup
        # -----------------------------
        self.mcp = FastMCP(
                name=server_name,
                include_tags={"public", "api"},
                exclude_tags={"internal", "deprecated"},
                on_duplicate_tools="error",
                on_duplicate_resources="warn",
                on_duplicate_prompts="replace",
                # strict_input_validation=False,
                include_fastmcp_meta=False,
            )

        # -----------------------------
        # Directory tree setup
        # -----------------------------
        self.lib_root = lib_root or self.ctx.app_dir.parent
        self.tools_root = self.lib_root / "tools"
        self.prompts_root = self.lib_root / "prompts"
        self.resources_root = self.lib_root / "resources"

    def purge_server_cache(self, days: int = 1) -> None:
        """ Purge transcript cache files older than `days` days.
            Args:
                days (int): Number of days to keep cache files. Default is 1 day.
        """
        cutoff = time.time() - (days * 86400)

        for f in self.ctx.transcript_dir().iterdir():
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

        # Purge old cache files on server startup
        self.purge_server_cache(days=1)
        PyRegistrar(
                        mcp=self.mcp,
                        app_ctx=self.ctx,
                        module_dir=self.tools_root,
                    ).register()
        self.logger.info("Tools registered.")

        PromptRegistrar(
                            mcp=self.mcp,
                            app_ctx=self.ctx,
                            module_dir=self.prompts_root,
                        ).register()
        self.logger.info("Prompt functions registered.")
        self.logger.info("Markdown files parsed and prompts registered.")

        ResourcesRegistrar(
                                mcp=self.mcp,
                                app_ctx=self.ctx,
                                module_dir=self.resources_root,
                            ).register()
        self.logger.info("Resources registered.")


    def run(self, host:str="127.0.0.1", port:int=8085) -> None:
        """ 20251101 MMH launch_server
            The entry point to start the FastMCP server. 
            Launch the FastMCP server with all tools and prompts attached. 
        """
        self.logger.info("mcp_server starting.")
        self.attach_everything()
        self.mcp.run(transport="http", host=host, port=port)
        self.logger.info("MCP Server started on http://%s:%d", host, port)

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

def main() -> None:
    """ 20251101 MMH main
        Main entry point when launched "stand alone" 
        Parse arguments and start the server. 
    """
    parser = argparse.ArgumentParser(description="Create and run an MCP server.")
    parser.add_argument("--host", type=str, default="127.0.0.1",
                        help="Host name or IP address (default 127.0.0.1).")
    parser.add_argument("--port", type=port_type, default=8085,
                        help="TCP port to bind/connect (default 8085).")
    args = parser.parse_args()

    server = MCPServer()

    server.run(args.host, args.port)

if __name__ == "__main__":
    main()
