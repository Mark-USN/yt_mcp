# math_tools.py
""" Math tools module for FastMCP server. """
# import logging
from typing import TypeVar
# from pathlib import Path
from fastmcp import FastMCP
from yt_lib.utils.log_utils import get_logger # , log_tree
from yt_lib.utils.app_context import RuntimeContext

T = TypeVar("T", bound=FastMCP)

# -----------------------------
# Logging setup
# -----------------------------
logger = get_logger(__name__)



def add(a: float, b: float) -> str:
    """Add two numbers (strings ok); returns string."""
    return str(float(a) + float(b))

def multiply(a: float, b: float) -> str:
    """Multiply two numbers (strings ok); returns string."""
    return str(float(a) * float(b))

def register(mcp: T, parent_ctx: RuntimeContext) -> None:
    """Register math tools with MCPServer."""
    _ctx = parent_ctx
    logger.info("Registering math tools")
    mcp.tool(tags={"public", "api"})(add)
    mcp.tool(tags={"public", "api"})(multiply)
