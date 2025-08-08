# Data Processing Module

한국 관세법 문서의 처리, 청킹, 메타데이터 추출을 담당하는 모듈입니다.

## 개요

이 모듈은 한국 관세법 관련 문서들(관세법, 관세법시행령, 관세법시행규칙)을 JSON 형태에서 AI 처리에 적합한 청크 단위로 변환하는 기능을 제공합니다. 법령의 계층 구조를 이해하고, 조문의 복잡도에 따라 지능적으로 청킹 전략을 결정합니다.

## 주요 기능

- **지능형 청킹**: 조문의 복잡도에 따라 조 단위 또는 항 단위로 자동 분할
- **계층 구조 추출**: 편-장-절-관-조 계층 구조 자동 인식
- **법령 참조 추출**: 내부/외부 법령 참조 패턴 자동 식별
- **메타데이터 생성**: 각 청크에 대한 상세한 메타데이터 생성
- **품질 검증**: 청크 데이터 무결성 및 구조 검증

## 모듈 구조

```
src/data_processing/
├── __init__.py          # 모듈 초기화 및 exports
├── document_loader.py   # CustomsLawLoader 클래스 (메인 처리 엔진)
├── chunking_utils.py    # 청킹 결과 분석 및 유틸리티
└── README.md           # 이 파일
```

## 빠른 시작

### 1. 기본 사용법

```python
from src.data_processing import CustomsLawLoader
from src.utils.file_utils import load_json_data

# JSON 데이터 로드
law_data = load_json_data("data/DCM/raw_json/관세법.json")

# CustomsLawLoader 인스턴스 생성
loader = CustomsLawLoader(law_data)

# 문서 처리 및 청킹
processed_documents = loader.load()

print(f"생성된 청크 수: {len(processed_documents)}")
```

### 2. 결과 분석

```python
from src.data_processing import analyze_chunking_results, get_chunk_statistics

# 기본 분석
analysis = analyze_chunking_results(processed_documents)
print(analysis['analysis_summary'])

# 상세 통계
stats = get_chunk_statistics(processed_documents)
print(f"최소 길이: {stats['length_stats']['min']}")
print(f"최대 길이: {stats['length_stats']['max']}")
```

### 3. 품질 검증

```python
from src.data_processing import validate_chunk_integrity

# 데이터 무결성 검증
issues = validate_chunk_integrity(processed_documents)
if issues:
    print("발견된 문제점:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("✅ 데이터 무결성 검증 통과")
```

## 주요 클래스: CustomsLawLoader

### 클래스 개요

`CustomsLawLoader`는 한국 관세법 JSON 데이터를 지능적으로 청킹하는 메인 클래스입니다.

### 초기화

```python
loader = CustomsLawLoader(json_data)
```

**매개변수:**

- `json_data` (Dict): 관세법 JSON 데이터

### 주요 메서드

#### `load() -> List[Dict]`

전체 로딩 프로세스를 실행하여 청크된 문서들을 반환합니다.

```python
documents = loader.load()
```

**반환값:** 처리된 문서 청크들의 리스트

#### `determine_chunking_strategy(article: Dict) -> str`

조문의 복잡도에 따라 청킹 전략을 결정합니다.

- **조 단위 청킹**: 항이 3개 미만인 단순한 조문
- **항 단위 청킹**: 항이 3개 이상인 복잡한 조문

#### `extract_hierarchy_context(current_index: int, articles: List[Dict]) -> Dict`

현재 조문의 상위 계층 정보를 추출합니다.

**지원하는 계층:**

- 편 (doc): `제1편`
- 장 (chapter): `제1장`
- 절 (section): `제1절`
- 관 (subsection): `제1관`

## 유틸리티 함수들

### analyze_chunking_results(documents: List[Dict]) -> Dict

청킹 결과에 대한 기본 분석을 수행합니다.

```python
analysis = analyze_chunking_results(documents)
# 반환값:
# {
#     "total_chunks": 150,
#     "article_level_count": 120,
#     "paragraph_level_count": 30,
#     "average_chunk_length": 245.6,
#     "law_distribution": {"관세법": 150},
#     "analysis_summary": "총 150개 청크 생성..."
# }
```

### get_chunk_statistics(documents: List[Dict]) -> Dict

더 상세한 통계 정보를 제공합니다.

```python
stats = get_chunk_statistics(documents)
# 길이 분포, 참조 패턴 등의 상세 통계
```

### validate_chunk_integrity(documents: List[Dict]) -> List[str]

청크 데이터의 무결성을 검증합니다.

```python
issues = validate_chunk_integrity(documents)
# 발견된 문제점들의 리스트 반환
```

### print_sample_chunks(documents: List[Dict], num_samples: int = 2)

샘플 청크들을 콘솔에 출력합니다.

```python
print_sample_chunks(documents, num_samples=3)
```

## 출력 데이터 구조

각 청크는 다음과 같은 구조를 가집니다:

```python
{
    "index": "제1조" | "제5조제1항",              # 조문 인덱스
    "subtitle": "조문의 제목",                     # 조문 제목
    "content": "정제된 조문 내용",                 # 실제 내용
    "metadata": {
        "law_name": "관세법",                     # 법령명
        "law_level": "법률",                      # 법령 단계
        "doc": "제1편 ...",                       # 편 정보
        "chapter": "제1장 ...",                   # 장 정보
        "section": "제1절 ...",                   # 절 정보
        "subsection": None,                       # 관 정보
        "effective_date": "2023.01.01",          # 시행일자
        "hierarchy_path": "제1장 총칙>제1절>제1조", # 계층 경로
        "chunk_type": "article_level",            # 청킹 타입
        "internal_law_references": {              # 내부 법령 참조
            "refers_to_main_law": [...],
            "refers_to_enforcement_decree": [...],
            "refers_to_enforcement_rules": [...]
        },
        "external_law_references": [...],         # 외부 법령 참조
        "total_paragraphs": 2                     # 총 항 개수
    }
}
```

## 고급 사용법

### 1. 커스텀 청킹 전략

```python
# 기본 설정 확인
from src.utils.config import get_setting

threshold = get_setting("chunk_strategy.paragraph_threshold", 3)
print(f"현재 항 분할 임계값: {threshold}")
```

### 2. 법령 참조 패턴 분석

```python
# 내부 참조 패턴 추출
for doc in processed_documents:
    internal_refs = doc['metadata']['internal_law_references']
    if internal_refs['refers_to_main_law']:
        print(f"{doc['index']}: {internal_refs['refers_to_main_law']}")
```

### 3. 계층별 문서 필터링

```python
# 특정 장의 문서만 필터링
chapter_1_docs = [
    doc for doc in processed_documents
    if doc['metadata'].get('chapter') and '제1장' in doc['metadata']['chapter']
]
```

## 성능 최적화

### 메모리 사용량 최적화

```python
# 대량 문서 처리시 배치 처리
def process_in_batches(law_data, batch_size=100):
    articles = law_data["법령"]["조문"]["조문단위"]
    for i in range(0, len(articles), batch_size):
        batch_data = {
            "법령": {
                **law_data["법령"],
                "조문": {"조문단위": articles[i:i+batch_size]}
            }
        }
        loader = CustomsLawLoader(batch_data)
        yield loader.load()
```

## 에러 처리

### 일반적인 에러 상황

```python
try:
    loader = CustomsLawLoader(law_data)
    documents = loader.load()
except KeyError as e:
    print(f"필수 JSON 키가 누락되었습니다: {e}")
except Exception as e:
    print(f"처리 중 오류 발생: {e}")
```

### 데이터 품질 확인

```python
# 빈 내용 청크 확인
empty_chunks = [
    doc for doc in documents
    if not doc['content'].strip()
]
if empty_chunks:
    print(f"빈 내용 청크 {len(empty_chunks)}개 발견")
```

## 디버깅 팁

### 로깅 활성화

```python
import logging

# 디버그 로깅 활성화
logging.getLogger('src.data_processing').setLevel(logging.DEBUG)
```

### 청킹 결과 시각화

```python
# 청킹 전략별 분포 확인
from collections import Counter

chunk_types = [doc['metadata']['chunk_type'] for doc in documents]
distribution = Counter(chunk_types)
print(f"청킹 전략 분포: {dict(distribution)}")
```

## 확장 가능성

### 새로운 법령 추가

1. `src/utils/config.py`의 `get_law_data_paths()`에 새 법령 추가
2. 법령별 특수 처리 로직이 필요한 경우 `CustomsLawLoader` 확장
3. 새로운 참조 패턴이 있는 경우 `extract_internal_law_references()` 업데이트

### 커스텀 청킹 전략

```python
class ExtendedCustomsLawLoader(CustomsLawLoader):
    def determine_chunking_strategy(self, article):
        # 커스텀 로직 구현
        if self.has_complex_structure(article):
            return "custom_level"
        return super().determine_chunking_strategy(article)
```

## 문제 해결

### 일반적인 문제들

**Q: 청킹 결과가 예상과 다릅니다**
A: `determine_chunking_strategy()` 메서드의 임계값을 확인하고, `print_sample_chunks()`로 결과를 검토하세요.

**Q: 메모리 사용량이 너무 높습니다**
A: 배치 처리를 사용하거나, 필요한 메타데이터만 추출하도록 설정을 조정하세요.

**Q: 법령 참조가 제대로 추출되지 않습니다**
A: `extract_internal_law_references()`의 정규식 패턴을 확인하고, 새로운 참조 형식에 대한 패턴을 추가하세요.

## 라이선스 및 기여

이 모듈은 한국 관세법 문서 처리 전용으로 설계되었습니다. 다른 법령이나 문서 타입으로 확장시에는 적절한 수정이 필요합니다.
