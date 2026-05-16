
""" Example FastMCP resources demonstrating various return types, template URIs,
    and annotations.
"""

from __future__ import annotations

import json
from typing import TypeVar
from fastmcp import FastMCP
from yt_lib.utils.app_context import RuntimeContext
from yt_lib.utils.log_utils import get_logger # , log_tree


T = TypeVar("T", bound=FastMCP)

logger = get_logger(__name__)

# Basic dynamic resource returning a string
def get_greeting() -> str:
    """Provides a simple greeting message."""
    return "Hello from FastMCP Resources!"

# Resource returning JSON data
def get_config() -> str:
    """Provides application configuration as JSON."""
    return json.dumps({
        "theme": "dark",
        "version": "1.2.0",
        "features": ["tools", "resources"],
    })

# Template URI includes {city} placeholder
def get_weather(city: str) -> str:
    """Provides weather information for a specific city."""
    return json.dumps({
        "city": city.capitalize(),
        "temperature": 22,
        "condition": "Sunny",
        "unit": "celsius"
    })

# Template with multiple parameters and annotations
def get_repo_info(owner: str, repo: str) -> str:
    """Retrieves information about a GitHub repository."""
    return json.dumps({
        "owner": owner,
        "name": repo,
        "full_name": f"{owner}/{repo}",
        "stars": 120,
        "forks": 48
    })

def register(mcp: T, parent_ctx: RuntimeContext) -> None:
    """Register resources with the MCP server instance."""
    logger.info("Registering resources")
    _ctx=parent_ctx

    mcp.resource("resource://greeting", tags={"public", "api"})(get_greeting)
    mcp.resource("data://config", tags={"public"})(get_config)
    mcp.resource("weather://{city}/current", tags={"public"})(get_weather)
    mcp.resource(
        "repos://{owner}/{repo}/info",
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True
        },
        tags={"public"}
    )(get_repo_info)
