# ax-stt

> **AI 영어 면접 평가 플랫폼** — 지원자 답변 영상 STT 변환 및 본인 확인 API 서버

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![faster-whisper](https://img.shields.io/badge/STT-faster--whisper-412991)](https://github.com/SYSTRAN/faster-whisper)
[![DeepFace](https://img.shields.io/badge/Face-DeepFace-FF6F00)](https://github.com/serengil/deepface)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 개요

아산 AX Step 3 — 5조 AI 영어 면접 챗봇의 **백엔드 AI 전처리 파이프라인** 모듈입니다.

```
[지원자 답변 영상] → FFmpeg 음성 추출 → faster-whisper STT → JSON 반환
[이력서·신분증·웹캠] → OCR PII 마스킹 → DeepFace 얼굴 대조 → PASS/FAIL 반환
```

---

## 기능

### 1. STT 변환 (`POST /stt/transcribe`)

면접 응시 영상을 업로드하면 음성을 추출하고 텍스트로 변환합니다.

- **지원 포맷:** mp4, webm, mov, avi, mkv
- **음성 추출:** FFmpeg → 16kHz mono WAV
- **STT 엔진:** faster-whisper (로컬, API 키 불필요)
  - 모델: `base` / device: `cpu` / compute_type: `int8`
- **출력:** 타임스탬프 기반 세그먼트 JSON

```json
{
  "applicant_id": "user_123",
  "question_id": "q_01",
  "segments": [
    { "start": 0.0, "end": 4.2, "text": "In my last project..." },
    { "start": 4.2, "end": 9.8, "text": "two members disagreed on..." }
  ],
  "duration_seconds": 45.2
}
```

### 2. 본인 확인 (`POST /vision/verify`)

이력서 사진·신분증·웹캠 프레임 3장으로 동일인 여부를 판별합니다.

- **PII 마스킹:** EasyOCR로 주민등록번호 탐지 → 뒷자리 자동 블랙박스 처리
- **얼굴 대조:** DeepFace (모델: SFace, 검출기: opencv)
- **검증 기준:** 이력서↔신분증, 신분증↔웹캠 유사도 모두 0.5 이상 시 PASS
- **보안:** 원본 신분증 데이터는 처리 직후 메모리에서 즉시 파기

```json
{
  "applicant_id": "user_123",
  "verification_status": "PASS",
  "masked_id_url": "masked/masked_a1b2c3d4e5.jpg",
  "match_scores": {
    "resume_vs_id": 0.82,
    "id_vs_webcam": 0.79
  }
}
```

---

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/stt/transcribe` | 면접 영상 STT 변환 |
| `POST` | `/vision/verify` | 지원자 본인 확인 (얼굴 대조) |

Swagger UI: `http://127.0.0.1:8001/docs`

---

## 프로젝트 구조

```
ax-stt/
├── app/
│   ├── main.py                  # FastAPI 앱 진입점 (lifespan, 라우터 등록)
│   ├── models.py                # Pydantic 응답 모델
│   ├── api/
│   │   ├── routes_stt.py        # STT 라우터 (prefix: /stt)
│   │   └── routes_vision.py     # 본인확인 라우터 (prefix: /vision)
│   ├── services/
│   │   ├── stt_service.py       # FFmpeg 추출 + faster-whisper 변환
│   │   └── vision_service.py    # EasyOCR 마스킹 + DeepFace 대조
│   └── utils/
│       └── file_helper.py       # 임시 파일 저장/삭제
├── requirements.txt
├── .env.example
├── .pre-commit-config.yaml
└── .gitignore
```

---

## 설치 및 실행

### 사전 요구 사항

| 항목 | 버전 | 설치 |
|------|------|------|
| Python | 3.10 이상 | [python.org](https://www.python.org/downloads/) |
| FFmpeg | 최신 | `winget install FFmpeg` (Windows) / `brew install ffmpeg` (macOS) |

FFmpeg 설치 확인:

```bash
ffmpeg -version
```

> **Windows 주의:** FFmpeg 설치 후 터미널을 재시작해야 PATH가 반영됩니다.

### 환경 설정

```bash
# 저장소 클론
git clone https://github.com/kim-jeongwoo/AX-ai-english-interview-chatbot.git
cd AX-ai-english-interview-chatbot

# 가상환경 생성 및 활성화
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 의존성 설치

```bash
pip install -r requirements.txt
```

> **Windows 주의:** deepface / tensorflow 설치 시 파일 경로 길이 제한(260자) 오류가 발생할 수 있습니다.
> 관리자 PowerShell에서 아래 명령 실행 후 재설치하세요.
>
> ```powershell
> New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
>   -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
> ```

### Pre-commit 훅 설치

```bash
pip install pre-commit
pre-commit install
```

### 서버 실행

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

브라우저에서 `http://127.0.0.1:8001/docs` 접속 후 "Try it out"으로 테스트합니다.

---

## 보안 정책

- `.env` 파일은 절대 커밋하지 않습니다 (pre-commit 훅 자동 차단)
- `masked/` 디렉터리(마스킹된 신분증)는 서버 로컬에만 보관합니다
- 신분증 원본 이미지는 API 처리 직후 메모리에서 즉시 파기합니다
- 서버는 `127.0.0.1` 로컬에서만 접근 가능하며, 외부 공개 시 인증을 반드시 추가해야 합니다

---

## Troubleshooting

### FFmpeg를 찾을 수 없음

```bash
winget install FFmpeg   # Windows
brew install ffmpeg     # macOS
# 설치 후 터미널 재시작
```

### EasyOCR/DeepFace 실행 중 CP949 인코딩 오류 (Windows)

진행 표시줄(`█`)이 CP949 터미널에서 오류를 유발합니다. `vision_service.py`의 `_suppress_output()` 컨텍스트 매니저로 이미 처리되어 있습니다.

### Windows Long Path 오류 (pip install 실패)

위 설치 가이드의 LongPathsEnabled 레지스트리 설정을 적용하세요.

---

> 아산 AX Step 3 — 5조 | 2026
