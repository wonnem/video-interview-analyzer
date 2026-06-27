from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models import VerificationResponse
from app.services.vision_service import run_verification_pipeline

router = APIRouter(prefix="/vision", tags=["안면인식 / 본인확인"])

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


@router.post(
    "/verify",
    response_model=VerificationResponse,
    summary="지원자 본인 확인",
    description=(
        "이력서 사진, 신분증 사진, 웹캠 프레임을 비교하여 동일인 여부를 검증합니다.\n\n"
        "**처리 과정:**\n"
        "1. 신분증 주민등록번호 뒷자리 자동 마스킹 (OCR + OpenCV)\n"
        "2. 마스킹 신분증 이미지 임시 저장\n"
        "3. 이력서↔신분증, 신분증↔웹캠 얼굴 유사도 계산 (DeepFace)\n"
        "4. 원본 신분증 데이터 즉시 파기\n\n"
        "**지원 형식:** jpg, jpeg, png, webp"
    ),
)
async def verify_applicant(
    img_resume: UploadFile = File(..., description="이력서 증명사진"),
    img_id_card: UploadFile = File(..., description="신분증 원본 사진"),
    img_webcam: UploadFile = File(..., description="실시간 웹캠 프레임"),
    applicant_id: str = Form(..., description="지원자 고유 ID (예: user_123)"),
):
    for upload in (img_resume, img_id_card, img_webcam):
        ext = "." + (upload.filename or "").rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_IMAGE_EXTS:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 이미지 형식입니다: {ext}",
            )

    try:
        result = run_verification_pipeline(
            resume_bytes=await img_resume.read(),
            id_card_bytes=await img_id_card.read(),
            webcam_bytes=await img_webcam.read(),
            applicant_id=applicant_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return result