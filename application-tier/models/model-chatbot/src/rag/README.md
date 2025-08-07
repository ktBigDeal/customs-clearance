# 관세법 RAG 시스템

OpenAI API를 활용한 한국 관세법 문서 기반 RAG(Retrieval-Augmented Generation) 시스템

## 개요

이 시스템은 관세법, 관세법시행령, 관세법시행규칙 문서를 기반으로 한 지능형 법률 상담 챗봇입니다. OpenAI의 `text-embedding-3-small` 모델로 임베딩을 생성하고, `GPT-4.1mini` 모델로 대화형 응답을 제공합니다.

## 주요 기능

### 🔍 **고급 검색 기능**

- **의미 기반 검색**: OpenAI 임베딩을 활용한 의미 기반 문서 검색
- **쿼리 정규화**: GPT를 사용하여 사용자 질의를 법률 검색에 최적화
- **내부 참조 추적**: `internal_law_references`를 활용한 관련 조문 자동 검색
- **동의어 확장**: 법률 용어 동의어를 포함한 확장 검색

### 💬 **대화형 상담**

- **컨텍스트 유지**: 대화 기록을 고려한 연속적인 상담
- **메모리 관리**: 이전 대화 내용과 참조 문서 추적
- **근거 제시**: 모든 답변에 관련 법령 조문 근거 제시

### 📊 **데이터 처리**

- **지능형 청킹**: 조문의 복잡도에 따른 자동 분할
- **계층 구조 인식**: 편-장-절-관-조 법령 계층 구조 자동 추출
- **참조 네트워크**: 법령 간 참조 관계 분석 및 활용

## 시스템 구조

```Plain Text
src/rag/
├── __init__.py                 # 모듈 초기화
├── embeddings.py              # OpenAI 임베딩 생성
├── vector_store.py            # ChromaDB 벡터 저장소
├── query_normalizer.py        # 쿼리 정규화 및 의도 분석
├── retriever.py               # 유사 문서 검색 및 참조 추적
├── conversation_agent.py      # 대화형 RAG 에이전트
├── data_processor.py          # 향상된 데이터 처리
├── cli.py                     # 명령줄 인터페이스
└── README.md                  # 이 파일
```

## 빠른 시작

### 1. 환경 설정

API 키가 `.env` 파일에 설정되어 있는지 확인:

```bash
OPENAI_API_KEY=your_openai_api_key
```

### 2. 데이터베이스 초기화

```bash
# CLI를 통한 초기 설정
python -m src.rag.cli --setup

# 기존 데이터 재설정
python -m src.rag.cli --setup --reset
```

### 3. 대화형 상담 시작

```bash
python -m src.rag.cli --chat
```

### 4. 문서 검색

```bash
# 특정 키워드로 검색
python -m src.rag.cli --search "수입신고 서류"

# 검색 결과 개수 지정
python -m src.rag.cli --search "관세 면제" --top-k 10
```

### 5. 통계 정보 확인

```bash
python -m src.rag.cli --stats
```

## 프로그래밍 인터페이스

### 기본 사용법

```python
from src.rag import (
    OpenAIEmbedder,
    ChromaVectorStore,
    QueryNormalizer,
    SimilarLawRetriever,
    ConversationAgent
)

# 시스템 초기화
embedder = OpenAIEmbedder()
vector_store = ChromaVectorStore()
query_normalizer = QueryNormalizer()

retriever = SimilarLawRetriever(
    embedder=embedder,
    vector_store=vector_store,
    query_normalizer=query_normalizer
)

agent = ConversationAgent(retriever=retriever)

# 대화형 상담
response, docs = agent.chat("수입신고서에 필요한 서류는 무엇인가요?")
print(response)
```

### 검색만 사용하기

```python
# 문서 검색
results = retriever.search_similar_laws(
    raw_query="관세 면제 조건",
    top_k=5,
    include_references=True
)

for result in results:
    print(f"조문: {result['metadata']['index']}")
    print(f"내용: {result['content'][:100]}...")
    print(f"유사도: {result['similarity']:.3f}")
```

### 데이터 처리

```python
from src.rag.data_processor import EnhancedDataProcessor

processor = EnhancedDataProcessor(embedder, vector_store)

# 모든 법령 데이터 처리
result = processor.load_and_process_all_laws()
print(f"처리된 문서 수: {result['statistics']['total_documents']}")

# 특정 법령만 로드
documents = processor.load_specific_law("관세법")
```

## 고급 기능

### 내부 참조 활용

시스템은 `internal_law_references` 메타데이터를 활용하여 관련 조문을 자동으로 검색합니다:

```json
{
  "internal_law_references": {
    "refers_to_main_law": ["제1조", "제5조"],
    "refers_to_enforcement_decree": ["제10조"],
    "refers_to_enforcement_rules": ["제20조"]
  }
}
```

### 컨텍스트 확장 검색

```python
# 기존 대화 컨텍스트를 고려한 검색
results = retriever.search_with_context_expansion(
    query="그럼 B/L 번호는?",
    context_documents=previous_documents,
    top_k=5
)
```

### 쿼리 정규화 및 의도 분석

```python
# 쿼리 정규화
normalized = query_normalizer.normalize("물품 검사는 언제 안 해도 돼?")
# -> "물품 검사 면제 조건 및 기준"

# 의도 추출
intent = query_normalizer.extract_legal_intent("수입할 때 뭘 내야 해?")
# -> {"intent_type": "절차안내", "law_area": "수입", ...}
```

## 설정 옵션

### 임베딩 모델 설정

```python
embedder = OpenAIEmbedder(model_name="text-embedding-3-small")
```

### 대화 에이전트 설정

```python
agent = ConversationAgent(
    retriever=retriever,
    model_name="gpt-4.1-mini",
    temperature=0.2,
    max_context_docs=5
)
```

### 벡터 저장소 설정

```python
vector_store = ChromaVectorStore(
    db_path="custom/path/to/chroma_db",
    collection_name="custom_collection"
)
```

## 성능 최적화

### 배치 처리

```python
# 여러 텍스트 동시 임베딩
embeddings = embedder.embed_texts(text_list, batch_size=100)

# 문서 배치 처리
enhanced_docs = embedder.embed_documents(documents)
```

### 메모리 관리

```python
# 대화 기록 제한
memory = ConversationMemory(max_history=10)

# 컨텍스트 문서 수 제한
agent = ConversationAgent(retriever, max_context_docs=3)
```

## 문제 해결

### 일반적인 오류

**Q: "Collection not initialized" 오류**
A: `vector_store.create_collection()`을 먼저 호출하거나 `--setup` 옵션으로 데이터를 로드하세요.

**Q: OpenAI API 오류**
A: `.env` 파일의 `OPENAI_API_KEY`가 올바른지 확인하세요.

**Q: 검색 결과가 부정확함**
A: 쿼리 정규화를 활용하거나 `expand_with_synonyms=True` 옵션을 사용하세요.

### 로깅 활성화

```python
import logging
logging.getLogger('src.rag').setLevel(logging.DEBUG)
```

### 데이터 검증

```python
# 문서 구조 검증
validation_result = processor.validate_document_structure(documents)
print(validation_result['issues'])

# 참조 네트워크 분석
network = processor.extract_reference_network(documents)
print(network['statistics'])
```

## 확장 가능성

### 새로운 법령 추가

1. `src/utils/config.py`의 `get_law_data_paths()`에 새 법령 추가
2. JSON 데이터를 `data/DCM/chunk_json/` 디렉토리에 배치
3. `--setup --reset` 옵션으로 데이터베이스 재구성

### 커스텀 검색 전략

```python
class CustomRetriever(SimilarLawRetriever):
    def search_similar_laws(self, query, **kwargs):
        # 커스텀 검색 로직 구현
        return super().search_similar_laws(query, **kwargs)
```

### 다른 언어 모델 통합

시스템의 모듈식 설계로 인해 OpenAI 외 다른 모델도 쉽게 통합 가능합니다.

## 라이선스

이 프로젝트는 한국 관세법 문서 처리 전용으로 개발되었습니다.
