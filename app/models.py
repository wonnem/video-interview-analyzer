from pydantic import BaseModel, Field


# ── STT 모델 ──────────────────────────────────────────────
class Segment(BaseModel):
    start: float = Field(description="세그먼트 시작 시간 (초)")
    end: float = Field(description="세그먼트 종료 시간 (초)")
    text: str = Field(description="해당 구간 인식 텍스트")


class TranscribeResponse(BaseModel):
    applicant_id: str = Field(description="지원자 고유 ID")
    question_id: str = Field(description="면접 질문 ID")
    segments: list[Segment] = Field(description="타임스탬프 기반 문장 세그먼트 목록")
    duration_seconds: float = Field(description="영상 재생 시간 (초, 소수점 둘째 자리)")


# ── 안면인식 / 본인확인 모델 ──────────────────────────────
class MatchScores(BaseModel):
    resume_vs_id: float = Field(description="이력서 사진 ↔ 신분증 얼굴 유사도 (0~1)")
    id_vs_webcam: float = Field(description="신분증 얼굴 ↔ 웹캠 유사도 (0~1)")


class VerificationResponse(BaseModel):
    applicant_id: str = Field(description="지원자 고유 ID")
    verification_status: str = Field(description="본인 확인 결과: PASS 또는 FAIL")
    masked_id_url: str = Field(description="마스킹된 신분증 저장 경로")
    match_scores: MatchScores = Field(description="얼굴 유사도 점수")
