""" Example of how to use the MCP client to perform a YouTube search,
    optionally normalize the search query using an MCP Prompt in conjunction with an AI agent,
    and post-filter the results.
"""
# pylint: disable=global-statement

from __future__ import annotations

import time
from copy import deepcopy
from typing import Any
from fastmcp import Client
from mcp.types import CallToolResult
from openai import AsyncOpenAI
from yt_lib.utils.log_utils import get_logger
from yt_lib.utils.tree_view import TreeView, TreeViewConfig
from modules.utils.client_prompt_data import NormalizedQuery, post_filter

from modules.mcp_clients.client_mods.output_sink import OutputSink, NullOutputSink


MAX_SEARCH_RESULTS: int = 50

logger = get_logger(__name__)

class SearchExample:
    """ Example of how to use the MCP client to perform a YouTube search,
        optionally normalize the search query using an MCP Prompt in conjunction with an AI agent,
        and post-filter the results.
    """
    mcp_client: Client
    ai_agent: AsyncOpenAI | None
    tv: TreeView

    def __init__(self, client: Client, emit: OutputSink = NullOutputSink()) -> None:
        """ Initialize the SearchExample with an MCP client.
            Args:
                client: An instance of the MCP Client to use for calling tools and getting prompts.
                emit: An instance of an OutputSink to handle output messages.
        """
        self.mcp_client = client
        self.emit = emit or (lambda _message: None)

        tv_cfg = TreeViewConfig()
        tv_cfg.collapse_keys={"env", "data"}
        tv_cfg.redact_keys={"token", "api_key"}

        self.tv = TreeView(tv_cfg)


    async def run(
                    self,
                    search_string: str,
                    max_results:int = MAX_SEARCH_RESULTS,
        ) -> CallToolResult | None:
        """ Run the YouTube search example without AI query normalization.
            Args:
                search_string: The search query string.
                max_results: The maximum number of search results to return.
            Returns:
                A CallToolResult containing a list of dictionaries representing the search results,
                or None if no results are found.
        """
        self.emit("Executing youtube_search...")
        yt_search_args: dict[str, str | int] = {
                        "query": search_string,
                        "order": "relevance",
                        "max_results": max_results,
                    }
        self.emit("")
        self.emit("Running youtube_search:")

        logger.info("Running youtube_search:")
        start = time.perf_counter()

        search_results: CallToolResult = await self.mcp_client.call_tool(
                                                                "youtube_search",
                                                                yt_search_args
                                                            )

        elapsed = time.perf_counter() - start
        # This is the title for treeview rendering of the search results, it includes the query,
        # order, and max_results for context.
        call_title = (
            'youtube_search('
            f'query: {yt_search_args["query"]}, '
            f'order: {yt_search_args["order"]}, '
            f'max_results: {yt_search_args["max_results"]}) results'
        )
        self.emit("")
        self.emit(self.tv.render_tree(obj=search_results, title=call_title))
        self.emit(f"youtube_search completed in {elapsed:.2f} seconds.")

        return search_results



    async def run_ai(
                    self,
                    normalized_query: NormalizedQuery,
                    max_results:int = MAX_SEARCH_RESULTS,
        ) -> CallToolResult | None:
        """ Run the YouTube search example, which includes query normalization with an
            the MCP prompt and the AI agent and post-filtering of the results.
            Args:
                normalized_query: A NormalizedQuery object containing the normalized search query
                                  and metadata.
                max_results: The maximum number of search results to return.
            Returns:
                A CallToolResult containing a list of dictionaries representing the search results,
                or None if no results are found.
        """
        self.emit("Executing youtube_search...")
        yt_search_args: dict[str, str | int] = {
                        "query": normalized_query.query,
                        "order": "relevance",
                        "max_results": max_results,
                    }
        self.emit("")
        self.emit("Running youtube_search:")

        logger.info("Running youtube_search:")
        total_start = time.perf_counter()
        start = total_start

        search_results: CallToolResult = await self.mcp_client.call_tool(
                                                            "youtube_search",
                                                            yt_search_args
                                                        )
        elapsed = time.perf_counter() - start

        original_data = search_results.data


        # This is the title for treeview rendering of the search results, it includes the query,
        # order, and max_results for context.
        call_title = (
            'youtube_search('
            f'query: {yt_search_args["query"]}, '
            f'order: {yt_search_args["order"]}, '
            f'max_results: {yt_search_args["max_results"]}) results'
        )
        self.emit("")
        self.emit(self.tv.render_tree(obj=search_results, title=call_title))
        self.emit(f"youtube_search completed in {elapsed:.2f} seconds.")


        if not isinstance(original_data, dict):
            raise TypeError(f"Expected dict result data, got {type(original_data).__name__}")

        original_items = original_data.get("items", [])

        if not isinstance(original_items, list):
            raise TypeError("Expected data['items'] to be list, "
                            f"got {type(original_items).__name__}")

        start = time.perf_counter()
        self.emit("")
        self.emit("Post-filtering search results ...")
        modified_items = post_filter(original_items, normalized_query)
        elapsed = time.perf_counter() - start
        self.emit(self.tv.render_tree(obj=modified_items, title="Post-filtered search results:"))
        self.emit(f"Post-filtering completed in {elapsed:.2f} seconds.")

        new_data: dict[str, Any] = deepcopy(original_data)
        new_data["items"] = modified_items

        final_results = search_results.model_copy(
                            update={
                                "structuredContent": new_data,
                            },
                            deep=True,
                        )


        total_elapsed = time.perf_counter() - total_start
        self.emit(f"Total elapsed time: {total_elapsed:.2f} seconds.")

        return final_results
