"""Client-side data structures for the YouTube query normalizer prompt."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final
from copy import deepcopy


@dataclass(frozen=True, slots=True)
class NormalizedQuery:
    """Structured representation of a YouTube search query normalized by an LLM."""

    query: str
    includes: list[str]
    excludes: list[str]
    phrases: list[str]
    channels: list[str]
    notes: str


YOUTUBE_QUERY_SCHEMA: Final[dict[str, Any]] = {
    "name": "youtube_query_normalized",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "query": {"type": "string"},
            "includes": {"type": "array", "items": {"type": "string"}},
            "excludes": {"type": "array", "items": {"type": "string"}},
            "phrases": {"type": "array", "items": {"type": "string"}},
            "channels": {"type": "array", "items": {"type": "string"}},
            "notes": {"type": "string"},
        },
        "required": ["query", "includes", "excludes", "phrases", "channels", "notes"],
    },
    "strict": True,
}

YOUTUBE_QUERY_TEXT_FORMAT: Final[dict[str, Any]] = {
    "type": "json_schema",
    **YOUTUBE_QUERY_SCHEMA,
}


def _string_list(value: Any, *, field_name: str) -> list[str]:
    """Return ``value`` as ``list[str]`` or raise a useful type error."""
    if not isinstance(value, list):
        raise TypeError(f"Expected {field_name!r} to be list[str], got {type(value)!r}")

    return [str(item) for item in value]


def normalized_query_from_mapping(data: Mapping[str, Any]) -> NormalizedQuery:
    """Build a ``NormalizedQuery`` from decoded JSON-like mapping data."""
    return NormalizedQuery(
        query=str(data["query"]),
        includes=_string_list(data.get("includes", []), field_name="includes"),
        excludes=_string_list(data.get("excludes", []), field_name="excludes"),
        phrases=_string_list(data.get("phrases", []), field_name="phrases"),
        channels=_string_list(data.get("channels", []), field_name="channels"),
        notes=str(data.get("notes", "")),
    )


def post_filter(
    data_items: list[dict[str, Any]],
    normalized: NormalizedQuery,
) -> list[dict[str, Any]]:
    """ Filter YouTube search results using a normalized query. """
    filtered_data: list[dict[str, Any]] = []

    includes = [term.lower() for term in normalized.includes]
    excludes = [term.lower() for term in normalized.excludes]
    phrases = [phrase.lower() for phrase in normalized.phrases]

    for video in data_items:
        title = str(video.get("title") or "").lower()
        description = str(video.get("description") or "").lower()
        text = f"{title} {description}"

        if not all(term in text for term in includes):
            continue

        if any(term in text for term in excludes):
            continue

        if not all(phrase in text for phrase in phrases):
            continue

        filtered_data.append(deepcopy(video))

    return filtered_data
