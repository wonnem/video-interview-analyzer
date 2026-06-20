from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes_stt import router as stt_router
from app.api.routes_vision import router as vision_router
from app.utils.file_helper import cleanup_temp_dir, ensure_temp_dir


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_temp_dir()
    yield
    cleanup_temp_dir()


app = FastAPI(
    lifespan=lifespan,
    title="AI 영어 면접 분석 파이프라인",
    description="면접 응시 영상의 STT 변환 및 안면인식 처리 API",
    version="2.0.0",
)

app.include_router(stt_router)
app.include_router(vision_router)
