from fastapi.testclient import TestClient

from app.main import app
from app.schemas import SpeechTranslationResult


client = TestClient(app)


def test_speech_translation_returns_text(monkeypatch) -> None:
    def mock_translate(*args, **kwargs) -> SpeechTranslationResult:
        return SpeechTranslationResult(
            source_language="ko",
            target_language="en",
            transcript="부산역으로 가는 방법을 알려주세요.",
            translated_text=(
                "Please tell me how to get to Busan Station."
            ),
        )

    monkeypatch.setattr(
        "app.routers.speech_translation_router."
        "transcribe_and_translate",
        mock_translate,
    )

    response = client.post(
        "/api/media/speech-translation",
        files={
            "audio": (
                "recording.wav",
                b"fake-audio",
                "audio/wav",
            )
        },
        data={
            "source_language": "ko",
            "target_language": "en",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["source_language"] == "ko"
    assert body["target_language"] == "en"
    assert body["transcript"] == (
        "부산역으로 가는 방법을 알려주세요."
    )
    assert body["translated_text"] == (
        "Please tell me how to get to Busan Station."
    )


def test_speech_translation_returns_422_for_input_error(
    monkeypatch,
) -> None:
    def mock_translate(*args, **kwargs):
        raise ValueError("지원하지 않는 음성 형식입니다.")

    monkeypatch.setattr(
        "app.routers.speech_translation_router."
        "transcribe_and_translate",
        mock_translate,
    )

    response = client.post(
        "/api/media/speech-translation",
        files={
            "audio": (
                "recording.txt",
                b"invalid",
                "text/plain",
            )
        },
        data={
            "source_language": "ko",
            "target_language": "en",
        },
    )

    assert response.status_code == 422
    assert "지원하지 않는 음성 형식" in response.json()["detail"]


def test_speech_translation_returns_502_for_provider_error(
    monkeypatch,
) -> None:
    def mock_translate(*args, **kwargs):
        raise RuntimeError("Provider 연결 실패")

    monkeypatch.setattr(
        "app.routers.speech_translation_router."
        "transcribe_and_translate",
        mock_translate,
    )

    response = client.post(
        "/api/media/speech-translation",
        files={
            "audio": (
                "recording.wav",
                b"fake-audio",
                "audio/wav",
            )
        },
        data={
            "source_language": "ko",
            "target_language": "en",
        },
    )

    assert response.status_code == 502
    assert "음성 인식 또는 번역에 실패" in response.json()["detail"]