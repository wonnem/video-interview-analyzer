from pydantic import BaseModel


class TranscribeResponse(BaseModel):
    applicant_id: str
    question_id: str
    transcript: str
    duration_seconds: float
