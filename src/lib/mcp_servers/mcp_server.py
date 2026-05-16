""" 20251101 MMH mcp_server.py — FastMCP server that discovers 
        tools/prompts/resources.
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


# -----------------------------
# Define global variables for logger and runtime context.
# The actual initialization will happen in the main() function, which is the entry point
# when launched "stand alone".
# -----------------------------
logger = Logger

ctx: RuntimeContext

# -----------------------------
# Paths to tool, prompt, resource packages
# -----------------------------

def get_lib_root() -> Path:
    """ Get the root directory of the library, which is the parent of the current 
        file's directory.
        Returns:
            Path: The root directory of the library.
    """
    return Path(__file__).parents[1]


def _get_tools_dir() -> Path:
    """ Get the directory where tool packages are located.
        Returns:
            Path: The directory where tool packages are located.
    """
    return get_lib_root() / "tools"


def _get_prompts_dir() -> Path:
    """ Get the directory where prompt packages are located.
        Returns:
            Path: The directory where prompt packages are located.
    """
    return get_lib_root() / "prompts"


def _get_resources_dir() -> Path:
    """ Get the directory where resource packages are located.
        Returns:
            Path: The directory where resource packages are located.
    """
    return get_lib_root() / "resources"

# def _get_cache_dir()->Path:
#     return ctx.transcript_dir()



# -----------------------------
# Server instance & conventions
# -----------------------------
mcp = FastMCP(
    name="MCP_Server",
    include_tags={"public", "api"},
    exclude_tags={"internal", "deprecated"},
    on_duplicate_tools="error",
    on_duplicate_resources="warn",
    on_duplicate_prompts="replace",
    # strict_input_validation=False,
    include_fastmcp_meta=False,
)


def purge_server_cache(days: int = 1) -> None:
    """ Purge transcript cache files older than `days` days.
        Args:
            days (int): Number of days to keep cache files. Default is 7 days.
    """
    cutoff = time.time() - (days * 86400)

    for f in ctx.transcript_dir().iterdir():
        if f.is_file() and f.stat().st_atime < cutoff:
            f.unlink(missing_ok=True)


# -----------------------------------------
# Attach everything to FastMCP at startup
# -----------------------------------------
def attach_everything():
    """ 20251101 MMH attach_everything registers all tools and prompts to the FastMCP server.
        Warning: The server will pull in all the code from a tool or prompt package.
        Any error in a file will cause the tools or prompts in that package to be ignored.
        Make sure you trust the code in those packages!
    """

    # Purge old cache files on server startup
    purge_server_cache(days=1)
    PyRegistrar(
                    mcp=mcp,
                    app_ctx=ctx,
                    module_dir=_get_tools_dir(),
                ).register()
    logger.info("Tools registered.")

    PromptRegistrar(
                        mcp=mcp,
                        app_ctx=ctx,
                        module_dir=_get_prompts_dir(),
                    ).register()
    logger.info("Prompt functions registered.")
    logger.info("Markdown files parsed and prompts registered.")

    ResourcesRegistrar(
                            mcp=mcp,
                            app_ctx=ctx,
                            module_dir=_get_resources_dir(),
                        ).register()
    logger.info("Resources registered.")


def launch_server(host:str="127.0.0.1", port:int=8085):
    """ 20251101 MMH launch_server
        The entry point to start the FastMCP server. 
        Launch the FastMCP server with all tools and prompts attached. 
    """
    global ctx
    ctx = RuntimeContext(
        create_service_context(
            app_name="mcp_server",
            app_author="HenCode",
            app_dir=Path(__file__).parent
        )
    )

    # -----------------------------
    # Logging setup
    # -----------------------------
    configure_logging(
                    LogConfig(ctx.app_name, log_level="INFO"),
                    force=True,
                    file_log_conf=FileLogConfig(log_file=ctx.log_path()),
                    tee_console=True,
                )
    global logger
    logger = get_logger(__name__)

    logger.info("mcp_server started.")
    attach_everything()
    mcp.run(transport="http", host=host, port=port)
    logger.info("MCP Server started on http://%s:%d", host, port)

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

def main():
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

    launch_server(args.host, args.port)

if __name__ == "__main__":
    main()
