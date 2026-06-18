from faster_whisper import WhisperModel

_model: WhisperModel | None = None

_INITIAL_PROMPT = (
    "Hello, welcome to the interview. "
    "This is a clear English sentence with proper punctuation."
)


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        # 첫 실행 시 모델 파일 자동 다운로드 (~150MB)
        _model = WhisperModel("base", device="cpu", compute_type="int8")
    return _model


def transcribe(audio_path: str) -> list[dict]:
    segments, _ = _get_model().transcribe(
        audio_path,
        language="en",
        initial_prompt=_INITIAL_PROMPT,
    )
    return [
        {"start": round(seg.start, 2), "end": round(seg.end, 2), "text": seg.text.strip()}
        for seg in segments
    ]
