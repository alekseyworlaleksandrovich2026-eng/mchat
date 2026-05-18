"""Schemas for speech-to-text API."""

from pydantic import BaseModel, Field


class SpeechConfigResponse(BaseModel):
    enabled: bool
    provider: str = Field(
        description="Backend STT provider: openai, local, or none"
    )
    browser_fallback: bool = Field(
        default=True,
        description="Frontend may use Web Speech API when backend unavailable",
    )
    max_audio_mb: int = 10
    language: str = "zh"


class TranscribeResponse(BaseModel):
    text: str
    provider: str
