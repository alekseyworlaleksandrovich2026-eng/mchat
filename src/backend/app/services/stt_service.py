"""Speech-to-text service — OpenAI Whisper API or optional local faster-whisper."""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any

from loguru import logger

from app.core.config import settings

_ALLOWED_EXTENSIONS = frozenset(
    {".webm", ".ogg", ".mp3", ".mp4", ".m4a", ".wav", ".mpeg", ".mpga"}
)
_ALLOWED_MIME_PREFIXES = ("audio/", "video/webm", "application/octet-stream")


class STTError(Exception):
    """STT configuration or transcription failure."""


class STTService:
    """Transcribe uploaded audio to text."""

    def get_public_config(self) -> dict[str, Any]:
        provider = (settings.stt_provider or "none").strip().lower()
        enabled = settings.stt_enabled and provider in ("openai", "local")
        if provider == "openai" and not self._openai_api_key():
            enabled = False
        if provider == "local":
            try:
                import faster_whisper  # noqa: F401
            except ImportError:
                enabled = False
        return {
            "enabled": enabled,
            "provider": provider if enabled else "none",
            "browser_fallback": True,
            "max_audio_mb": settings.stt_max_audio_mb,
            "language": settings.stt_language or "zh",
        }

    async def transcribe(
        self,
        data: bytes,
        *,
        filename: str = "audio.webm",
        content_type: str | None = None,
    ) -> tuple[str, str]:
        if not settings.stt_enabled:
            raise STTError("语音识别未启用")
        if not data:
            raise STTError("音频为空")
        max_bytes = settings.stt_max_audio_mb * 1024 * 1024
        if len(data) > max_bytes:
            raise STTError(
                f"音频过大，请控制在 {settings.stt_max_audio_mb}MB 以内"
            )

        ext = Path(filename or "audio.webm").suffix.lower()
        if ext and ext not in _ALLOWED_EXTENSIONS:
            raise STTError(f"不支持的音频格式: {ext}")
        if content_type and not any(
            content_type.startswith(p) for p in _ALLOWED_MIME_PREFIXES
        ):
            raise STTError(f"不支持的 Content-Type: {content_type}")

        provider = (settings.stt_provider or "openai").strip().lower()
        if provider == "openai":
            text = await self._transcribe_openai(data, filename)
            return text.strip(), "openai"
        if provider == "local":
            text = await asyncio.to_thread(
                self._transcribe_local_sync, data, filename
            )
            return text.strip(), "local"
        raise STTError(f"未知的 STT 提供商: {provider}")

    def _openai_api_key(self) -> str:
        return (
            (settings.stt_openai_api_key or "").strip()
            or os.environ.get("OPENAI_API_KEY", "").strip()
        )

    async def _transcribe_openai(self, data: bytes, filename: str) -> str:
        api_key = self._openai_api_key()
        if not api_key:
            raise STTError(
                "未配置 OpenAI API Key。请在 .env 设置 STT_OPENAI_API_KEY 或 OPENAI_API_KEY"
            )

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key)
        suffix = Path(filename).suffix or ".webm"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        try:
            lang = (settings.stt_language or "").strip() or None
            with open(tmp_path, "rb") as audio_file:
                kwargs: dict[str, Any] = {
                    "model": settings.stt_model or "whisper-1",
                    "file": audio_file,
                }
                if lang:
                    kwargs["language"] = lang
                result = await client.audio.transcriptions.create(**kwargs)
            return getattr(result, "text", None) or str(result)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _transcribe_local_sync(self, data: bytes, filename: str) -> str:
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise STTError(
                "本地语音识别需要安装 faster-whisper：pip install faster-whisper"
            ) from e

        suffix = Path(filename).suffix or ".webm"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        try:
            model_name = settings.stt_local_model or "base"
            logger.info(f"STT local transcribe with model={model_name}")
            model = WhisperModel(model_name, device="cpu", compute_type="int8")
            lang = (settings.stt_language or "zh").strip() or None
            segments, _info = model.transcribe(
                tmp_path,
                language=lang,
                beam_size=5,
            )
            return "".join(seg.text for seg in segments).strip()
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
