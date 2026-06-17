# 🎤 ax-stt

> **AI 영어 면접 평가 플랫폼**의 핵심 데이터 전처리 파이프라인 — 지원자 답변 영상을 받아 **음성 추출 → 텍스트 변환(STT)** 결과를 JSON으로 반환합니다.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Whisper](https://img.shields.io/badge/STT-OpenAI%20Whisper-412991?logo=openai&logoColor=white)](https://platform.openai.com/docs/guides/speech-to-text)
[![FFmpeg](https://img.shields.io/badge/Audio-FFmpeg-007808?logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Hero

**ax-stt**는 AI 영어 면접 챗봇 시스템의 STT(Speech-To-Text) 파이프라인 모듈입니다.  
지원자가 영상으로 제출한 영어 면접 답변을 자동으로 텍스트로 전환하여, 후속 **CEFR 기반 영어 평가 엔진**과 **면접관 화면(프론트엔드)**에 전달합니다.

```
지원자 답변 영상 → 음성 추출 → Whisper STT → JSON 텍스트 출력
```

아산 AX 프로그램 Step 3 — 5조 공동 프로젝트 (2-week MVP Sprint)

---

## Demo

### 입력

```bash
python pipeline.py --input answer_01.mp4 --applicant user_123 --question q_01
```

### 출력 (JSON)

```json
{
  "applicant_id": "user_123",
  "question_id": "q_01",
  "transcript": "In my last project, two members disagreed on the design direction. I scheduled a brief sync and helped both sides articulate their core concerns...",
  "duration_seconds": 45.2
}
```

### 처리 흐름 예시

| 단계 | 입력 | 출력 |
|------|------|------|
| 1. 영상 수신 | `answer_01.mp4` | (원본 영상) |
| 2. 음성 추출 | `answer_01.mp4` | `answer_01.wav` (16kHz) |
| 3. STT 변환 | `answer_01.wav` | 텍스트 + 타임스탬프 |
| 4. JSON 패키징 | 텍스트 메타데이터 | `result.json` |

---

## Features

- **고정밀 영어 STT** — OpenAI Whisper는 다양한 억양과 발음에서도 문맥 기반 고정밀 변환을 제공하며, CEFR 평가에 최적화된 텍스트를 생성합니다.
- **다중 영상 포맷 지원** — FFmpeg 기반으로 `.mp4`, `.webm`, `.mov` 등 주요 영상 포맷을 모두 처리합니다.
- **16kHz 표준 오디오 추출** — STT 모델에 최적화된 샘플레이트로 자동 변환합니다.
- **내장 노이즈 필터링** — Whisper의 자체 노이즈 캔슬링으로 면접 환경의 배경 소음을 처리합니다.
- **타임스탬프 포함 출력** — 발화 구간별 타임스탬프를 JSON에 포함해 평가 엔진에서 구간 분석이 가능합니다.
- **로컬/클라우드 선택 가능** — 비용·보안 요구에 따라 `openai` API 또는 로컬 `faster-whisper`로 전환할 수 있습니다.
- **보안 가드레일** — pre-commit 훅으로 API 키·개인키 커밋 차단, 대용량 파일 업로드 방지를 자동 적용합니다.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     ax-stt Pipeline                     │
│                                                         │
│  [Client / Interview Platform]                          │
│         │  answer_XX.mp4                                │
│         ▼                                               │
│  ┌─────────────────┐                                    │
│  │  Audio Extractor │  FFmpeg (via moviepy / pydub)     │
│  │  video → .wav   │  출력: 16kHz mono WAV              │
│  └────────┬────────┘                                    │
│           │  answer_XX.wav                              │
│           ▼                                             │
│  ┌─────────────────┐                                    │
│  │  STT Engine     │  OpenAI Whisper API                │
│  │  audio → text   │  (대안: faster-whisper, 로컬)      │
│  └────────┬────────┘                                    │
│           │  transcript + timestamps                    │
│           ▼                                             │
│  ┌─────────────────┐                                    │
│  │  JSON Packager  │  applicant_id / question_id 바인딩 │
│  └────────┬────────┘                                    │
│           │                                             │
│    ┌──────┴──────┐                                      │
│    ▼             ▼                                      │
│ [평가 엔진]   [프론트엔드]                               │
│  CEFR 분석    면접관 화면                                │
└─────────────────────────────────────────────────────────┘
```

### 컴포넌트 역할

| 컴포넌트 | 기술 | 역할 |
|----------|------|------|
| Audio Extractor | FFmpeg + `moviepy` / `pydub` | 영상에서 오디오 트랙 분리, 16kHz WAV 저장 |
| STT Engine | OpenAI Whisper API | 오디오 → 텍스트 + 타임스탬프 변환 |
| JSON Packager | Python `json` | 결과 직렬화 및 메타데이터 바인딩 |

### 디렉터리 구조 (구현 시 예상)

```
ax-stt/
├── pipeline.py          # 메인 파이프라인 실행 진입점
├── extractor.py         # FFmpeg 오디오 추출 모듈
├── transcriber.py       # Whisper STT 모듈
├── packager.py          # JSON 출력 포매터
├── data/
│   └── raw/             # 입력 영상 (gitignore 처리)
├── results/             # 출력 JSON 저장
├── requirements.txt     # Python 의존성
├── .env.example         # 환경변수 템플릿
├── .pre-commit-config.yaml
└── .gitignore
```

---

## Runbook

### 1. 사전 요구 사항

| 항목 | 버전 | 설치 방법 |
|------|------|-----------|
| Python | 3.10 이상 | [python.org](https://www.python.org/downloads/) |
| FFmpeg | 최신 | `winget install FFmpeg` (Windows) / `brew install ffmpeg` (macOS) |
| Git | - | [git-scm.com](https://git-scm.com/) |

FFmpeg 설치 확인:

```bash
ffmpeg -version
```

### 2. 저장소 클론 및 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd ax-stt

# 가상환경 생성 및 활성화
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

주요 패키지:

```txt
openai>=1.0.0
moviepy>=1.0.3
pydub>=0.25.1
python-dotenv>=1.0.0
```

### 4. 환경 변수 설정

```bash
# .env.example 복사 후 편집
cp .env.example .env
```

`.env` 파일에 OpenAI API 키를 입력합니다:

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> **주의:** `.env` 파일은 절대 커밋하지 마세요. pre-commit 훅이 API 키 노출을 자동 차단합니다.

### 5. Pre-commit 훅 설치

```bash
pip install pre-commit
pre-commit install
```

### 6. 파이프라인 실행

```bash
# 단일 파일 처리
python pipeline.py --input data/raw/answer_01.mp4 \
                   --applicant user_123 \
                   --question q_01

# 결과는 results/ 디렉터리에 JSON으로 저장
```

**로컬 모드 (faster-whisper 사용 시):**

```bash
pip install faster-whisper
python pipeline.py --input data/raw/answer_01.mp4 \
                   --applicant user_123 \
                   --question q_01 \
                   --mode local
```

### 7. 출력 확인

```bash
cat results/user_123_q_01.json
```

---

## Troubleshooting

### ❌ `ffmpeg: command not found` 오류

**원인:** FFmpeg가 시스템 PATH에 등록되지 않음

```bash
# Windows — winget으로 설치
winget install FFmpeg

# 설치 후 터미널 재시작 필수
ffmpeg -version
```

macOS:

```bash
brew install ffmpeg
```

---

### ❌ `AuthenticationError: Invalid API Key`

**원인:** `.env` 파일에 API 키가 없거나 잘못 입력됨

1. `.env` 파일이 프로젝트 루트에 있는지 확인합니다.
2. `OPENAI_API_KEY=sk-...` 형식이 맞는지 검토합니다.
3. [OpenAI 콘솔](https://platform.openai.com/api-keys)에서 키 유효성을 확인합니다.

---

### ❌ `pre-commit` 훅이 API 키를 감지하여 커밋 차단

**원인:** 코드나 설정 파일에 API 키가 하드코딩됨

API 키를 코드에서 제거하고 `.env`로 이동합니다:

```python
# 잘못된 방법
client = openai.OpenAI(api_key="sk-xxxxx")

# 올바른 방법
import os
from dotenv import load_dotenv
load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

---

### ❌ STT 결과 품질 저하 (단어 뭉개짐, 오타)

**원인:** 오디오 품질 문제 또는 강한 배경 소음

- 입력 영상의 마이크 품질을 확인합니다.
- `pydub`로 오디오를 전처리하여 볼륨을 정규화합니다.
- Whisper `large` 모델 사용을 고려합니다 (정확도 ↑, 속도 ↓).

```python
# 모델 크기 변경 (faster-whisper 로컬 모드)
model = WhisperModel("large-v3", device="cpu")
```

---

### ❌ `data/raw/` 폴더가 gitignore로 무시됨

**의도된 동작**입니다. 대용량 영상 파일은 Git에 포함하지 않습니다.  
팀원 간 공유가 필요하면 별도 스토리지(S3, Google Drive 등)를 이용하거나  
`data/raw/sample/` 하위에 소용량 샘플 파일만 예외적으로 추적하세요:

```bash
git add -f data/raw/sample/answer_sample.mp4
```

---

### ❌ `ModuleNotFoundError: No module named 'moviepy'`

가상환경이 활성화된 상태인지 확인합니다:

```bash
# 활성화 여부 확인 (프롬프트 앞에 (.venv) 표시 확인)
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
```

---

## Contributing

1. `main` 브랜치에서 feature 브랜치를 분기합니다.
2. 커밋 전 pre-commit 훅이 통과하는지 확인합니다.
3. PR 제목에 변경 사항을 명확히 기술합니다.

---

> 아산 AX Step 3 — 5조 | 2026
