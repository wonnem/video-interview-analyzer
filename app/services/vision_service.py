import contextlib
import io
import os
import re
import uuid

# cv2, numpy는 요청 시점에 지연 로딩 (vision 패키지 미설치 시 STT 기능은 정상 동작)


@contextlib.contextmanager
def _suppress_output():
    """EasyOCR/DeepFace 진행 표시줄(█ 등)이 CP949 터미널에서 인코딩 오류를 일으키는 것을 방지."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        yield

MASKED_DIR = "masked"

_ocr_reader = None


def _cv2():
    import cv2
    return cv2


def _np():
    import numpy as np
    return np


def _get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is None:
        import easyocr
        with _suppress_output():
            _ocr_reader = easyocr.Reader(["ko", "en"], gpu=False)
    return _ocr_reader


MAX_WIDTH = 800  # DeepFace 추론 전 리사이징 상한 (정확도·속도 균형)


# ── 내부 유틸 ────────────────────────────────────────────────
def _bytes_to_bgr(data: bytes):
    np = _np()
    cv2 = _cv2()
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("이미지를 디코딩할 수 없습니다.")
    return img


def _resize_for_model(img):
    """가로 600px 초과 이미지를 비율 유지하며 축소 — 고해상도 입력 시 추론 속도 개선."""
    cv2 = _cv2()
    h, w = img.shape[:2]
    if w <= MAX_WIDTH:
        return img
    scale = MAX_WIDTH / w
    new_w, new_h = MAX_WIDTH, int(h * scale)
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


def _save_masked(img) -> str:
    cv2 = _cv2()
    os.makedirs(MASKED_DIR, exist_ok=True)
    filename = f"masked_{uuid.uuid4().hex[:10]}.jpg"
    path = os.path.join(MASKED_DIR, filename)
    cv2.imwrite(path, img)
    return path


# ── Step 2: 신분증 PII 마스킹 ───────────────────────────────
def mask_id_card(img):
    """EasyOCR로 주민등록번호 탐지 후 OpenCV로 뒷자리 마스킹."""
    np = _np()
    cv2 = _cv2()
    reader = _get_ocr_reader()
    pattern = re.compile(r"\d{6}-?\d{1,7}")

    with _suppress_output():
        results = reader.readtext(img)

    masked = img.copy()
    for (bbox, text, _conf) in results:
        cleaned = text.replace(" ", "")
        if not pattern.search(cleaned):
            continue

        pts = np.array(bbox, dtype=np.int32)
        x1, y1 = int(pts[:, 0].min()), int(pts[:, 1].min())
        x2, y2 = int(pts[:, 0].max()), int(pts[:, 1].max())

        # 전체 번호 영역의 오른쪽 절반(뒷자리)만 마스킹
        mid_x = x1 + (x2 - x1) // 2
        cv2.rectangle(masked, (mid_x, y1 - 2), (x2, y2 + 2), (0, 0, 0), -1)

    return masked


# ── Step 3~4: 얼굴 대조 ─────────────────────────────────────
def _face_verify(img1, img2) -> tuple:
    """DeepFace로 동일인 여부 판단 및 정규화 유사도 반환.

    - verified : DeepFace 모델 자체 임계값 기준 동일인 여부 (bool)
    - score    : distance/threshold 비율 역산 → 0~1 (1에 가까울수록 유사)

    model_name='SFace'      : 경량·고속 모델
    detector_backend='mtcnn': opencv 대비 정확한 얼굴 검출기
    """
    from deepface import DeepFace

    with _suppress_output():
        result = DeepFace.verify(
            img1_path=img1,
            img2_path=img2,
            model_name="SFace",
            detector_backend="mtcnn",
            enforce_detection=False,
            silent=True,
        )
    verified = bool(result.get("verified", False))
    distance = float(result.get("distance", 1.0))
    threshold = float(result.get("threshold", 0.593))
    score = round(max(0.0, min(1.0, 1.0 - distance / threshold)), 2) if threshold > 0 else 0.0
    return verified, score


# ── 메인 파이프라인 ──────────────────────────────────────────
def run_verification_pipeline(
    resume_bytes: bytes,
    id_card_bytes: bytes,
    webcam_bytes: bytes,
    applicant_id: str,
) -> dict:
    # Step 1: 이미지 디코딩 (메모리에만 올림)
    img_resume = _bytes_to_bgr(resume_bytes)
    img_id_card = _bytes_to_bgr(id_card_bytes)
    img_webcam = _bytes_to_bgr(webcam_bytes)

    # Step 2: 신분증 PII 마스킹 → 마스킹 이미지만 저장
    img_id_masked = mask_id_card(img_id_card)
    masked_id_path = _save_masked(img_id_masked)

    # Step 3~4: 얼굴 대조 (리사이징 후 추론)
    img_resume_s = _resize_for_model(img_resume)
    img_id_s = _resize_for_model(img_id_masked)
    img_webcam_s = _resize_for_model(img_webcam)
    verified_resume_id, score_resume_id = _face_verify(img_resume_s, img_id_s)
    verified_id_webcam, score_id_webcam = _face_verify(img_id_s, img_webcam_s)

    status = "PASS" if verified_resume_id and verified_id_webcam else "FAIL"

    result = {
        "applicant_id": applicant_id,
        "verification_status": status,
        "masked_id_url": masked_id_path,
        "match_scores": {
            "resume_vs_id": score_resume_id,
            "id_vs_webcam": score_id_webcam,
        },
    }

    # Step 5: 원본 민감 데이터 즉시 파기
    del img_id_card, id_card_bytes, resume_bytes, webcam_bytes

    return result