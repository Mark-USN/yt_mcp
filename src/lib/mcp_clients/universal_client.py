"""
Universal MCP client.

Connects to a FastMCP server, lists its tools/resources/templates/prompts,
and exercises known workflows using safe, deterministic arguments.
"""

from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from fastmcp import Client
from yt_lib.utils.log_utils import (
        INFO,
        Logger,
        LogConfig,
        FileLogConfig,
        configure_logging,
        get_logger,
        log_tree
)
from yt_lib.utils.app_context import RuntimeContext, create_user_context
from .youtube_demo import run_youtube_demo

ctx = RuntimeContext(
    create_user_context(
        app_name="universal_client",
        app_author="HenCode",
        app_dir=Path(__file__).parent
    )
)

# -----------------------------
# Logging setup
# -----------------------------
configure_logging(
                LogConfig(log_root=ctx.app_name, log_level="INFO"),
                force=True,
                file_log_conf=FileLogConfig(log_file=ctx.log_path()),
                tee_console=False,
            )
logger = get_logger(__name__)


RUN_PROMPT_EXAMPLES = True
RUN_RESOURCE_EXAMPLES = True
RUN_TOOL_EXAMPLES = True


@dataclass(slots=True, frozen=True)
class ServerConfig:
    """ Configuration for connecting to the FastMCP server. """
    host: str
    port: int

    @property
    def url(self) -> str:
        """ Construct the base URL for the FastMCP server. """
        return f"http://{self.host}:{self.port}/mcp"


class UniversalClient(Client):
    """Universal FastMCP client.

    Responsibilities:
    - connect to server
    - list tools/resources/templates/prompts
    - exercise known workflows when available
    """

    yt_search: str = (
        "English language tutorials about North American birds and their habitats."
        " Don't include videos that are just recording of bird songs."
    )
    MAX_SEARCH_RESULTS: int = 5

    tools_list: list[Any]
    tool_names: set[str]

    def __init__(self, host: str, port: int) -> None:
        """ Initialize the UniversalClient with server connection details.
            Args:
                host (str): The hostname or IP address of the FastMCP server.
                port (int): The port number of the FastMCP server.
        """
        self.config = ServerConfig(host, port)
        super().__init__(self.config.url)
        self.tools_list = []
        self.tool_names = set()

    # -------------------------------------------------
    # Paths
    # -------------------------------------------------
    def cache_output_dir(self) -> Path:
        """Return the directory for caching output."""
        return ctx.cache_dir

    # -------------------------------------------------
    # Server discovery
    # -------------------------------------------------
    async def refresh_tools(self) -> None:
        """Query the server for tools and cache their names."""
        self.tools_list = await self.list_tools()
        self.tool_names = {
            getattr(t, "name", "")
            for t in self.tools_list
            if getattr(t, "name", "")
        }

    # -------------------------------------------------
    # Main entry point
    # -------------------------------------------------
    async def run(self) -> None:
        """ Main execution method for the UniversalClient. Connects to the server, lists
            capabilities, and exercises workflows. 
        """
        async with self:
            print("\n=============== Ping the MCP Server.\n")
            result = await self.ping()
            log_tree(
                logger,
                INFO,
                "ping",
                result,
                collapse_keys={"env", "data"},  # env can be huge/noisy
                redact_keys={"token", "api_key"},
            )

            print("\n=============== List available Tools.\n")
            await self.refresh_tools()
            self._show_tools(self.tools_list)

            print("\n=============== List available Resources.\n")
            resources = await self.list_resources()
            self._show_resources(resources)

            print("\n=============== List available Templates.\n")
            templates = await self.list_resource_templates()
            self._show_templates(templates)

            print("\n=============== List available Prompts.\n")
            prompts = await self.list_prompts()
            self._show_prompts(prompts)

            if RUN_PROMPT_EXAMPLES:
                await self._run_example_prompts(prompts)

            if RUN_RESOURCE_EXAMPLES:
                await self._run_example_resources(resources)

            if RUN_TOOL_EXAMPLES:
                await self._run_example_tools()

    # -------------------------------------------------
    # Exercisers
    # -------------------------------------------------
    async def _run_example_tools(self) -> None:
        """Exercise known workflows using server-discovered tools."""
        print("\n=============== Run Tool Examples.\n")
        if "youtube_search" not in self.tool_names:
            logger.info("youtube_search not available; skipping tool exercises.")
            return

        transcript_tools = {
            "youtube_json",
            "youtube_text",
            "youtube_paragraph",
        }
        if not self.tool_names & transcript_tools:
            logger.info("No transcript tools available; skipping YouTube demo.")
            return

        await run_youtube_demo(self, ctx)

    async def _run_example_prompts(self, prompts: list[Any]) -> None:
        """ Exercise known workflows using server-discovered prompts.
            Args:
                prompts (list[Any]): A list of prompts to exercise.
            Returns:
                None
        """
        print("\n=============== Run Prompt Examples.\n")
        names = {getattr(p, "name", "") for p in prompts if getattr(p, "name", "")}
        if "youtube_query_normalizer" not in names:
            return

        search_string = "Find English language videos on python list comprehensions"
        logger.info("Executing youtube_query_normalizer prompt")
        result = await self.get_prompt(
            "youtube_query_normalizer",
            {"search_string": search_string},
        )

        # 20260125 MMH dump the result from youtube_query_normalizer
        # logger.info("youtube_query_normalizer result = \n%s",json.dumps(
        # result.messages[0].content, indent=2, ensure_ascii=False))

        for msg in getattr(result, "messages", []) or []:
            logger.info("Prompt output: %s", getattr(msg, "content", msg))

    async def _run_example_resources(self, resources: list[Any]) -> None:
        print("\n=============== Run Resource and Template Examples.\n")
        result = await self.read_resource("resource://greeting")
        print(f"Greeting output: {result[0].text}")
        result = await self.read_resource("data://config")
        print(f"Config output: {result[0].text}")
        result = await self.read_resource("weather://stockton/current")
        print(f"Weather output: {result[0].text}")
        result = await self.read_resource("repos://Mark-USN/yt_mcp/info")
        print(f"Repos output: {result[0].text}")
        result = await self.read_resource("file://countries.json")
        decoded = base64.b64decode(result[0].blob).decode("utf-8")
        print(f"countries.jason output: {decoded}")
        result = await self.read_resource("resource://UnicodeTable.md")
        print(f"UnicodeTable.md output:\n{result[0].text}")

    # -------------------------------------------------
    # Display helpers
    # -------------------------------------------------
    def _show_tools(self, tools: list[Any]) -> None:
        """ Display the list of tools in a readable format.
            Args:
                tools (list[Any]): A list of tools to display.
        """
        logger.info("\n\nAvailable Tools:")
        for t in tools:
            logger.info("Tool: %s", getattr(t, "name", None))

    def _show_resources(self, resources: list[Any]) -> None:
        """ Display the list of resources in a readable format.
            Args:
                resources (list[Any]): A list of resources to display.
        """
        logger.info("\n\nAvailable Resources:")
        for r in resources:
            logger.info("Resource: %s", getattr(r, "uri", None))

    def _show_templates(self, templates: list[Any]) -> None:
        """ Display the list of resource templates in a readable format.
            Args:
                templates (list[Any]): A list of resource templates to display. 
        """
        logger.info("\n\nAvailable Resource Templates:")
        for t in templates:
            logger.info("Template: %s", getattr(t, "uriTemplate", None))

    def _show_prompts(self, prompts: list[Any]) -> None:
        """ Display the list of prompts in a readable format.
            Args:
                prompts (list[Any]): A list of prompts to display.
        """
        logger.info("\n\nAvailable Prompts:")
        for p in prompts:
            logger.info("Prompt: %s", getattr(p, "name", None))


def main() -> None:
    """ Main entry point for the Universal MCP client. """
    asyncio.run(UniversalClient("127.0.0.1", 8085).run())


if __name__ == "__main__":
    main()
