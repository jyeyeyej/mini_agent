import httpx

from core.api_client import BACKEND_URL, BackendAPIError, REQUEST_TIMEOUT


def translate_speech(
    filename: str,
    content: bytes,
    content_type: str,
    source_language: str,
    target_language: str,
) -> dict:
    try:
        response = httpx.post(
            f"{BACKEND_URL}/api/media/speech-translation",
            files={
                "audio": (
                    filename,
                    content,
                    content_type,
                )
            },
            data={
                "source_language": source_language,
                "target_language": target_language,
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as error:
        try:
            detail = error.response.json().get(
                "detail",
                str(error),
            )
        except ValueError:
            detail = str(error)

        raise BackendAPIError(detail) from error
    except httpx.TimeoutException as error:
        raise BackendAPIError(
            "음성 인식 및 번역 응답 시간이 초과되었습니다."
        ) from error
    except httpx.RequestError as error:
        raise BackendAPIError(
            "백엔드 서버에 연결할 수 없습니다."
        ) from error