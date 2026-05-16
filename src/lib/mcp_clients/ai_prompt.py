""" Example of using an LLM to normalize a YouTube search query and post-filter results."""

from __future__ import annotations

import json
# import os
from dataclasses import dataclass
from typing import Any, Iterable
from openai import OpenAI
from yt_lib.utils.api_keys import ApiVault



def _get_openai_client() -> Any:
    """ Return an authenticated OpenAI client using api_vault for key management. """
    vault = ApiVault()
    openai_key = vault.get_value(key="OPENAI_KEY")
    if not openai_key:
        raise RuntimeError("Missing OPENAI_KEY from api_vault()")
    return OpenAI(api_key=openai_key)

@dataclass(slots=True)
class NormalizedQuery:
    """ Structured representation of a YouTube search query, normalized by an LLM. """
    query: str
    includes: list[str]
    excludes: list[str]
    phrases: list[str]
    channels: list[str]
    notes: str


YOUTUBE_QUERY_SCHEMA = {
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


@dataclass(slots=True)
class LlmMessage:
    """ A normalized message format for LLM interactions."""
    role: str
    content: str


def _coerce_content_to_text(content: Any) -> str:
    """ Coerce various content formats to plain text for OpenAI input.
        Args:
            content (Any): The content to coerce, which may be a string, an object
            with a .text attribute, or a list of such items.
        Returns:
            str: The coerced text content.
        Raises:
            TypeError: If the content cannot be coerced to text.
    """
    if isinstance(content, str):
        return content

    # TextContent(...) with .text
    text = getattr(content, "text", None)
    if isinstance(text, str):
        return text

    # If your MCP ever returns a list of parts, join text parts
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
                continue
            t = getattr(part, "text", None)
            if isinstance(t, str):
                parts.append(t)
        if parts:
            return "\n".join(parts)

    raise TypeError(f"Unsupported content type for OpenAI: {type(content)!r}")

def _get(obj: Any, name: str) -> Any:
    """ Read field `name` from dict-like OR attribute-like objects.
        Args:
            obj (Any): The object to read from, which may be a dict or an object
            name (str): The name of the field to read.
        Returns:
            Any: The value of the field.
        Raises:
            KeyError: If the field is not found in a dict.
            AttributeError: If the field is not found in an object.
    """
    if isinstance(obj, dict):
        return obj[name]
    return getattr(obj, name)



def mcp_messages_to_openai(messages: list[Any]) -> list[dict[str,str]]:
    """ Convert FastMCP PromptResult.messages to OpenAI API input format.
            Args:
                messages (list[Any]): A list of messages from FastMCP, which may be dict-like
                                        or attribute-like.
            Returns:
                list[dict[str, str]]: A list of messages formatted for OpenAI API input.
            Raises:
                TypeError: If the input messages are not in a supported format.
        """
    return [{"role": str(m.role), "content": _coerce_content_to_text(m.content)} for m in messages]


def prompt_result_messages_to_llm(messages: Any) -> list[LlmMessage]:
    """ Normalize `PromptResult.messages` into a stable `list[LlmMessage]`.
        Args:
            messages (Any): The messages to normalize, which may be a string or an iterable of
                            dict-like or attribute-like objects.
        Returns:
            list[LlmMessage]: A list of normalized LlmMessage objects.
        Raises:
            TypeError: If the input messages are not in a supported format.
        Handles FastMCP return shapes:
          - messages is str  -> one user message
          - messages is list -> each element may be dict-like or attribute-like
    """
    # FastMCP docs: PromptResult.messages can be str or list[Message].
    # :contentReference[oaicite:1]{index=1}
    if isinstance(messages, str):
        return [LlmMessage(role="user", content=messages)]

    if not isinstance(messages, Iterable):
        raise TypeError(f"Expected messages to be str or iterable, got {type(messages)!r}")

    out: list[LlmMessage] = []
    for m in messages:
        role = str(_get(m, "role"))
        content = _coerce_content_to_text(_get(m, "content"))
        out.append(LlmMessage(role=role, content=content))

    return out

def _messages_to_openai_input(messages: list[LlmMessage]) -> list[dict[str, Any]]:
    """ Convert internal messages to OpenAI Responses API input items.
        Args:
            messages (list[LlmMessage]): A list of internal LlmMessage objects.
        Returns:
            list[dict[str, Any]]: A list of messages formatted for OpenAI Responses API input.
        This uses a simple pattern: one 'message' item per LlmMessage.
    """
    return [
        {
            "role": m.role,
            "content": [{"type": "input_text", "text": m.content}],
        }
        for m in messages
    ]


def normalize_youtube_query(messages: list[LlmMessage]) -> NormalizedQuery:
    """ Normalize a YouTube search query using an LLM and return a structured NormalizedQuery.
        Args:
            messages (list[LlmMessage]): The input messages to the LLM, which should include
                                         the user's search query.
        Returns:
            NormalizedQuery: A structured representation of the normalized YouTube search query.
        Raises:
            RuntimeError: If the LLM response cannot be parsed or does not conform to the
                          expected schema.
    """
    resp = _get_openai_client().responses.create(
        model="gpt-5.2",
        input=_messages_to_openai_input(messages),
        # If you want stricter behavior, you can add:
        # temperature=0,
    )

    # Most reliable: treat model output as JSON string and validate locally.
    raw = resp.output_text.strip()
    data = json.loads(raw)

    # Construct the typed result (dataclass/pydantic/etc.)
    return NormalizedQuery(
        query=str(data["query"]),
        includes=list(data.get("includes", [])),
        excludes=list(data.get("excludes", [])),
        phrases=list(data.get("phrases", [])),
        channels=list(data.get("channels", [])),
        notes=str(data.get("notes", "")),
    )


def post_filter(
    results: list[dict[str, Any]],
    normalized: NormalizedQuery,
) -> list[dict[str, Any]]:
    """ Post-filter YouTube search results based on a normalized query.
        Args:
            results (list[dict[str, Any]]): The raw search results from YouTube.
            normalized (NormalizedQuery): The normalized query to filter results against.
        Returns:
            list[dict[str, Any]]: The filtered list of search results.
    """
    filtered: list[dict[str, Any]] = []

    for r in results:
        title = (r["title"] or "").lower()
        description = (r["description"] or "").lower()

        text = f"{title} {description}"

        # required terms
        if not all(term.lower() in text for term in normalized.includes):
            continue

        # excluded terms
        if any(term.lower() in text for term in normalized.excludes):
            continue

        # phrases
        if not all(phrase.lower() in text for phrase in normalized.phrases):
            continue

        # channel name check (if needed)
        if normalized.channels:
            if (r.get("channel_title") or "") not in normalized.channels:
                continue

        filtered.append(r)

    return filtered

if __name__ == "__main__":
    nq = normalize_youtube_query(
        'python list comprehension OR "lambda functions" -shorts channel:"Corey Schafer"'
    )
    print(nq.query)
    print(nq)
