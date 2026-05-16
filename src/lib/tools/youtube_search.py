"""
YouTube search + metadata tools (playlist-aware; playlist expansion is opt-in).

Source baseline: /mnt/data/youtube_search.py :contentReference[oaicite:0]{index=0}
"""

from __future__ import annotations

from typing import Any, Annotated, TypeVar
from pydantic import Field
from fastmcp import FastMCP                         # pylint: disable=unused-import
from yt_lib.utils.app_context import RuntimeContext
from yt_lib.yt_search import (
    YtOrder,
    SearchKind,
    yt_search,
    yt_video_info,
    yt_playlist_info,
    yt_playlist_video_list
)
from yt_lib.utils import log_utils

logger = log_utils.get_logger(__name__)

T = TypeVar("T", bound="FastMCP")

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
        Field(default=YtOrder.RELEVANCE, description="Sort order. " + YtOrder.help_text()),
    ] = YtOrder.RELEVANCE,
    max_results: Annotated[int, Field(description="Max search items (1-50).", ge=1, le=50)] = 10,
    kinds: Annotated[
        SearchKind,
        Field(default=SearchKind.BOTH, description="Return videos only, playlists only, or both."),
    ] = SearchKind.BOTH,
) -> dict[str, Any]:
    """Search YouTube and return enriched MCP-friendly JSON (no playlist expansion)."""

    return yt_search(
        query=query,
        order=order,
        max_results=max_results,
        kinds=kinds
    )



def youtube_video_info(
    inputs: Annotated[list[str], Field(description="List of YouTube video URLs or video IDs.")],
) -> dict[str, Any]:
    """Return full metadata for one or many videos."""

    return yt_video_info(inputs=inputs)


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

    return yt_playlist_info(playlist=playlist)


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

    return yt_playlist_video_list(
        playlist=playlist,
        max_videos=max_videos
    )


def register(mcp: T, parent_ctx: RuntimeContext) -> None:
    """Register tools with FastMCP."""
    _ctx = parent_ctx
    logger.info("Registering YouTube Search tools")
    mcp.tool(tags={"public", "api"})(youtube_search)
    mcp.tool(tags={"public", "api"})(youtube_video_info)
    mcp.tool(tags={"public", "api"})(youtube_playlist_info)
    mcp.tool(tags={"public", "api"})(youtube_playlist_video_list)


def test() -> None:
    """Simple CLI entry point."""
    yt_query = "Python tutorials about list comprehension -shorts"

    logger.info("Executing youtube_search(query=%s)", yt_query)
    sr = youtube_search(query=yt_query, order=YtOrder.DATE, max_results=5, kinds=SearchKind.BOTH)
    playlist_ids = [it.get("playlist_id") for it in sr.get("items", []) if it.get("kind") ==
                    SearchKind.PLAYLIST]
    playlist_ids = [pid for pid in playlist_ids if pid]

    if playlist_ids:
        logger.info("Fetching playlist info only (no expansion)")
        pi = youtube_playlist_info(playlist=playlist_ids[:2])
        logger.info("Playlist info (no expansion): %s", pi)

        logger.info("Expanding playlist videos (opt-in)")
        pv = youtube_playlist_video_list(playlist=playlist_ids[0], max_videos=10)
        if isinstance(pv, dict):
            logger.info("Playlist video list: %s", pv)

# -------------------------------------------------------------------------------
# Search for Playlists only
# -------------------------------------------------------------------------------


    # logger.info("Executing youtube_search(query=%s)", yt_query)
    sr = youtube_search(
            query=yt_query,
            order=YtOrder.DATE,
            max_results=5,
            kinds=SearchKind.PLAYLIST
        )
    playlist_ids = [
            it.get("playlist_id") for it in sr.get("items", [])
            if it.get("kind") == SearchKind.PLAYLIST
        ]
    playlist_ids = [pid for pid in playlist_ids if pid]

    if playlist_ids:
        logger.info("Expanding playlist videos (opt-in)")
        pv = youtube_playlist_video_list(playlist=playlist_ids[0], max_videos=3)


if __name__ == "__main__":
    test()
