# 🏢 HS 코드 추천 시스템

한국 관세청 데이터 기반 지능형 HS 코드 추천 서비스

## 🚀 빠른 시작

### 1. 종속성 설치
```bash
uv sync
```

### 2. API 키 설정 (자동)
OpenAI API 키가 `docs/Aivle-api.txt` 파일에서 자동으로 로드됩니다.

### 3. UI 실행
```bash
# Gradio 웹 UI 실행
uv run python ui_app.py

# 또는 간단한 런처 사용
uv run python run_ui.py
```

### 4. 브라우저 접속
브라우저에서 `http://localhost:7860` 접속

## 🎯 주요 기능

- 🤖 **AI 기반 추천**: OpenAI GPT를 활용한 지능형 HS 코드 추천
- 🔍 **하이브리드 검색**: TF-IDF + 의미 기반 검색 결합
- 📊 **정확한 결과**: 신뢰도 점수와 상세 정보 제공
- 🇰🇷 **한국어 특화**: 한국 관세청 데이터 완벽 지원
- 📱 **웹 인터페이스**: 직관적인 Gradio UI
- ⚡ **자동 설정**: API 키 자동 로드로 간편한 사용

## 📁 프로젝트 구조

```
hs-code-recommender/
├── ui_app.py              # Gradio 웹 UI
├── run_ui.py              # UI 런처
├── main.py                # CLI 버전
├── config.py              # 설정 파일
├── src/                   # 소스 코드
├── data/                  # 관세청 데이터
├── cache/                 # 캐시 파일
├── output/               # 출력 파일
└── docs/                 # 문서
    ├── Aivle-api.txt     # OpenAI API 키 (자동 로드)
    ├── CLAUDE.md
    └── README.md
```

## 🛠️ 사용법

### 웹 UI 버전 (권장)
```bash
uv run python ui_app.py
```

### CLI 버전
```bash
uv run python main.py
```

## ⚙️ 설정

### API 키 자동 설정
OpenAI API 키는 `docs/Aivle-api.txt` 파일에 저장되어 있으며, 시스템 초기화 시 자동으로 로드됩니다.

### 수동 설정 (필요시)
자동 로드가 실패한 경우, 웹 UI의 "시스템 설정" 탭에서 수동으로 API 키를 입력할 수 있습니다.

## 📖 자세한 문서

자세한 사용법과 설정은 [docs/CLAUDE.md](docs/CLAUDE.md)를 참조하세요.

## 🔧 기술 스택

- **Python 3.9+**
- **UV**: 패키지 관리
- **Gradio**: 웹 UI
- **OpenAI**: AI 기반 추천
- **scikit-learn**: 머신러닝
- **SentenceTransformers**: 의미 검색

## ⚠️ 주의사항

이 시스템의 추천 결과는 참고용이며, 실제 HS 코드 신고 시에는 관세청에 최종 확인이 필요합니다.