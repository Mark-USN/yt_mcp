"""YouTube transcript tool for FastMCP.

This module fetches transcripts/subtitles for a YouTube video using
`youtube-transcript-api`, with a best-effort on-disk cache.

Key behaviors:
- Accepts either a full YouTube URL or a bare video id.
- Tries preferred languages first (descending priority).
- Falls back to translating the first available transcript when possible.
- Writes/reads a JSON cache under a configurable cache directory.

Environment variables:
- MCP_CACHE_DIR: override the base cache directory.

Notes for AI agents:
- The primary public entrypoints (MCP tools) are `youtube_json()` and
  `youtube_text()`.
- `fetch_transcript()` is the core I/O function; it returns raw transcript
  snippets as JSON-serializable dictionaries.
"""

from __future__ import annotations

import time
from typing import TypeVar
from collections.abc import Sequence
from fastmcp import FastMCP  # pylint: disable=unused-import
from yt_lib.utils.log_utils import get_logger
from yt_lib.yt_types import Snippet
from yt_lib.yt_transcript import yt_json, TranscriptPaths, set_info
from yt_lib.utils.app_info import RuntimeInfo

logger = get_logger(__name__)

T = TypeVar("T", bound="FastMCP")

def youtube_json(
    url: str,
    prefer_langs: Sequence[str] | None = None,
) -> list[Snippet] | None:
    """Return the raw transcript snippets (typed), or None.

    This is the "structured" variant intended for typed workflow engines.
    It returns the same data that `fetch_transcript()` produces (a list of
    TranscriptSnippet dicts), without JSON serialization.

    Args:
        url: YouTube URL or video id.
        prefer_langs: Preferred language codes (descending priority).

    Returns:
        A JSON string or None.

    """
    return yt_json(
        url=url,
        prefer_langs=prefer_langs
    )



def register(mcp: T, info: RuntimeInfo) -> None:
    """Register YouTube transcript tools with the MCP instance."""

    paths = TranscriptPaths(
        transcript_dir=info.transcript_dir,
    )

    set_info(paths)

    logger.debug("Registering YouTube transcript tools")
    mcp.tool(tags={"public", "api"})(youtube_json)


def test() -> None:
    """CLI entry point to test transcript retrieval (outside MCP)."""
    # pylint: disable=import-outside-toplevel
    from datetime import timedelta

    yt_url = "https://www.youtube.com/watch?v=ulebPxBw8Uw"

    while not yt_url:
        yt_url = input("Enter YouTube URL: ").strip()
        if not yt_url:
            logger.warning("Please paste a valid YouTube URL.")

    start = time.perf_counter()
    trans = youtube_json(yt_url)
    elapsed = time.perf_counter() - start
    print("\n\n--- JSON TRANSCRIPT ---\n")
    # `youtube_jason()` already returns a JSON string.
    print(trans)
    print(f"\nTranscribed in {timedelta(seconds=elapsed)}.\n")



if __name__ == "__main__":
    test()
