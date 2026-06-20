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
PASS_THRESHOLD = 0.5  # 유사도 이 값 이상이면 PASS

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


# ── 내부 유틸 ────────────────────────────────────────────────
def _bytes_to_bgr(data: bytes):
    np = _np()
    cv2 = _cv2()
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("이미지를 디코딩할 수 없습니다.")
    return img


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


# ── Step 3~4: 얼굴 유사도 계산 ──────────────────────────────
def _face_similarity(img1, img2) -> float:
    """DeepFace로 두 이미지 유사도 반환 (0~1, 높을수록 유사)."""
    from deepface import DeepFace

    with _suppress_output():
        result = DeepFace.verify(
            img1_path=img1,
            img2_path=img2,
            enforce_detection=False,
            silent=True,
        )
    distance = float(result.get("distance", 1.0))
    return round(max(0.0, min(1.0, 1.0 - distance)), 2)


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

    # Step 3~4: 얼굴 대조
    score_resume_id = _face_similarity(img_resume, img_id_masked)
    score_id_webcam = _face_similarity(img_id_masked, img_webcam)

    status = (
        "PASS"
        if score_resume_id >= PASS_THRESHOLD and score_id_webcam >= PASS_THRESHOLD
        else "FAIL"
    )

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