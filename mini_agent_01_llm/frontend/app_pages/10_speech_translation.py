import streamlit as st

from core.api_client import BackendAPIError, request_audio
from core.speech_translation_client import translate_speech


LANGUAGE_OPTIONS = {
    "자동 감지": "auto",
    "한국어": "ko",
    "영어": "en",
    "일본어": "ja",
    "중국어": "zh",
}

TARGET_LANGUAGE_OPTIONS = {
    "한국어": "ko",
    "영어": "en",
    "일본어": "ja",
    "중국어": "zh",
}

VOICE_OPTIONS = [
    "coral",
    "marin",
    "cedar",
    "alloy",
    "nova",
]


st.title("1-8. 음성 번역")
st.caption("음성을 텍스트로 변환하고 선택한 언어로 번역합니다.")

recorded_audio = st.audio_input("번역할 음성을 녹음하세요.")

col1, col2 = st.columns(2)

with col1:
    source_label = st.selectbox(
        "원본 언어",
        list(LANGUAGE_OPTIONS),
        index=0,
    )

with col2:
    target_label = st.selectbox(
        "번역 대상 언어",
        list(TARGET_LANGUAGE_OPTIONS),
        index=1,
    )

source_language = LANGUAGE_OPTIONS[source_label]
target_language = TARGET_LANGUAGE_OPTIONS[target_label]

same_language = (
    source_language != "auto"
    and source_language == target_language
)

if same_language:
    st.warning("원본 언어와 번역 대상 언어가 같습니다.")

translate_disabled = recorded_audio is None or same_language

if st.button(
    "음성 인식 및 번역",
    type="primary",
    disabled=translate_disabled,
):
    try:
        with st.spinner("음성을 인식하고 번역하고 있습니다."):
            result = translate_speech(
                filename=recorded_audio.name or "recording.wav",
                content=recorded_audio.getvalue(),
                content_type=recorded_audio.type or "audio/wav",
                source_language=source_language,
                target_language=target_language,
            )

        st.session_state["speech_translation"] = result
    except BackendAPIError as error:
        st.error(str(error))

result = st.session_state.get("speech_translation")

if result:
    st.subheader("음성 인식 결과")
    st.write(result["transcript"])

    st.subheader("번역 결과")
    st.write(result["translated_text"])

    voice = st.selectbox(
        "음성",
        VOICE_OPTIONS,
    )

    instructions = st.text_input(
        "말하기 방식",
        "번역된 언어로 또렷하고 자연스럽게 말하세요.",
    )

    if st.button("번역 음성 생성", type="primary"):
        try:
            with st.spinner("번역문을 음성으로 변환하고 있습니다."):
                audio = request_audio(
                    result["translated_text"],
                    voice,
                    instructions,
                )

            st.warning("아래 음성은 AI가 생성한 합성 음성입니다.")
            st.audio(audio, format="audio/mpeg")
        except BackendAPIError as error:
            st.error(str(error))

st.info(
    "음성 인식과 번역 결과에는 오류가 포함될 수 있으므로 "
    "중요한 내용은 원본과 비교하세요."
)
st.caption(
    "주민등록번호, 계좌번호, 비밀번호 등 민감한 개인정보는 녹음하지 마세요."
)