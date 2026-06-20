import shutil
import subprocess
import tempfile

from faster_whisper import WhisperModel

from app.models import TranscribeResponse
from app.utils.file_helper import TEMP_DIR, remove_file

_model: WhisperModel | None = None


def _ffmpeg() -> str:
    return shutil.which("ffmpeg") or r"C:\Users\wonst\ffmpeg\bin\ffmpeg.exe"


def _ffprobe() -> str:
    return shutil.which("ffprobe") or r"C:\Users\wonst\ffmpeg\bin\ffprobe.exe"


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        # 첫 실행 시 모델 파일 자동 다운로드 (~150MB)
        _model = WhisperModel("base", device="cpu", compute_type="int8")
    return _model


def _extract_audio(video_path: str, output_path: str) -> float:
    subprocess.run(
        [_ffmpeg(), "-y", "-i", video_path, "-ar", "16000", "-ac", "1", "-f", "wav", output_path],
        check=True, capture_output=True,
    )
    result = subprocess.run(
        [_ffprobe(), "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", video_path],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def _transcribe(audio_path: str) -> list[dict]:
    segments, _ = _get_model().transcribe(audio_path, language="en")
    return [
        {"start": round(seg.start, 2), "end": round(seg.end, 2), "text": seg.text.strip()}
        for seg in segments
    ]


def run_stt_pipeline(video_path: str, applicant_id: str, question_id: str) -> TranscribeResponse:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name
    try:
        duration = _extract_audio(video_path, wav_path)
        segments = _transcribe(wav_path)
    finally:
        remove_file(wav_path)
    return TranscribeResponse(
        applicant_id=applicant_id,
        question_id=question_id,
        segments=segments,
        duration_seconds=round(duration, 2),
    )