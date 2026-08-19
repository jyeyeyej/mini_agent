from io import BytesIO
from time import perf_counter
from typing import Literal

from openai import OpenAI

from app.config import settings
from app.schemas import SpeechTranslationResult


LanguageCode = Literal["auto", "ko", "en", "ja", "zh"]

ALLOWED_AUDIO_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/webm",
    "audio/mpeg",
    "audio/mp4",
    "audio/ogg",
}

LANGUAGE_NAMES = {
    "ko": "한국어",
    "en": "영어",
    "ja": "일본어",
    "zh": "중국어",
}


def validate_audio(content_type: str, content: bytes) -> None:
    if content_type not in ALLOWED_AUDIO_TYPES:
        raise ValueError(
            "WAV, WEBM, MP3, M4A, OGG 음성만 업로드할 수 있습니다."
        )

    if not content:
        raise ValueError("빈 음성 파일은 처리할 수 없습니다.")

    max_size = settings.max_audio_size_mb * 1024 * 1024

    if len(content) > max_size:
        raise ValueError(
            f"음성 파일은 {settings.max_audio_size_mb}MB 이하여야 합니다."
        )


def _transcribe_audio(
    client: OpenAI,
    filename: str,
    content_type: str,
    content: bytes,
    source_language: LanguageCode,
) -> str:
    audio_file = BytesIO(content)
    audio_file.name = filename

    request: dict = {
        "model": settings.openai_stt_model,
        "file": (filename, audio_file, content_type),
    }

    if source_language != "auto":
        request["language"] = source_language

    response = client.audio.transcriptions.create(**request)
    transcript = (response.text or "").strip()

    if not transcript:
        raise RuntimeError("음성에서 텍스트를 인식하지 못했습니다.")

    return transcript


def _translate_text(
    client: OpenAI,
    transcript: str,
    target_language: LanguageCode,
) -> str:
    target_name = LANGUAGE_NAMES[target_language]

    response = client.responses.create(
        model=settings.openai_translation_model,
        instructions=(
            f"입력된 문장을 {target_name}로 정확하고 자연스럽게 번역하세요. "
            "설명, 따옴표, 머리말을 추가하지 말고 번역문만 출력하세요."
        ),
        input=transcript,
    )

    translated_text = response.output_text.strip()

    if not translated_text:
        raise RuntimeError("번역 결과를 생성하지 못했습니다.")

    return translated_text


def transcribe_and_translate(
    filename: str,
    content_type: str,
    content: bytes,
    source_language: LanguageCode,
    target_language: LanguageCode,
) -> SpeechTranslationResult:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")

    if source_language not in {"auto", "ko", "en", "ja", "zh"}:
        raise ValueError("지원하지 않는 원본 언어입니다.")

    if target_language not in {"ko", "en", "ja", "zh"}:
        raise ValueError("지원하지 않는 번역 대상 언어입니다.")

    if source_language != "auto" and source_language == target_language:
        raise ValueError("원본 언어와 번역 대상 언어가 같습니다.")

    validate_audio(content_type, content)

    client = OpenAI(api_key=settings.openai_api_key)

    transcript = _transcribe_audio(
        client,
        filename,
        content_type,
        content,
        source_language,
    )

    translated_text = _translate_text(
        client,
        transcript,
        target_language,
    )

    return SpeechTranslationResult(
        source_language=source_language,
        target_language=target_language,
        transcript=transcript,
        translated_text=translated_text,
    )