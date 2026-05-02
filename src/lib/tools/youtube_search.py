"""
YouTube search + metadata tools (playlist-aware; playlist expansion is opt-in).

Source baseline: /mnt/data/youtube_search.py :contentReference[oaicite:0]{index=0}
"""

from __future__ import annotations

# import json
import logging
import re
import threading
import os
from collections.abc import Iterable
from enum import Enum
from typing import Any, Annotated
from pydantic import Field
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from fastmcp import FastMCP
from yt_lib.utils.app_context import RunContextStore
from yt_lib.yt_ids import (
    YoutubeIdKind,
    extract_video_id,
    is_playlist_id,
    extract_playlist_id
)
from yt_lib import yt_search
from yt_lib.yt_search import (
    YtOrder,
    SearchKind
)

from yt_lib.utils.api_keys import api_vault
from yt_lib.utils.log_utils import get_logger, log_tree
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

def youtube_search(
    query: Annotated[
        str,
        Field(
            description=(
                "Search query using standard web-search syntax when possible. "
                "Supports quoted phrases and exclusion with '-'."
            )
        ),
    ],
    order: Annotated[
        YtOrder,
        Field(default=YtOrder.relevance, description="Sort order. " + YtOrder.help_text()),
    ] = YtOrder.relevance,
    max_results: Annotated[int, Field(description="Max search items (1-50).", ge=1, le=50)] = 10,
    kinds: Annotated[
        SearchKind,
        Field(default=SearchKind.both, description="Return videos only, playlists only, or both."),
    ] = SearchKind.both,
) -> dict[str, Any]:
    """Search YouTube and return enriched MCP-friendly JSON (no playlist expansion)."""

    return yt_search.youtube_search(
        query=query,
        order=order,
        max_results=max_results,
        kinds=kinds
    )



def youtube_video_info(
    inputs: Annotated[list[str], Field(description="List of YouTube video URLs or video IDs.")],
) -> dict[str, Any]:
    """Return full metadata for one or many videos."""

    return yt_search.yt_video_info(inputs=inputs)


# CHANGE (request #3): playlist arg is ONLY str | list[str]
def youtube_playlist_info(
    playlist: Annotated[
        str | list[str],
        Field(description="Playlist URL/ID or list of playlist URLs/IDs."),
    ],
) -> dict[str, Any] | list[dict[str, Any]]:
    """Return general playlist metadata only.

    This does NOT fetch playlistItems or video metadata.
    """

    return yt_search.yt_playlist_info(playlist=playlist)


# CHANGE (request #1): separate opt-in expansion tool
def youtube_playlist_video_list(
    playlist: Annotated[
        str | list[str],
        Field(description="Playlist URL/ID or list of playlist URLs/IDs."),
    ],
    max_videos: Annotated[int, Field(description="Max videos per playlist.", ge=1, le=500)] = 50,
) -> dict[str, Any] | list[dict[str, Any]]:
    """Return playlist videos enriched with video_info-style metadata.

    Output shape per playlist:
      {
        "kind": "playlist_videos",
        "playlist_id": "...",
        "url": "https://www.youtube.com/playlist?list=...",
        "max_videos": 50,
        "items": { "<videoId>": { ...playlist_fields..., ...video_fields... } },
        "errors": [...]
      }
    """

    return yt_search.yt_playlist_video_list(
        playlist=playlist,
        max_videos=max_videos
    )


def register(mcp: T, ctx: RunContextStore) -> None:
    """Register tools with FastMCP."""
    logger.info("Registering YouTube Search tools")
    mcp.tool(tags=["public", "api"])(youtube_search)
    mcp.tool(tags=["public", "api"])(youtube_video_info)
    mcp.tool(tags=["public", "api"])(youtube_playlist_info)
    mcp.tool(tags=["public", "api"])(youtube_playlist_video_list)


def test() -> None:
    """Simple CLI entry point."""
    yt_search = "Python tutorials about list comprehension -shorts"

    logger.info("Executing youtube_search(query=%s)", yt_search)
    sr = youtube_search(query=yt_search, order="date", max_results=5, kinds="video,playlist")
    # log_tool_result("youtube_search", sr, level=logging.INFO)

    playlist_ids = [it.get("playlist_id") for it in sr.get("items", []) if it.get("kind") == "playlist"]
    playlist_ids = [pid for pid in playlist_ids if pid]

    if playlist_ids:
        logger.info("Fetching playlist info only (no expansion)")
        pi = youtube_playlist_info(playlist=playlist_ids[:2])
        # log_tool_result("youtube_playlist_info", {"items": pi if isinstance(pi, list) else [pi]}, level=logging.INFO)

        logger.info("Expanding playlist videos (opt-in)")
        pv = youtube_playlist_video_list(playlist=playlist_ids[0], max_videos=10)
        # if isinstance(pv, dict):
        #     log_tool_result("youtube_playlist_video_list", {"items": pv.get("items", {})}, level=logging.INFO, items_key="items")

# -------------------------------------------------------------------------------
# Search for Playlists only
# -------------------------------------------------------------------------------


    # logger.info("Executing youtube_search(query=%s)", yt_search)
    sr = youtube_search(query=yt_search, order="date", max_results=5, kinds="playlist")
    # log_tool_result("youtube_search", sr, level=logging.INFO)

    playlist_ids = [it.get("playlist_id") for it in sr.get("items", []) if it.get("kind") == "playlist"]
    playlist_ids = [pid for pid in playlist_ids if pid]

    if playlist_ids:
        logger.info("Expanding playlist videos (opt-in)")
        pv = youtube_playlist_video_list(playlist=playlist_ids[0], max_videos=3)
        # if isinstance(pv, dict):
        #     log_tool_result("youtube_playlist_video_list", {"items": pv.get("items", {})}, level=logging.INFO, items_key="items")


if __name__ == "__main__":
    test()
