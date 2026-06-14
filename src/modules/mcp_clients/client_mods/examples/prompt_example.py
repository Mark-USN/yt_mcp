""" Example of executing MCP's youtube_query_normalizer prompt and processing the results through
    an OpenAI Agent.
"""

from __future__ import annotations

import time
from fastmcp import Client
from fastmcp.prompts import PromptResult

from openai import AsyncOpenAI

from yt_lib.utils.agent_messages import prompt_result_messages_to_llm
from yt_lib.utils.log_utils import get_logger
from yt_lib.utils.tree_view import TreeView, TreeViewConfig

from modules.open_ai.openai_client import get_openai_client, normalize_youtube_query
from modules.utils.client_prompt_data import NormalizedQuery
from modules.mcp_clients.client_mods.output_sink import OutputSink, NullOutputSink

logger = get_logger(__name__)


class PromptExample:
    """Exercise the youtube_query_normalizer MCP prompt."""

    def __init__(
        self,
        mcp_client: Client,
        *,
        emit: OutputSink = NullOutputSink(),
    ) -> None:
        """ Initialize the PromptExample.
            Args:
                mcp_client: The MCP client instance.
                emit: An optional output sink for emitting messages (default is NullOutputSink).
        """
        self.mcp_client = mcp_client
        self.ai_agent: AsyncOpenAI = get_openai_client()
        self.emit = emit or (lambda _message: None)

        tv_cfg = TreeViewConfig()
        tv_cfg.collapse_keys={"env", "data"}
        tv_cfg.redact_keys={"token", "api_key"}

        self.tv = TreeView(tv_cfg)

    async def run(self, search_string: str) -> NormalizedQuery:
        """ Run the prompt example with the given search string.
            Args:
                search_string: The search string to normalize.
            Returns:
                The normalized query result.
        """
        start = time.perf_counter()

        self.emit("Executing youtube_query_normalizer prompt...")
        logger.info("Executing youtube_query_normalizer prompt")

        mcp_prompt_result: PromptResult = await self.mcp_client.get_prompt(
            "youtube_query_normalizer",
            {"search_string": search_string},
        )
        self.emit(self.tv.render_tree(obj=mcp_prompt_result, title="MCP Prompt Result:"))

        llm_messages = prompt_result_messages_to_llm(mcp_prompt_result.messages)

        self.emit("")
        self.emit(self.tv.render_tree(obj=llm_messages, title="LLM Messages"))

        self.emit("")
        self.emit("Calling OpenAI query normalizer...")

        ai_query_results = await normalize_youtube_query(
            llm_messages,
            ai_client=self.ai_agent,
        )

        elapsed = time.perf_counter() - start

        self.emit("")
        self.emit(self.tv.render_tree(obj=ai_query_results, title="AI Query Results:"))

        self.emit("")
        self.emit(f"Normalized YouTube query: {ai_query_results.query}")
        self.emit(f"Prompt example completed in {elapsed:.2f} seconds.")

        logger.info("Normalized YouTube query: %s", ai_query_results.query)
        return ai_query_results
