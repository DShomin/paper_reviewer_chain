# 논문 리뷰어 체인

이 프로젝트는 논문을 자동으로 분석하고 리뷰하는 도구입니다.

## 설치 및 설정

1. 이 저장소를 클론합니다:
```bash
git clone https://github.com/yourusername/paper_reviewer_chain.git
cd paper_reviewer_chain
```

2. 가상 환경을 생성하고 활성화합니다:
```bash
python -m venv .venv
# Windows에서는
.venv\Scripts\activate
# macOS/Linux에서는
source .venv/bin/activate
```

3. 필요한 패키지를 설치합니다:
```bash
pip install -r requirements.txt
```

4. `.env.example` 파일을 `.env`로 복사하고 필요한 API 키를 입력합니다:
```bash
cp .env.example .env
# 텍스트 에디터로 .env 파일을 열어 API 키를 입력합니다
```

## 필요한.env 변수

이 프로젝트에는 다음 API 키가 필요합니다:

- `OPENAI_API_KEY`: OpenAI API 키 (https://platform.openai.com/api-keys에서 발급 가능)
- `YOUTUBE_API_KEY`: YouTube Data API 키 (https://console.cloud.google.com/에서 발급 가능)

## 실행 방법

애플리케이션을 실행하려면:

```bash
python Home.py
```

## 주요 기능

- 논문 리뷰 자동화
- 논문 요약 생성
- 핵심 아이디어 분석

## 프로젝트 구조

```
paper_reviewer_chain/
├── Home.py          # 메인 애플리케이션 진입점
├── pages/           # 애플리케이션 페이지
├── src/             # 핵심 소스 코드
├── data/            # 데이터 파일 (git에서 제외됨)
└── requirements.txt # 의존성 패키지 목록
```

## 참고 사항

- `data/` 디렉토리와 `.env` 파일은 Git에서 제외되어 있습니다.
- 필요한 API 키를 발급받아 `.env` 파일에 설정해야 합니다. 