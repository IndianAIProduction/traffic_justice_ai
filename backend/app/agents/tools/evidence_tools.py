"""
Tools available to the Evidence Agent for transcription and analysis.
"""
from langchain_core.tools import tool
from openai import OpenAI

from app.config import settings


@tool
def transcribe_audio(file_path: str) -> str:
    """Transcribe an audio or video file using OpenAI Whisper.

    Args:
        file_path: Path to the audio/video file on disk.
    """
    client = OpenAI(api_key=settings.openai_api_key)
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text",
        )
    return transcript
