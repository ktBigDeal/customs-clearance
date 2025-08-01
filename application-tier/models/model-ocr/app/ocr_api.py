import os
import json
from fastapi import FastAPI, File, UploadFile, HTTPException
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# --- 환경 변수 로딩 ---
load_dotenv(dotenv_path="../api_key.env")

# --- 필드 파싱 ---
def parse_field(field):
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
    poller = client.begin_analyze_document(model_id, document=file_bytes)
    result = poller.result()

    doc = result.documents[0]
    fields = doc.fields
    return {name: parse_field(field) for name, field in fields.items()}

# --- JSON 병합 ---
def merge_jsons(invoice, packing_list1, packing_list2, bill_of_lading):
    merged = {
        "invoice_number": invoice.get("invoice_number", ""),
        "country_export": invoice.get("country_export", ""),
        "country_import": invoice.get("county_import", ""),
        "shipper": invoice.get("shipper", ""),
        "importer": invoice.get("importer", ""),
        "buyer": invoice.get("buyer", ""),
        "total_amount": invoice.get("total_amount", ""),
        "items": [],
        "gross_weight": packing_list1.get("gross_weight", ""),
        "net_weight": packing_list1.get("net_weight", ""),
        "total_packages": packing_list1.get("total_packages", ""),
        "bill_number": bill_of_lading.get("bill_number", ""),
        "port_departure": bill_of_lading.get("port_departure", ""),
        "port_destination": bill_of_lading.get("port_destination", ""),
        "vessel_name": bill_of_lading.get("vessel_name", ""),
        "vessel_nationality": bill_of_lading.get("vessel_nationality", "")
    }

    invoice_items = invoice.get("items", [])
    packing_items = packing_list2.get("items", [])

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

# --- API 엔드포인트 ---
@app.post("/ocr/")
async def analyze_docs(
    invoice_file: UploadFile = File(...),
    packing_list_file: UploadFile = File(...),
    bill_of_lading_file: UploadFile = File(...)
):
    try:
        invoice_bytes = await invoice_file.read()
        packing_bytes = await packing_list_file.read()
        bill_bytes = await bill_of_lading_file.read()

        json_invoice = analyze_document_to_json(client, "model-invoice", invoice_bytes)
        json_packing_list1 = analyze_document_to_json(client, "model-packing_list", packing_bytes)
        json_packing_list2 = analyze_document_to_json(client, "model-packing_list_2", packing_bytes)
        json_bill_of_lading = analyze_document_to_json(client, "model-bill_of_lading", bill_bytes)

        merged_json = merge_jsons(json_invoice, json_packing_list1, json_packing_list2, json_bill_of_lading)
        return merged_json

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
