# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

- 이 프로젝트 참여자는 모두 한국인이기 때문에 md파일이나 주석은 모두 한국어로 작성해야 합니다.
- 참여한 개발자는 모두 초급 개발자이기 때문에 코드마다 주석을 달아서 쉽게 설명해주어야 합니다.
- 주석은 현재 작성된 코드에 달려있는 주석들을 참고하여, 기존 주석과 똑같은 방식과 형식으로 일관되게 작성하여야 합니다.


## 1. 프로젝트 개요

- **라이브러리 관리**: uv
- **라이브러리 사용**: fastapi, uvicorn[standard], sqlalchemy, greenlet, psycopg[binary], alembic, pydantic[email], pydantic-settings, pyjwt, python-multipart, pgvector ...(개발을 진행하면서 계속 추가/변경될 예정)
- **프로젝트 목적**: 무인 피자가게에서 조리기기가 피자를 만들 때 일정한 퀄리티를 보장할 수 있도록 AI를 활용한다.
- **프로젝트 목표 기능**: 
  - **메인 기능**: 조리기기가 피자의 상태를 카메라로 찍어 사진을 보내주면, Vision AI를 활용하여 피자 식자재의 종류, 상태, 누락 등을 판별한다. 
  - **보조 기능**: 
    - **비전 학습 기능**: 피자가게에서 원하는 최적의 피자 상태(토핑의 종류, 토핑의 양, 토핑 배치 등)의 특징을 벡터(임베딩) 형태로 변환하여 학습한다.
    - **사진 업로드 기능**: 조리기기가 피자 사진을 전송해주면, 해당 사진을 AWS S3에 저장한다.
    - **현재 상태 파악 및 차이 분석 기능**: 조리기기가 보내준 피자 사진을 바탕으로 멀티모달 LLM이 목표 사진과 현재 사진을 비교하여 차이를 분석한다.
    - **행동 계획 수립**: LLM이 다음 단계에서 필요한 명령을 생성한다. (예시: 치즈 토핑이 기준치 미달 상태이므로 피자에 추가로 치즈를 더 뿌려야 한다.)
- **주요 특징**: 
  - fastapi, uvicorn[standard]를 활용하여 웹 서버 구축
  - PoC 개발 단계 DB: Supabase에서 제공하는 무료티어 Postgres DB를 사용
  - 실무 전환 단계 DB: AWS에서 제공하는 Postgres DB로 변경할 예정
  - Postgres DB 관련: pgvector를 활용하여 임베딩 벡터 데이터를 저장할 수 있게 함. 나중에 Vector DB를 따로 추가하는 방안도 검토 중이지만, 개발 단계에서는 일단 Postgres DB에 벡터 데이터를 저장하는 방안을 선택
  - 이미지 저장: AWS S3에 저장할 예정
  - 비전 임베딩 모델: CLIP-ViT-Base32 (이 모델로 개발이 불가능한 경우 SigLIP2 모델로 대체)
  - PoC 개발 단계 LLM: ollama를 활용하여 Qwen3.5:9b 구동
  - 실무 전환 단계 LLM: AWS Bedrock에서 모델을 선택할 예정(아직 모델 미정)
  - LLM 출력 관련: 출력 형식 규칙화(JSON Mode)를 따른다. (예시: {"action": "STOP", "time": 0} 등과 같은 JSON 형식을 따르도록 만들어, LLM 모델을 변경하더라도 에러 가능성을 최소화함)


## 2. 프로젝트 개발

### 2-1. 백엔드 개발 및 빌드 명령어
백엔드 개발 시에는 `backend/` 디렉토리에서 진행한다. (uv 프로젝트 루트)
- **의존성 설치**: `uv sync`
- **패키지 추가**: `uv add <패키지명>` (개발 도구는 `uv add --dev <패키지명>`)
- **서버 실행**: `uv run uvicorn src.main:app --reload`
- **린트 검사**: `uv run ruff check .`
- **마이그레이션 생성**: `uv run alembic revision --autogenerate -m "변경 내용"`
- **마이그레이션 적용**: `uv run alembic upgrade head`

### 2-2. 프론트엔드 개발 및 명령어
프론트엔드 개발 시에는 `frontend/` 디렉토리에서 진행한다. (React + TypeScript + Vite, 아이콘 lucide-react, 폰트 pretendard)
- **의존성 설치**: `npm install`
- **개발 서버 실행**: `npm run dev` → http://localhost:3000 (백엔드 서버가 먼저 켜져 있어야 함)
- **타입 검사 + 빌드**: `npm run build` (결과물: `frontend/dist/`)

## 3. 규칙
- **린트**: `pyproject.toml`의 `[tool.ruff]` 설정에 따라 `line-length = 100`, `select = ["E", "F", "I", "UP", "B"]` (pycodestyle, pyflakes, isort)를 준수한다. 백엔드 작업을 마치기 전 `uv run ruff check .`를 실행한다.
- **환경 변수 추가**: `src/core/config.py`에 필드를 추가하고 `backend/.env.example`에도 항목을 추가해야 함
- **환경 변수 위치**: 모든 외부 연결 정보(주소, API 키, 모델 이름, 벡터 차원 등)는 코드에 적지 말고 `src/core/config.py`의 환경 변수로 받아야 한다. 환경 변수만 바꾸면 로컬/클라우드/고객사 환경을 자유롭게 전환할 수 있도록 한다.
- **외부 호출 관리**: DB, Vector DB, 임베딩, LLM 등을 호출하는 코드는 각각 `src/core/` 아래 한 파일에만 둔다. 다른 제품으로 교체할 때 그 파일만 수정하면 되도록 하기 위함이다. 

## 4. 주의
- **환경 변수 관리**: 데이터베이스 URL이나 AWS 관련 비밀키 등 타인에게 유출되어서는 안되는 정보는 절대 코드에 하드코딩하지 말고, `src/core/config.py`를 통해 `.env`에서 안전하게 로드하여 사용해야 한다.

## 5. 주석
- **코드 수정**: 클로드가 코드를 수정한 경우 `[수정]` 표시를 꼭 표기하고 `기존`과 `변경` 후가 어떻게 다른지 각각 설명해 주어야 한다. 만약 기존 코드를 수정하는 것이 아니라 완전히 새로운 기능이 추가되는 경우에는 `[신규]` 로 표시한다. 신규인 경우에는 `기존`이 없는 상태이므로 `기존`과 `변경`에 대한 설명을 하지 않고, `추가`된 것에 대한 설명을 한다.
- **수정 확인**: 개발자가 클로드의 수정 내용을 모두 확인한 경우, `[수정]` 표시를 직접 지워서 수정된 내용을 확인했음을 표시한다.