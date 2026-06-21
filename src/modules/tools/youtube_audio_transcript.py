""" YouTube Audio Transcript Tool """

from __future__ import annotations

import json
# import asyncio
from typing import TypeVar
from dataclasses import asdict
from fastmcp import FastMCP  # pylint: disable=unused-import

from fastmcp.dependencies import Progress
from fastmcp.server.tasks import TaskConfig
from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from yt_lib.yt_types import Snippet
from yt_lib.yt_audio_transcript import transcribe_youtube_audio_async, AudioPaths, set_info
from yt_lib.audio.audio_types import AUDIO_SETTINGS
from yt_lib.utils.app_info import RuntimeInfo
from yt_lib.utils.log_utils import get_logger


T = TypeVar("T", bound="FastMCP")

# -----------------------------
# Logging setup
# -----------------------------
logger = get_logger(__name__)

async def youtube_audio_json(
    url: str,
    *,
    model_name: str = AUDIO_SETTINGS.whisper_model,
    progress: Progress = Progress(),
    mcp_info: Context = CurrentContext()
) -> str:
    """ ASYNC variant of the YouTube audio transcript tool that returns JSON.
        This function transcribes the audio of a YouTube video asynchronously and provides
        progress updates. The result is returned as a JSON string.
        Args:
            url: The URL of the YouTube video to transcribe.
            model_name: The name of the model to use for transcription.
            progress: A Progress object to report progress updates.
        Returns:
            A JSON string representing the transcript of the YouTube video's audio.
        Note:
            1. The progress argument is automatically provided by the MCP server when this
               function is registered as a tool, so it should not be passed manually when calling
               this function through the MCP interface.
            2. This function is asynchronous and can be cancelled while transcribing.
    """
    await mcp_info.info(f"Starting audio transcript for {url}")
    await progress.set_total(100)
    await progress.set_message("Starting YouTube audio transcription")

    snippets: list[Snippet] = await transcribe_youtube_audio_async(
        url=url,
        model_name=model_name,
        progress_rptr=progress,
    )

    await progress.set_message("Audio transcription tool complete")
    return json.dumps(
                    snippets,
                    ensure_ascii=False,
                    indent=2
                )


# ----------------- MCP integration -----------------

def register(mcp: T, info: RuntimeInfo ) -> None:
    """ Register YouTube to json and text audio tools with the MCP instance as a long job.
        This registers ASYNC variants so the job can be cancelled while transcribing.
        The sync versions remain available for CLI/testing.
        Args:
                mcp: The MCP instance to register the tools with.
                info: The runtime info to set for the transcription functions.
    """
    paths = AudioPaths(
        audio_dir=info.audio_dir,
    )

    set_info(paths)

    logger.debug("Registering YouTube audio transcript tools (async/cancellable)")
    mcp.tool(tags=["public", "api"], task=TaskConfig(mode="required"))(youtube_audio_json)
    # mcp.tool(tags=["public", "api"])(youtube_audio_text)

# ----------------- CLI -----------------


# def test() -> None:
#     """ CLI entry point to test the YouTube to text tool. """
#     import fastmcp, torch
#     from datetime import timedelta
#     print("\nfastmcp:", fastmcp.__version__)
#     print("torch:", torch.__version__)
#     print("CUDA available:", torch.cuda.is_available())
#     print("Device count:", torch.cuda.device_count())
#     print("Whisper models available:", whisper.available_models())

#     # CLI for testing the YouTube to text tool.
#     yt_url = "https://www.youtube.com/watch?v=DAYJZLERqe8"    # 6:32 comedy
#     # yt_url = "https://www.youtube.com/watch?v=_uQrJ0TkZlc"    # 6 + hours!
#     # yt_url = "https://www.youtube.com/watch?v=Ro_MScTDfU4"    # 30:34 Python tutorial < 30 Mins
#     # yt_url = "https://www.youtube.com/watch?v=gJz4lByMHUg"    # Just music
#     # yt_url = "https://youtu.be/N23vXA-ai5M?list=PLC37ED4C488778E7E&index=1"
#     # yt_url = "https://youtu.be/N23vXA-ai5M"
#     # yt_url = "https://www.youtube.com/watch?v=ulebPxBw8Uw"

#     while not yt_url:
#         yt_url = input("Enter YouTube URL: ").strip()
#         if not yt_url:
#             logger.warning("⚠️ Please paste a valid YouTube URL.")

#     ffmpeg_path = ensure_ffmpeg_on_path()
#     if not ffmpeg_path:
#         raise SystemExit(
#             "❌ FFmpeg is not available. Please install "
#             "FFmpeg and ensure it is on the system PATH."
#         )
#     logger.info("Using ffmpeg at %s", get_ffmpeg_binary_path())

#     start = time.perf_counter()
#     json_trans = youtube_audio_json(yt_url)
#     elapsed = time.perf_counter()-start
#     print("\n\n--- JSON AUDIO TRANSCRIPT ---\n")
#     print(f"{json_trans}")
#     print(f"\nTranscribed in {str(timedelta(seconds=elapsed))} seconds.\n")

#     start = time.perf_counter()
#     text_trans = youtube_audio_text(yt_url)
#     elapsed = time.perf_counter()-start
#     print("\n\n--- TEXT AUDIO TRANSCRIPT ---\n")
#     print(f"{text_trans}")
#     print(f"\nTranscribed in {str(timedelta(seconds=elapsed))} seconds.\n")
# if __name__ == "__main__":
#     test()
