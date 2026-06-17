import os
import shutil
import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from dotenv import load_dotenv

from app.pipeline import run_pipeline
from app.models import TranscribeResponse

load_dotenv()

TEMP_DIR = "temp"


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(TEMP_DIR, exist_ok=True)
    yield
    shutil.rmtree(TEMP_DIR, ignore_errors=True)


app = FastAPI(lifespan=lifespan)

ALLOWED_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_video(
    video: UploadFile = File(...),
    applicant_id: str = Form(...),
    question_id: str = Form(...),
):
    ext = os.path.splitext(video.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

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
