import os
import shutil
import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from app.pipeline import run_pipeline
from app.models import TranscribeResponse

TEMP_DIR = "temp"


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(TEMP_DIR, exist_ok=True)
    yield
    shutil.rmtree(TEMP_DIR, ignore_errors=True)


app = FastAPI(
    lifespan=lifespan,
    title="AI 영어 면접 STT 파이프라인",
    description=(
        "지원자의 면접 응시 영상에서 음성을 추출하고, "
        "Whisper 모델을 통해 텍스트로 변환하는 STT 파이프라인 API입니다."
    ),
    version="1.0.0",
)

ALLOWED_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}


@app.post(
    "/transcribe",
    response_model=TranscribeResponse,
    summary="영상 파일 음성 텍스트 변환",
    description=(
        "면접 응시 영상 파일을 업로드하면 음성을 추출하고 텍스트로 변환합니다.\n\n"
        "**지원 형식:** mp4, webm, mov, avi, mkv\n\n"
        "**처리 과정:** 영상 업로드 → 16kHz 오디오 추출 → Whisper STT 변환 → JSON 응답"
    ),
    tags=["STT 변환"],
)
async def transcribe_video(
    video: UploadFile = File(..., description="면접 응시 영상 파일 (mp4, webm, mov, avi, mkv)"),
    applicant_id: str = Form(..., description="지원자 고유 ID (예: user_123)"),
    question_id: str = Form(..., description="면접 질문 ID (예: q_01)"),
):
    ext = os.path.splitext(video.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 형식입니다: {ext}")

    tmp_video = tempfile.NamedTemporaryFile(
        dir=TEMP_DIR, suffix=ext, delete=False
    )
    try:
        contents = await video.read()
        tmp_video.write(contents)
        tmp_video.close()

        try:
            result = run_pipeline(tmp_video.name, applicant_id, question_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_video.name):
            os.remove(tmp_video.name)

    return result
