"""Speech-to-text API (admin chat)."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.speech import SpeechConfigResponse, TranscribeResponse
from app.services.stt_service import STTError, STTService

router = APIRouter()


@router.get("/config", response_model=SpeechConfigResponse)
async def speech_config(
    _current_user: User = Depends(get_current_user),
) -> SpeechConfigResponse:
    """Return STT capabilities for the chat UI."""
    return SpeechConfigResponse(**STTService().get_public_config())


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    _current_user: User = Depends(get_current_user),
) -> TranscribeResponse:
    """Upload audio and return transcribed text."""
    data = await file.read()
    try:
        text, provider = await STTService().transcribe(
            data,
            filename=file.filename or "audio.webm",
            content_type=file.content_type,
        )
    except STTError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"语音识别失败: {e}",
        ) from e

    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未识别到语音内容，请重试",
        )
    return TranscribeResponse(text=text, provider=provider)
