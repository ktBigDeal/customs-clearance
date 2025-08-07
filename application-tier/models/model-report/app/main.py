"""
LangChain 기반 관세신고서 생성 서비스

이 모듈은 LangChain과 OpenAI GPT를 사용하여 OCR 결과를 바탕으로
한국 관세청 규정에 맞는 수입/수출 신고서를 자동 생성합니다.
"""

from fastapi import FastAPI
import json
import asyncio
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import os
from langchain.schema import Document
import re
from pydantic import BaseModel
from typing import List, Dict, Any
from dotenv import load_dotenv
from pathlib import Path

# --- 환경 변수 로딩 ---
env_path = Path(__file__).parent.parent / '.env'

# 절대 경로를 사용해 .env 파일 로드
load_dotenv(dotenv_path=env_path)
load_dotenv(dotenv_path="../.env")

app = FastAPI()

base_path = Path(__file__).parent.parent


# 수입신고서 전체항목정의 처리
def process_entry(항목명, 내용):
    """
    신고서 항목 정의를 Document 객체로 변환
    
    한국 관세청의 수입/수출 신고서 항목정의를 LangChain Document 형태로 변환합니다.
    각 항목의 조건, 타입, 작성요령, 예시 등을 구조화합니다.
    
    Args:
        항목명 (str): 신고서 항목명
        내용 (dict): 항목의 상세 정보
        
    Returns:
        List[Document]: LangChain Document 객체 리스트
    """
    documents = []
    if 'TYPE' in 내용:
        content = (
            f"[항목명] {항목명} "
            f"[조건] {내용.get('조건', '-')} "
            f"[TYPE] {내용.get('TYPE', '-')}, SIZE: {내용.get('SIZE', '-')} "
            f"[작성요령] {내용.get('작성요령', '-')} "
            f"[예시] {내용.get('예시', '-')}"
        )
        if '통계부호' in 내용:
            content += f"[통계부호] {내용.get('통계부호', '-')}"
        documents.append(Document(page_content=content, metadata={"항목": 항목명}))
    else:
        for 하위항목명, 하위내용 in 내용.items():
            documents.extend(process_entry(f"{항목명} - {하위항목명}", 하위내용))
    return documents

documents = []
with open(base_path / "수입신고서_전체항목정의(v1).json", "r", encoding="utf-8") as f:
    data = json.load(f)
for 항목명, 항목내용 in data.items():
    documents.extend(process_entry(항목명, 항목내용))

# Load and process 수출신고서_전체항목정의(v1).json
export_documents = []
with open(base_path / "수출신고서_전체항목정의(v1).json", "r", encoding="utf-8") as f:
    data = json.load(f)
for 항목명, 항목내용 in data.items():
    export_documents.extend(process_entry(항목명, 항목내용))

# Load and process 무역통계부호.json
def flatten_dict(section, d, prefix=None):
    docs = []
    for k, v in d.items():
        if isinstance(v, dict):
            docs += flatten_dict(section, v, (prefix + " | " + k) if prefix else k)
        else:
            meta = {"section": section, "code_path": (prefix + " | " + k) if prefix else k}
            docs.append(Document(page_content=f"{section} | {(prefix + ' | ' + k) if prefix else k}: {v}", metadata=meta))
    return docs

def make_documents(json_path):
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    stat_code_documents = []
    for section, codes in data.items():
        if isinstance(codes, dict):
            stat_code_documents += flatten_dict(section, codes)
        else:
            stat_code_documents.append(Document(page_content=f"{section}: {codes}", metadata={"section": section}))
    return stat_code_documents

stat_code_documents = make_documents(base_path / "무역통계부호.json")

# AI Model Setting
llm = ChatOpenAI(temperature=0.3, model_name="gpt-4o-mini")

# User-defined functions (Document Search)
def get_documents_by_main_item_name(documents, main_item_name):
    matching_documents = []
    for doc in documents:
        item_in_metadata = doc.metadata.get("항목")
        if item_in_metadata:
            if item_in_metadata == main_item_name or item_in_metadata.startswith(f"{main_item_name} - "):
                matching_documents.append(doc)
    return matching_documents

def extract_stat_code(document_content):
    match = re.search(r"\[통계부호\]\s*(.*?)(?=\[|$)", document_content)
    if match:
        return match.group(1).strip()
    return None

def get_stat_documents_by_section(stat_documents, section_name):
    matching_stat_docs = []
    for doc in stat_documents:
        if doc.metadata.get("section") == section_name:
            matching_stat_docs.append(doc)
    return matching_stat_docs

# Prompt Templates
prompt = PromptTemplate(
    input_variables=["통관","항목명", "작성요령", "ocr_result"],
    template="""
너는 {통관}신고서 자동작성 AI야.
다음 문서와 작성요령을 참고해서 "{항목명}" 항목에 들어갈 값을 작성해줘.

※ 작성요령:
{작성요령}

※ 문서 정보:
OCR 추출값 : {ocr_result}

조건:
- 작성요령을 반드시 지켜서 값의 형식, 단위 등을 지켜 작성
- 하위항목의 작성요령 또한 반드시 참고해서 작성
- 값에는 모든 하위항목의 값을 모두 붙여서 표기
- 문서에서 나온 정보들로 작성 못할 경우 "미기재"로 작성
- 오직 값만 출력해 (예: 43411, 20010201, Korea 등)
"""
)

item_prompt = PromptTemplate(
    input_variables=["통관","item_key", "작성요령", "item_data"],
    template="""
너는 {통관}신고서 자동작성 AI야.
다음 품목 정보와 작성요령을 참고해서 "{item_key}" 항목에 들어갈 값을 작성해줘.

※ 작성요령:
{작성요령}

※ 품목 정보:
{item_data}

조건:
- 작성요령을 반드시 지켜서 값의 형식, 단위 등을 지켜 작성
- "{item_key}" 항목에 해당하는 값만 추출해서 작성
- 오직 값만 출력해 (예: Thermometer, 96, $47.44 등)
- 정보가 없을 경우 "미기재"로 작성해
"""
)

llm_chain = LLMChain(llm=llm, prompt=prompt)
item_llm_chain = LLMChain(llm=llm, prompt=item_prompt)

# Helper functions for processing
async def process_main_item(통관, 항목명, llm_chain, documents_to_search, stat_code_documents, current_ocr_result):
    retrieved_docs = get_documents_by_main_item_name(documents_to_search, f"{항목명}")
    retrieved_stat = []
    for docs in retrieved_docs:
        stat_code = extract_stat_code(docs.page_content)
        if stat_code:
            retrieved_stat.extend(get_stat_documents_by_section(stat_code_documents, stat_code))
    retrieved_docs.extend(retrieved_stat)
    작성요령 = "\n".join([doc.page_content for doc in retrieved_docs])
    항목값 = await llm_chain.arun({
        "통관": 통관,
        "항목명": 항목명,
        "작성요령": 작성요령,
        "ocr_result": json.dumps(current_ocr_result, ensure_ascii=False)
    })
    return 항목명, 항목값.strip()

async def process_item_detail(통관, item_key, item_llm_chain, documents_to_search, stat_code_documents, item_data):
    retrieved_docs = get_documents_by_main_item_name(documents_to_search, item_key)
    retrieved_stat = []
    for docs in retrieved_docs:
        stat_code = extract_stat_code(docs.page_content)
        if stat_code:
            retrieved_stat.extend(get_stat_documents_by_section(stat_code_documents, stat_code))
    retrieved_docs.extend(retrieved_stat)
    작성요령 = "\n".join([doc.page_content for doc in retrieved_docs])
    item_value = await item_llm_chain.arun({
        "통관": 통관,
        "item_key": item_key,
        "작성요령": 작성요령,
        "item_data": json.dumps(item_data, ensure_ascii=False)
    })
    return item_key, item_value.strip()

async def process_all_items(통관, items_list_data, 물품_list, item_llm_chain, documents_to_search, stat_code_documents):
    all_item_results = []
    for item_data in items_list_data:
        item_tasks = [
            process_item_detail(
                통관,
                item_key,
                item_llm_chain,
                documents_to_search,
                stat_code_documents,
                item_data
            ) for item_key in 물품_list
        ]
        item_details = await asyncio.gather(*item_tasks)
        extracted_item_data = dict(item_details)
        all_item_results.append(extracted_item_data)
    return all_item_results

# Define target item lists
항목명_list = [
    "신고구분", "거래구분", "종류", "원산지", "B/L(AWB)번호", "Master B/L 번호",
    "국내도착항", "선기명", "수입자", "납세의무자", "해외공급자", "적출국", "결제금액", "총포장갯수"
]
물품_list = [
    "거래품명", "세번번호", "모델·규격", "수량", "단가", "순중량", "총중량", "금액", "총포장갯수"
]
all_target_items = 항목명_list + 물품_list

수출_항목명_list = [
    "수출대행자",
    "제조자",
    "구매자",
    "신고구분",
    "거래구분",
    "종류",
    "목적국",
    "선박명(또는 항공편명)",
    "운송형태",
    "송품장부호",
    "원산지",
    "순중량",
    "총중량",
    "총포장개수",
    "결제금액"
]

수출_물품_list = [
    "물품상태",
    "품명",
    "거래품명",
    "상표명",
    "모델및규격",
    "수량",
    "단가",
    "금액",
    "세번부호",
    "순중량",
    "총중량",
    "포장개수"
]
all_export_target_items = 수출_항목명_list + 수출_물품_list
# Filter documents based on target items
filtered_documents = []
for doc in documents:
    item_in_metadata = doc.metadata.get("항목")
    if item_in_metadata:
        if any(item_in_metadata == target_item or item_in_metadata.startswith(f"{target_item} - ") for target_item in all_target_items):
            filtered_documents.append(doc)

# Filter export documents based on target items
export_filtered_documents = []
for doc in export_documents:
    item_in_metadata = doc.metadata.get("항목")
    if item_in_metadata:
        if any(item_in_metadata == target_item or item_in_metadata.startswith(f"{target_item} - ") for target_item in all_export_target_items):
            export_filtered_documents.append(doc)

# OCR mapping function
def map_ocr_data(ocr_data, mapping):
    mapped_data = {}
    for key, value in ocr_data.items():
        if key in mapping:
            mapped_key = mapping[key]
            if isinstance(value, dict):
                if isinstance(mapped_key, dict):
                    mapped_data[mapped_key] = map_ocr_data(value, mapped_key)
                elif isinstance(mapped_key, list) and len(mapped_key) > 0 and isinstance(mapped_key[0], dict):
                    mapped_data[key] = map_ocr_data(value, mapped_key[0])
                else:
                    mapped_data[mapped_key] = value
            elif isinstance(value, list):
                item_mapping = mapping.get(key)
                if isinstance(item_mapping, list) and len(item_mapping) > 0 and isinstance(item_mapping[0], dict):
                    mapped_data[key] = [map_ocr_data(item, item_mapping[0]) for item in value if isinstance(item, dict)]
                else:
                    mapped_data[mapped_key] = value
            else:
                mapped_data[mapped_key] = value
        else:
            mapped_data[key] = value
    return mapped_data

# OCR mapping dictionary
ocr_mapping = {
    "invoice_number": "인보이스 번호",
    "country_export": "수출국명",
    "country_import": "수입국명",
    "shipper": "수출자",
    "importer": "수입자(납세의무자)",
    "buyer": "납세의무자",
    "total_amount": "총 결제금액",
    "items": [
        {
            "item_name": "상품명",
            "quantity": "수량",
            "unit": "수량 단위",
            "unit_price": "단가",
            "amount": "금액",
            "hs_code": "HS 코드",
            "gross_weight": "총중량",
            "net_weight": "순중량",
            "total_package": "포장개수",
        }
    ],
    "gross_weight": "총중량",
    "net_weight": "순중량",
    "total_packages": "총포장개수",
    "bill_number": "BL 번호",
    "port_departure": "출발항",
    "port_destination": "도착항",
    "vessel_name": "선기명",
    "vessel_nationality": "선박 국적"
}

# Pydantic models
class OcrData(BaseModel):
    ocr_data: Dict[str, Any]

class ItemResult(BaseModel):
    거래품명: str
    세번번호: str
    모델규격: str
    수량: str
    단가: str
    순중량: str
    총중량: str
    금액: str
    총포장갯수: str

class ExportItemResult(BaseModel):
    물품상태: str
    품명: str
    거래품명: str
    상표명: str
    모델및규격: str
    수량: str
    단가: str
    금액: str
    세번부호: str
    순중량: str
    총중량: str
    포장개수: str

class DeclarationRequest(BaseModel):
    ocr_data: Dict[str, Any]

class DeclarationResponse(BaseModel):
    신고구분: str
    거래구분: str
    종류: str
    원산지: str
    BL_AWB_번호: str
    Master_BL_번호: str
    국내도착항: str
    선기명: str
    수입자: str
    납세의무자: str
    해외공급자: str
    적출국: str
    결제금액: str
    총포장갯수: str
    품목별_결과: List[ItemResult]

class ExportDeclarationResponse(BaseModel):
    수출대행자: str
    제조자: str
    구매자: str
    신고구분: str
    거래구분: str
    종류: str
    목적국: str
    선박명: str
    운송형태: str
    송품장부호: str
    원산지: str
    순중량: str
    총중량: str
    총포장개수: str
    결제금액: str
    품목별_결과: List[ExportItemResult]

@app.post("/generate-customs-declaration/import", response_model=DeclarationResponse)
async def generate_declaration(request: DeclarationRequest):
    mapped_ocr_result = map_ocr_data(request.ocr_data, ocr_mapping)

    final_result = {}
    main_item_tasks = [
        process_main_item(
            "수입",
            항목명,
            llm_chain,
            filtered_documents,
            stat_code_documents,
            mapped_ocr_result
        ) for 항목명 in 항목명_list
    ]
    main_item_results = await asyncio.gather(*main_item_tasks)
    final_result.update(dict(main_item_results))

    items_list_data = mapped_ocr_result.get("items", [])
    llm_item_results = await process_all_items(
        "통관",
        items_list_data,
        물품_list,
        item_llm_chain,
        filtered_documents,
        stat_code_documents
    )
    final_result["품목별 결과"] = llm_item_results

    response_data = {
        "신고구분": final_result.get("신고구분", "미기재"),
        "거래구분": final_result.get("거래구분", "미기재"),
        "종류": final_result.get("종류", "미기재"),
        "원산지": final_result.get("원산지", "미기재"),
        "BL_AWB_번호": final_result.get("B/L(AWB)번호", "미기재"),
        "Master_BL_번호": final_result.get("Master B/L 번호", "미기재"),
        "국내도착항": final_result.get("국내도착항", "미기재"),
        "선기명": final_result.get("선기명", "미기재"),
        "수입자": final_result.get("수입자", "미기재"),
        "납세의무자": final_result.get("납세의무자", "미기재"),
        "해외공급자": final_result.get("해외공급자", "미기재"),
        "적출국": final_result.get("적출국", "미기재"),
        "결제금액": final_result.get("결제금액", "미기재"),
        "총포장갯수": final_result.get("총포장갯수", "미기재"),
        "품목별_결과": [
            {
                "거래품명": item.get("거래품명", "미기재"),
                "세번번호": item.get("세번번호", "미기재"),
                "모델규격": item.get("모델·규격", "미기재"),
                "수량": item.get("수량", "미기재"),
                "단가": item.get("단가", "미기재"),
                "순중량": item.get("순중량", "미기재"),
                "총중량": item.get("총중량", "미기재"),
                "금액": item.get("금액", "미기재"),
                "총포장갯수": item.get("총포장갯수", "미기재"),
            } for item in final_result.get("품목별 결과", [])
        ]
    }

    return DeclarationResponse(**response_data)

@app.post("/generate-customs-declaration/export", response_model=ExportDeclarationResponse)
async def generate_export_declaration(request: DeclarationRequest):
    mapped_ocr_result = map_ocr_data(request.ocr_data, ocr_mapping)
    final_result = {}

    main_item_tasks = [
        process_main_item(
            "수출",
            항목명,
            llm_chain,
            export_filtered_documents,
            stat_code_documents,
            mapped_ocr_result
        ) for 항목명 in 수출_항목명_list
    ]
    main_item_results = await asyncio.gather(*main_item_tasks)
    final_result.update(dict(main_item_results))
    items_list_data = mapped_ocr_result.get("items", [])
    llm_item_results = await process_all_items(
        "수출",
        items_list_data,
        수출_물품_list,
        item_llm_chain,
        export_filtered_documents,
        stat_code_documents
    )
    final_result["품목별 결과"] = llm_item_results
    response_data = {
        "수출대행자": final_result.get("수출대행자", "미기재"),
        "제조자": final_result.get("제조자", "미기재"),
        "구매자": final_result.get("구매자", "미기재"),
        "신고구분": final_result.get("신고구분", "미기재"),
        "거래구분": final_result.get("거래구분", "미기재"),
        "종류": final_result.get("종류", "미기재"),
        "목적국": final_result.get("목적국", "미기재"),
        "선박명": final_result.get("선박명(또는 항공편명)", "미기재"),
        "운송형태": final_result.get("운송형태", "미기재"),
        "송품장부호": final_result.get("송품장부호", "미기재"),
        "원산지": final_result.get("원산지", "미기재"),
        "순중량": final_result.get("순중량", "미기재"),
        "총중량": final_result.get("총중량", "미기재"),
        "총포장개수": final_result.get("총포장개수", "미기재"),
        "결제금액": final_result.get("결제금액", "미기재"),
        "품목별_결과": [
            {
                "물품상태": item.get("물품상태", "미기재"),
                "품명": item.get("품명", "미기재"),
                "거래품명": item.get("거래품명", "미기재"),
                "상표명": item.get("상표명", "미기재"),
                "모델및규격": item.get("모델및규격", "미기재"),
                "수량": item.get("수량", "미기재"),
                "단가": item.get("단가", "미기재"),
                "금액": item.get("금액", "미기재"),
                "세번부호": item.get("세번부호", "미기재"),
                "순중량": item.get("순중량", "미기재"),
                "총중량": item.get("총중량", "미기재"),
                "포장개수": item.get("포장개수", "미기재"),
            } for item in final_result.get("품목별 결과", [])
        ]
    }
    return ExportDeclarationResponse(**response_data)

# FastAPI 실행 (개발 서버)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)