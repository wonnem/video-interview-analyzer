# 안면인식 / 마스킹 API 엔드포인트
# TODO: vision_service 구현 후 엔드포인트 추가 예정

from fastapi import APIRouter

router = APIRouter(prefix="/vision", tags=["안면인식"])