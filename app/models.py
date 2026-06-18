from pydantic import BaseModel, Field


class Segment(BaseModel):
    start: float = Field(description="세그먼트 시작 시간 (초)")
    end: float = Field(description="세그먼트 종료 시간 (초)")
    text: str = Field(description="해당 구간 인식 텍스트")


class TranscribeResponse(BaseModel):
    applicant_id: str = Field(description="지원자 고유 ID")
    question_id: str = Field(description="면접 질문 ID")
    segments: list[Segment] = Field(description="타임스탬프 기반 문장 세그먼트 목록")
    duration_seconds: float = Field(description="영상 재생 시간 (초, 소수점 둘째 자리)")
