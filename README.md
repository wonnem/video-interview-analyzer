# AX-ai-english-interview-chatbot

> 아산 AX Step 3 — 5조 AI 영어 면접 챗봇 시스템

---

## 모듈 구성

| 모듈 | 경로 | 설명 |
|------|------|------|
| ax-stt | `app/` | 지원자 답변 STT 변환 + 본인 확인 API |
| ax-tts | `ax-tts` | TTS 모듈 |

---

## ax-stt — STT 변환 및 본인 확인 API

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![faster-whisper](https://img.shields.io/badge/STT-faster--whisper-412991)](https://github.com/SYSTRAN/faster-whisper)
[![DeepFace](https://img.shields.io/badge/Face-DeepFace-FF6F00)](https://github.com/serengil/deepface)

### 기능

#### 1. STT 변환 (`POST /stt/transcribe`)

면접 응시 영상을 업로드하면 음성을 추출하고 텍스트로 변환합니다.

- **지원 포맷:** mp4, webm, mov, avi, mkv
- **음성 추출:** FFmpeg → 16kHz mono WAV
- **STT 엔진:** faster-whisper (로컬, API 키 불필요)
- **출력:** 타임스탬프 기반 세그먼트 JSON

```json
{
  "applicant_id": "user_123",
  "question_id": "q_01",
  "segments": [
    { "start": 0.0, "end": 4.2, "text": "In my last project..." }
  ],
  "duration_seconds": 45.2
}
```

#### 2. 본인 확인 (`POST /vision/verify`)

이력서 사진·신분증·웹캠 프레임 3장으로 동일인 여부를 판별합니다.

- **PII 마스킹:** EasyOCR로 주민등록번호 탐지 → 뒷자리 자동 블랙박스 처리
- **얼굴 대조:** DeepFace (모델: SFace, 검출기: opencv)
- **검증 기준:** 이력서↔신분증, 신분증↔웹캠 유사도 모두 0.5 이상 시 PASS

```json
{
  "applicant_id": "user_123",
  "verification_status": "PASS",
  "masked_id_url": "masked/masked_a1b2c3.jpg",
  "match_scores": {
    "resume_vs_id": 0.82,
    "id_vs_webcam": 0.79
  }
}
```

### 프로젝트 구조

```
app/
├── main.py                  # FastAPI 앱 진입점
├── models.py                # Pydantic 응답 모델
├── api/
│   ├── routes_stt.py        # /stt/transcribe 라우터
│   └── routes_vision.py     # /vision/verify 라우터
├── services/
│   ├── stt_service.py       # FFmpeg + faster-whisper
│   └── vision_service.py    # EasyOCR 마스킹 + DeepFace
└── utils/
    └── file_helper.py
```

### 설치 및 실행

**사전 요구사항:** Python 3.10+, FFmpeg

```bash
# 가상환경
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # macOS/Linux

# 의존성
pip install -r requirements.txt

# 서버 실행
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

Swagger UI: `http://127.0.0.1:8001/docs`

> **Windows 주의:** deepface 설치 시 Long Path 오류가 발생하면 관리자 PowerShell에서 실행하세요.
> ```powershell
> New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
> ```

### 보안 정책

- `.env` 파일 커밋 금지 (pre-commit 훅 자동 차단)
- `masked/` 디렉터리는 서버 로컬에만 보관
- 신분증 원본은 API 처리 직후 메모리에서 즉시 파기
- 서버는 `127.0.0.1` 로컬 전용, 외부 공개 시 인증 필수

---

> 아산 AX Step 3 — 5조 | 2026
