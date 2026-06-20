import os

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models import TranscribeResponse
from app.services.stt_service import run_stt_pipeline
from app.utils.file_helper import remove_file, save_upload

router = APIRouter(prefix="/stt", tags=["STT 변환"])

ALLOWED_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}


@router.post(
    "/transcribe",
    response_model=TranscribeResponse,
    summary="영상 파일 음성 텍스트 변환",
    description=(
        "면접 응시 영상 파일을 업로드하면 음성을 추출하고 텍스트로 변환합니다.\n\n"
        "**지원 형식:** mp4, webm, mov, avi, mkv\n\n"
        "**처리 과정:** 영상 업로드 → 16kHz 오디오 추출 → Whisper STT 변환 → JSON 응답"
    ),
)
async def transcribe_video(
    video: UploadFile = File(..., description="면접 응시 영상 파일 (mp4, webm, mov, avi, mkv)"),
    applicant_id: str = Form(..., description="지원자 고유 ID (예: user_123)"),
    question_id: str = Form(..., description="면접 질문 ID (예: q_01)"),
):
    ext = os.path.splitext(video.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 형식입니다: {ext}")

    contents = await video.read()
    tmp_path = save_upload(contents, ext)
    try:
        result = run_stt_pipeline(tmp_path, applicant_id, question_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        remove_file(tmp_path)
    return result