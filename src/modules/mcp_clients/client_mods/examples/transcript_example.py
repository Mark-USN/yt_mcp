""" Example of how to use the MCP client to call a tool that retrieves YouTube video transcripts,
    and then cache those transcripts to disk.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Protocol
from pathlib import Path
from fastmcp import Client
from yt_lib.yt_types import extract_video_id
from yt_lib.utils.log_utils import get_logger
from yt_lib.utils.tree_view import TreeView, TreeViewConfig
from modules.mcp_clients.client_mods.output_sink import OutputSink, NullOutputSink


logger = get_logger(__name__)

class DocumentDirProvider(Protocol):
    """ Prototype to translate app_context methods into a simple protocol for this module,
        to avoid a hard dependency on the full app context. 
    """
    def document_dir(self) -> Path:
        """ Return the base directory where documents (like transcripts) should be stored.
            This is a simple protocol to abstract away the specifics of how the document
            directory is determined, allowing this module to be more easily integrated into
            different application contexts without requiring a full dependency on the app context.
        """

def _coerce_to_list(var:Any) -> list[Any]:
    """ Ensure the input is a list. If it's not already a list, wrap it in a list. """
    if isinstance(var,list):
        return var
    return [var]


class TranscriptExample:
    """ Example of how to use the MCP client to call a tool that retrieves YouTube video transcripts,
        and then cache those transcripts to disk.
    """
    mcp_client: Client
    tv: TreeView
    out_path: Path

    def __init__(self, mcp_client: Client, doc_dir_provider: DocumentDirProvider, emit: OutputSink = NullOutputSink()) -> None:
        """ Initialize the TranscriptExample with an MCP client a document directory provider
            and an output sink.
            Args:
                mcp_client: An instance of the MCP Client to use for calling tools.
                doc_dir_provider: An instance of DocumentDirProvider to provide the base directory
                                    for storing transcripts.
                emit: An instance of an OutputSink to handle output messages.
            Side Effects:
                Initializes a TreeView for rendering results and sets up the output path for transcripts.
        """
        self.mcp_client = mcp_client
        self.out_path = doc_dir_provider.document_dir() / "Transcripts"
        tv_cfg = TreeViewConfig()
        tv_cfg.collapse_keys={"env", "data"}
        tv_cfg.redact_keys={"token", "api_key"}

        self.tv = TreeView(tv_cfg)
        self.emit = emit or (lambda _message: None)


    async def run(self, video_urls: str | list[str]) -> None:
        """ Run the transcript retrieval and caching process for the given video URLs.
            Args:
                video_urls: A single video URL or a list of video URLs to process.
            Side Effects:
                For each video URL, retrieves the transcript using the MCP client, renders the
                result in a TreeView, and writes the transcript to a JSON file in the output
                directory. Also prints the time taken for each transcript retrieval.
        """
        self.emit("Executing youtube_json...")

        urls = _coerce_to_list(video_urls)
        self.emit("")
        self.emit(self.tv.render_tree(obj=urls, title="Processing the following video URLs:"))

        for url in urls:
            start = time.perf_counter()
            result = await self.mcp_client.call_tool("youtube_json", {"url_or_id": url})
            elapsed = time.perf_counter() - start
            self.emit(self.tv.render_tree(obj=result, title=f"youtube_json({url}):"))

            vid = extract_video_id(url)
            out = self.out_path / f"{vid}.json"
            payload = getattr(result, "content", result)
            # payload is:
            # [TextContent(type='text', text='[{"text":"..."}]', ...)]
            json_text = None
            if isinstance(payload, list) and payload:
                first = payload[0]
                # Extract embedded JSON string
                json_text = first.text
            if json_text:
                out.write_text(json_text, encoding="utf-8")
            else:
                out.write_text(str(payload), encoding="utf-8")
            self.emit(f"Transcript for {url} written to {out} (took {elapsed:.2f} seconds)")
            await asyncio.sleep(1)              # Sleep between calls to avoid overwhelming
                                                # the MCP server or hitting rate limits
