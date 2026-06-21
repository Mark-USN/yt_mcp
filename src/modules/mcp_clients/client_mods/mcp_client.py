"""
Universal MCP client.

Connects to a FastMCP server, lists its tools/resources/templates/prompts,
and exercises known workflows using safe, deterministic arguments.
"""

from __future__ import annotations

from dataclasses import dataclass
from fastmcp.client.client import CallToolResult
from fastmcp import Client
# from fastmcp.prompts import PromptResult, Message
# from fastmcp.resources import ResourceResult, ResourceContent


@dataclass(slots=True, frozen=True)
class ServerConfig:
    """ Configuration for connecting to an MCP server. """
    host: str
    port: int
    path: str = "/mcp"
    scheme: str = "http"

    @property
    def url(self) -> str:
        """ Construct the full URL for connecting to the MCP server. """
        path = self.path if self.path.startswith("/") else f"/{self.path}"
        return f"{self.scheme}://{self.host}:{self.port}{path}"

class McpClient(Client):
    """ MCP client for interacting with a FastMCP server. """
    def __init__(self, host: str, port: int) -> None:
        """ Initialize the MCP client with the given host and port. 
        Args:
                    host: The hostname or IP address of the MCP server.
                    port: The port number on which the MCP server is listening.
        """
        self.config = ServerConfig(host=host, port=port)
        super().__init__(self.config.url)

    async def ping_server(self) -> bool:
        """ Ping the MCP server to check its availability. """
        async with self:
            return await self.ping()

    async def list_selected(self, selected: set[str]) -> dict[str, CallToolResult]:
        """ List the selected categories of tools/resources/templates/prompts from the MCP server.
            Args:
                selected: A set of strings indicating which categories to list. Valid values are
                          "tools", "resources", "templates", and "prompts".
            Returns:
                A dictionary mapping each selected category to its corresponding list of items.
        """
        # results: dict[str, list[Any]] = {}
        results: dict[str, CallToolResult] = {}
        async with self:
            if "tools" in selected:
                results["tools"] = await self.list_tools()

            if "resources" in selected:
                results["resources"] = await self.list_resources()

            if "templates" in selected:
                results["templates"] = await self.list_resource_templates()

            if "prompts" in selected:
                results["prompts"] = await self.list_prompts()

        return results

    async def close(self) -> None:
        """ Close the MCP client connection. """
        await self.__aexit__(None, None, None)
