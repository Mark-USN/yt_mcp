"""
    Test stub for running various MCP servers and clients, and other tools
    This is a temporary utility for development and testing purposes.
    Many test can be run directly by calling uv run -m lib.dir.name.
"""

# pylint: disable=import-outside-toplevel

#./src/debug_stub.py

import asyncio
import argparse
import sys
from yt_lib.utils.log_utils import configure_logging, get_logger # , log_tree

# -----------------------------
# Logging setup
# -----------------------------
logger = get_logger(__name__)


def debug_stub():
    """ Main entry point: parse arguments and start/stop server or run client. """    
    parser = argparse.ArgumentParser(
        description="Create and run an MCP server or client."
    )

    parser.add_argument("--test",
        choices=["demo-server", "long-job-server", "universal-client", "yt-search", "yt-audio"],
        type=str.lower,
        required=True,
        help="Run as server, long_job_server, client, or stop-server."
    )

    args = parser.parse_args()

    # 20251215 MMH Show help if no arguments are given
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)  # Exit with an error code

    match args.test:
        case "mcp-server":
            import lib.mcp_servers.mcp_server as demo
            demo.main()
        case "universal-client":
            from lib.mcp_clients.universal_client import UniversalClient
            # import lib.mcp_clients.universal_client as uc
            asyncio.run(UniversalClient("127.0.0.1", 8085).run())
        case "yt_search":
            import lib.tools.youtube_search as yt_search
            # from lib.utils.api_keys import api_vault
            # api_keys = api_vault()
            # google_key = api_keys.get_value("GOOGLE_KEY")
            yt_search.test()

if __name__ == "__main__":
    # -----------------------------
    # Logging setup
    # -----------------------------
    configure_logging()

    debug_stub()
