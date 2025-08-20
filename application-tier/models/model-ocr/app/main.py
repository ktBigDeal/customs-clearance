"""
Azure Document Intelligence 기반 OCR API 서비스

이 모듈은 관세 문서 3종(Invoice, Packing List, Bill of Lading)에 대해
Azure Document Intelligence를 사용하여 OCR 처리를 수행하고 구조화된 데이터를 추출합니다.
"""

import asyncio
import os
import json
from fastapi import FastAPI, File, UploadFile, HTTPException
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

# --- 환경 변수 로딩 ---
env_path = Path(__file__).parent.parent / '.env'

# 절대 경로를 사용해 .env 파일 로드
load_dotenv(dotenv_path=env_path)
load_dotenv(dotenv_path="../.env")

# --- 필드 파싱 ---
def parse_field(field):
    """
    Azure Document Intelligence 필드 데이터 파싱
    
    Azure Document Intelligence에서 반환된 필드 데이터를 
    Python 객체로 변환하는 함수입니다.
    
    Args:
        field: Azure Document Intelligence 필드 객체
        
    Returns:
        변환된 Python 객체 (문자열, 숫자, 리스트, 사전 등)
    """
    if field is None:
        return None

    vt = field.value_type

    if vt in ["string", "number", "integer", "boolean"]:
        return field.value
    elif vt in ["date", "time"]:
        return str(field.value)
    elif vt in ["array", "list"]:
        return [parse_field(item) for item in field.value]
    elif vt in ["dictionary", "object"]:
        return {k: parse_field(v) for k, v in field.value.items()}
    else:
        return None

# --- 문서 분석 ---
def analyze_document_to_json(client, model_id, file_bytes: bytes):
    """
    문서를 분석하여 JSON 형태로 변환
    
    Azure Document Intelligence를 사용하여 문서를 분석하고
    추출된 필드 데이터를 JSON 형태로 변환합니다.
    
    Args:
        client: Azure Document Intelligence 클라이언트
        model_id (str): 사용할 모델 ID
        file_bytes (bytes): 분석할 문서 파일 바이트
        
    Returns:
        dict: 추출된 필드 데이터를 포함하는 딕셔너리
    """
    poller = client.begin_analyze_document(model_id, document=file_bytes)
    result = poller.result()

    doc = result.documents[0]
    fields = doc.fields
    return {name: parse_field(field) for name, field in fields.items()}

# --- JSON 병합 ---
def merge_jsons(invoice, packing_list, bill_of_lading):
    """
    여러 문서에서 추출된 데이터를 통합
    
    Invoice, Packing List, Bill of Lading에서 추출된 데이터를
    하나의 통합된 JSON 객체로 병합합니다.
    
    Args:
        invoice (dict): 인보이스에서 추출된 데이터
        packing_list1 (dict): 첫 번째 포장 명세서 데이터
        packing_list2 (dict): 두 번째 포장 명세서 데이터
        bill_of_lading (dict): 선하증권에서 추출된 데이터
        
    Returns:
        dict: 병합된 데이터를 포함하는 딕셔너리
    """
    merged = {
        "invoice_number": invoice.get("invoice_number", ""),
        "country_export": invoice.get("country_export", ""),
        "country_import": invoice.get("county_import", ""),
        "shipper": invoice.get("shipper", ""),
        "importer": invoice.get("importer", ""),
        "buyer": invoice.get("buyer", ""),
        "total_amount": invoice.get("total_amount", ""),
        "items": [],
        "gross_weight": packing_list.get("gross_weight", ""),
        "net_weight": packing_list.get("net_weight", ""),
        "total_packages": packing_list.get("total_packages", ""),
        "bill_number": bill_of_lading.get("bill_number", ""),
        "port_departure": bill_of_lading.get("port_departure", ""),
        "port_destination": bill_of_lading.get("port_destination", ""),
        "vessel_name": bill_of_lading.get("vessel_name", ""),
        "vessel_nationality": bill_of_lading.get("vessel_nationality", "")
    }

    invoice_items = invoice.get("items", [])
    packing_items = packing_list.get("items", [])

    for i in range(len(invoice_items)):
        invoice_item = invoice_items[i]
        packing_item = packing_items[i] if i < len(packing_items) else {}

        merged_item = {
            "item_name": invoice_item.get("item_name", ""),
            "quantity": invoice_item.get("quantity", ""),
            "unit": invoice_item.get("unit", ""),
            "unit_price": invoice_item.get("unit_price", ""),
            "amount": invoice_item.get("amount", ""),
            "hs_code": invoice_item.get("hs_code", ""),
            "gross_weight": packing_item.get("gross_weight", ""),
            "net_weight": packing_item.get("net_weight", ""),
            "total_package": packing_item.get("total_package", "")
        }

        merged["items"].append(merged_item)

    return merged

# --- FastAPI 앱 정의 ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 환경 변수에서 직접 읽기
endpoint = os.getenv("AZURE_ENDPOINT")
key = os.getenv("AZURE_API_KEY")
client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

# 전역 executor 정의
executor = ThreadPoolExecutor()

# --- API 엔드포인트 ---
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {"message": "OCR Service is running", "service": "model-ocr"}

@app.get("/health")
async def health():
    """헬스체크 엔드포인트"""
    return {"status": "healthy", "service": "model-ocr"}

@app.post("/ocr/")
async def analyze_docs(
    invoice_file: Optional[UploadFile] = File(None),
    packing_list_file: Optional[UploadFile] = File(None),
    bill_of_lading_file: Optional[UploadFile] = File(None),
):
    try:
        # 파일 이름이 empty.png인 경우는 모델 호출 생략
        async def get_bytes_if_not_empty(file: Optional[UploadFile]) -> Optional[bytes]:
            if file and file.filename != "empty.png":
                return await file.read()
            return None
        
        invoice_bytes = await get_bytes_if_not_empty(invoice_file)
        packing_bytes = await get_bytes_if_not_empty(packing_list_file)
        bill_bytes = await get_bytes_if_not_empty(bill_of_lading_file)

        loop = asyncio.get_event_loop()

        # 병렬 분석 실행 (없는 파일은 None 결과 처리)
        tasks = [
            loop.run_in_executor(executor, analyze_document_to_json, client, "model-invoice", invoice_bytes)
            if invoice_bytes else None,
            loop.run_in_executor(executor, analyze_document_to_json, client, "model-packing_list", packing_bytes)
            if packing_bytes else None,
            loop.run_in_executor(executor, analyze_document_to_json, client, "model-bill_of_lading", bill_bytes)
            if bill_bytes else None,
        ]

        # 실행된 태스크만 await
        results = await asyncio.gather(*[t if t else asyncio.sleep(0, result=None) for t in tasks])

        json_invoice, json_packing_list, json_bill_of_lading = results

        # None이면 빈 dict로 처리 (merge_json에서 ""로 들어가게 하려면)
        merged_json = merge_jsons(
            json_invoice or {},
            json_packing_list or {},
            json_bill_of_lading or {}
        )

        return merged_json

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
