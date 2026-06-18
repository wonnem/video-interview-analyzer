from pydantic import BaseModel, Field


class TranscribeResponse(BaseModel):
    applicant_id: str = Field(description="지원자 고유 ID")
    question_id: str = Field(description="면접 질문 ID")
    transcript: str = Field(description="음성 인식 결과 텍스트")
    duration_seconds: float = Field(description="영상 재생 시간 (초)")
