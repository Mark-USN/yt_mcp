
""" Example of using the MCP client to call a tool that retrieves the audio from a YouTube video
    and transcribe the audio into text.
"""

from __future__ import annotations

import asyncio
import time
from typing import Protocol
from pathlib import Path
from fastmcp import Client
from yt_lib.yt_types import extract_video_id
from yt_lib.utils.log_utils import get_logger
from yt_lib.utils.tree_view import TreeView, TreeViewConfig
from modules.mcp_clients.client_mods.output_sink import OutputSink, NullOutputSink


logger = get_logger(__name__)

# pylint: disable=too-few-public-methods
class DocumentDirProvider(Protocol):
    """ Prototype to translate app_info methods into a simple protocol for this module,
        to avoid a hard dependency on the full app info. 
    """
    @property
    def document_dir(self) -> Path:
        """ Directory and file name to 'cache' transcripts for a given video ID.
            Args:
                video_id: The YouTube video ID for which to provide a transcript cache path.
            Returns:
                A Path object representing the file path where the transcript for the given video
                ID should be cached.
        """

# pylint: disable=too-few-public-methods
class AudioTranscriptExample:
    """ Example of how to use the MCP client to call a tool that retrieves the audio from a YouTube
        video and transcribes it into text.
    """
    mcp_client: Client
    tv: TreeView
    out_path: Path

    def __init__(
                    self,
                    mcp_client: Client,
                    doc_dir_provider: DocumentDirProvider,
                    emit: OutputSink = NullOutputSink()
                ) -> None:
        """ Initialize the AudioTranscriptExample with an MCP client and a document directory
            provider.
            Args:
                mcp_client: An instance of the MCP Client to use for calling tools and getting
                            prompts.
                doc_dir_provider: An instance of a DocumentDirProvider to provide the directory for
                                  caching transcripts.
                emit: An instance of an OutputSink to handle output messages.
            Side Effects:
                Initializes a TreeView for rendering results and sets up the
                ~/Documents/transcripts output path for transcripts.
        """
        self.mcp_client = mcp_client
        self.out_path = doc_dir_provider.documents_dir / "transcripts"
        self.out_path.mkdir(parents=True, exist_ok=True)
        self.emit = emit or (lambda _message: None)

        tv_cfg = TreeViewConfig()
        tv_cfg.collapse_keys={"env", "data"}
        tv_cfg.redact_keys={"token", "api_key"}

        self.tv = TreeView(tv_cfg)


    async def run(self, video_url: str) -> None:
        """ Run the example of retrieving and transcribing audio from a YouTube video.
            Args:
                video_url: The URL of the YouTube video to process.
            Side Effects:
               Stores the transcript of the video's audio to a JSON file in the output
               directory, and renders the result using the TreeView.
        """
        self.emit("Executing youtube_audio_json transcription...")

        start = time.perf_counter()
        async with self.mcp_client:
            task = await self.mcp_client.call_tool(
                                            "youtube_audio_json", 
                                            {
                                                "url": video_url,
                                                "model_name": "small"
                                            },
                                            task=True
                                        )
            self.emit(f"Started task: {task.task_id}")

            # def on_status_change(status) -> None:
            #     print(f"{status.status}: {status.statusMessage}")

            # task.on_status_change(on_status_change)
            while True:
                status = await task.status()
                self.emit(f"{status.status}: {status.statusMessage}")

                if status.status in {"completed", "failed", "cancelled"}:
                    break

                await asyncio.sleep(2)

            result = await task.result()
        elapsed = time.perf_counter() - start
        self.emit("")
        self.emit(self.tv.render_tree(obj=result, title=f"youtube_audio_json({video_url}):"))
        self.emit(f"Normalized YouTube query completed in {elapsed:.2f} seconds.")

        vid = extract_video_id(video_url)
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
            self.emit(self.tv.render_tree(
                                            obj=json_text,
                                            title=f"Extracted JSON text for {video_url}:")
                                        )
        else:
            out.write_text(str(payload), encoding="utf-8")
            self.emit(self.tv.render_tree(
                                            obj=str(payload),
                                            title=f"Payload for {video_url} (not JSON text):")
                                        )
        self.emit(f"Audio transcript for {video_url} written to {out} (took {elapsed:.2f} seconds)")
