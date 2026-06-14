"""OpenAI client helpers used by the yt_mcp client."""

from __future__ import annotations

import json
from collections.abc import Sequence

from openai import AsyncOpenAI
from yt_lib.utils.agent_messages import LlmMessage, llm_messages_to_openai_responses_input
from yt_lib.utils.api_vault import ApiVault
from modules.utils.client_prompt_data import (
    NormalizedQuery,
    YOUTUBE_QUERY_TEXT_FORMAT,
    normalized_query_from_mapping,
)

DEFAULT_OPENAI_MODEL = "gpt-5.2"


def get_openai_client() -> AsyncOpenAI:
    """Return an authenticated async OpenAI client using ApiVault key management."""
    vault = ApiVault()
    openai_key = vault.get_value(key="OPENAI_KEY")
    if not openai_key:
        raise RuntimeError("Missing OPENAI_KEY from ApiVault")

    return AsyncOpenAI(api_key=openai_key)


async def normalize_youtube_query(
    messages: Sequence[LlmMessage],
    *,
    model: str = DEFAULT_OPENAI_MODEL,
    ai_client: AsyncOpenAI | None = None,
) -> NormalizedQuery:
    """Normalize a YouTube search query with OpenAI and return typed prompt data."""
    openai_client = ai_client or get_openai_client()

    response = await openai_client.responses.create(
        model=model,
        input=llm_messages_to_openai_responses_input(messages),
        text={"format": YOUTUBE_QUERY_TEXT_FORMAT},
    )

    raw = response.output_text.strip()
    if not raw:
        raise RuntimeError("OpenAI returned an empty normalized query response")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"OpenAI returned invalid JSON: {raw!r}") from exc

    if not isinstance(data, dict):
        raise RuntimeError(f"OpenAI returned JSON {type(data)!r}, expected object")

    return normalized_query_from_mapping(data)


# def post_filter(
#         results: list[dict[str, Any]],
#         normalized: NormalizedQuery,
#     ) -> list[dict[str, Any]]:
#     """ Post-filter YouTube search results based on a normalized query.
#         Args:
#             results (list[dict[str, Any]]): The raw search results from YouTube.
#             normalized (NormalizedQuery): The normalized query to filter results against.
#         Returns:
#             list[dict[str, Any]]: The filtered list of search results.
#     """
#     filtered: list[dict[str, Any]] = []

#     for r in results:
#         title = (r["title"] or "").lower()
#         description = (r["description"] or "").lower()

#         text = f"{title} {description}"

#         # required terms
#         if not all(term.lower() in text for term in normalized.includes):
#             continue

#         # excluded terms
#         if any(term.lower() in text for term in normalized.excludes):
#             continue

#         # phrases
#         if not all(phrase.lower() in text for phrase in normalized.phrases):
#             continue

#         # channel name check (if needed)
#         if normalized.channels:
#             if (r.get("channel_title") or "") not in normalized.channels:
#                 continue

#         filtered.append(r)

#     return filtered
