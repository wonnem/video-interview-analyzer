import os
import tempfile
from app.audio import extract_audio
from app.stt import transcribe
from app.models import TranscribeResponse


def run_pipeline(video_path: str, applicant_id: str, question_id: str) -> TranscribeResponse:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name

    try:
        duration = extract_audio(video_path, wav_path)
        segments = transcribe(wav_path)
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)

    return TranscribeResponse(
        applicant_id=applicant_id,
        question_id=question_id,
        segments=segments,
        duration_seconds=round(duration, 2),
    )
