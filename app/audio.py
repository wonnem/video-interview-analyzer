import shutil
import subprocess


def _ffmpeg() -> str:
    return shutil.which("ffmpeg") or r"C:\Users\wonst\ffmpeg\bin\ffmpeg.exe"


def _ffprobe() -> str:
    return shutil.which("ffprobe") or r"C:\Users\wonst\ffmpeg\bin\ffprobe.exe"


def extract_audio(video_path: str, output_path: str) -> float:
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
