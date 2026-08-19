from typing import Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas import SpeechTranslationResult
from app.services.speech_translation_service import transcribe_and_translate


speech_translation_router = APIRouter(
    prefix="/api/media",
    tags=["Multimodal"],
)


@speech_translation_router.post(
    "/speech-translation",
    response_model=SpeechTranslationResult,
)
async def speech_translation(
    audio: UploadFile = File(...),
    source_language: Literal["auto", "ko", "en", "ja", "zh"] = Form("auto"),
    target_language: Literal["ko", "en", "ja", "zh"] = Form("en"),
) -> SpeechTranslationResult:
    try:
        content = await audio.read()

        return transcribe_and_translate(
            filename=audio.filename or "recording.wav",
            content_type=audio.content_type or "",
            content=content,
            source_language=source_language,
            target_language=target_language,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"음성 인식 또는 번역에 실패했습니다: {error}",
        ) from error