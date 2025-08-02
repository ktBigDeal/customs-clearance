# 🔧 Application Tier CURL 테스트 가이드

AI Gateway와 모델 서비스들을 curl로 테스트하는 완전한 가이드입니다.

## 🚀 서비스 시작 순서

### 1단계: AI Gateway 시작
```bash
cd application-tier/ai-gateway
source .venv/Scripts/activate
python main.py
```

### 2단계: OCR 모델 시작 (별도 터미널)
```bash
cd application-tier/models/model-ocr
source .venv/Scripts/activate
python -m uvicorn app.ocr_api:app --host 127.0.0.1 --port 8001
```

### 3단계: Report 모델 시작 (별도 터미널)
```bash
cd application-tier/models/model-report
source .venv/Scripts/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002  
```

## 📋 CURL 테스트 명령어들

### 기본 연결 테스트

#### AI Gateway 루트 확인
```bash
curl -X GET http://localhost:8000/ \
  -H "Content-Type: application/json"
```

**예상 응답:**
```json
{
  "service": "Customs Clearance AI Gateway",
  "version": "1.0.0", 
  "status": "running",
  "environment": "development"
}
```

#### 서비스 헬스 체크
```bash
curl -X GET http://localhost:8000/api/v1/pipeline/health/services \
  -H "Content-Type: application/json"
```

**예상 응답:**
```json
{
  "overall_status": "healthy",
  "services": {
    "model-ocr": {
      "status": "healthy",
      "url": "http://localhost:8001",
      "response_time": "12ms"
    },
    "model-report": {
      "status": "healthy", 
      "url": "http://localhost:8002",
      "response_time": "8ms"
    }
  }
}
```

### OCR 서비스 테스트

#### 샘플 파일 생성
```bash
# 테스트용 더미 PDF 생성
echo "Invoice Data - INV-2024-001" > sample_invoice.txt
echo "Packing List Data" > sample_packing_list.txt  
echo "Bill of Lading Data" > sample_bill_of_lading.txt
```

#### OCR 문서 분석
```bash
curl -X POST http://localhost:8000/api/v1/ocr/analyze-documents \
  -F "invoice_file=@sample_invoice.txt" \
  -F "packing_list_file=@sample_packing_list.txt" \
  -F "bill_of_lading_file=@sample_bill_of_lading.txt"
```

**예상 응답:**
```json
{
  "status": "success",
  "message": "Documents analyzed successfully",
  "ocr_data": {
    "invoice_number": "INV-2024-001",
    "country_export": "Korea",
    "country_import": "USA",
    "shipper": "ABC Trading Co.",
    "importer": "XYZ Corp",
    "total_amount": "15000.00",
    "items": [
      {
        "item_name": "Electronics",
        "quantity": "100",
        "unit_price": "150.00", 
        "hs_code": "8541.10"
      }
    ]
  },
  "processing_time": "2.5s"
}
```

### Report 생성 서비스 테스트

#### 수입 신고서 생성
```bash
curl -X POST http://localhost:8000/api/v1/report/generate-import-declaration \
  -H "Content-Type: application/json" \
  -d '{
    "ocr_data": {
      "invoice_number": "INV-2024-001",
      "country_export": "Korea", 
      "country_import": "USA",
      "shipper": "ABC Trading Co.",
      "importer": "XYZ Corp",
      "total_amount": "15000.00",
      "items": [
        {
          "item_name": "Electronics",
          "quantity": "100",
          "unit_price": "150.00",
          "hs_code": "8541.10"
        }
      ]
    },
    "hsk_data": {
      "hsk_code": "8541.10-0000",
      "description": "Electronic components"
    },
    "declaration_type": "import"
  }'
```

**예상 응답:**
```json
{
  "status": "success",
  "message": "Import declaration generated successfully",
  "declaration": {
    "declaration_id": "DECL-IMP-2024-001",
    "declaration_type": "import",
    "shipper": "ABC Trading Co.",
    "importer": "XYZ Corp",
    "total_amount": "15000.00",
    "applicable_taxes": {
      "import_duty": "1500.00",
      "vat": "1650.00",
      "total_tax": "3150.00"
    }
  },
  "processing_time": "5.2s"
}
```

### 완전한 워크플로우 테스트

#### OCR → 신고서 생성 파이프라인
```bash
curl -X POST http://localhost:8000/api/v1/pipeline/process-complete-workflow \
  -F "declaration_type=import" \
  -F "hsk_data={\"hsk_code\": \"8541.10-0000\", \"description\": \"Electronic components\"}" \
  -F "invoice_file=@sample_invoice.txt" \
  -F "packing_list_file=@sample_packing_list.txt" \
  -F "bill_of_lading_file=@sample_bill_of_lading.txt"
```

**예상 응답:**
```json
{
  "status": "success",
  "message": "Complete workflow processed successfully",
  "workflow_id": "workflow_1704067200.123",
  "declaration_type": "import",
  "pipeline_results": {
    "step_1_ocr": {
      "status": "completed",
      "processing_time": "2.5s",
      "data": {
        "invoice_number": "INV-2024-001",
        "total_amount": "15000.00"
      }
    },
    "step_2_declaration": {
      "status": "completed",
      "processing_time": "5.2s", 
      "data": {
        "declaration_id": "DECL-IMP-2024-001",
        "applicable_taxes": {
          "total_tax": "3150.00"
        }
      }
    }
  },
  "summary": {
    "invoice_number": "INV-2024-001",
    "total_amount": "15000.00",
    "shipper": "ABC Trading Co.",
    "importer": "XYZ Corp",
    "items_count": 1,
    "declaration_type": "import",
    "total_tax": "3150.00"
  },
  "processing_time": "7.8s"
}
```

## 🔍 개별 서비스 직접 테스트

### OCR 서비스 (Port 8001)
```bash
# OCR 서비스 헬스 체크
curl -X GET http://localhost:8001/docs

# OCR 직접 호출
curl -X POST http://localhost:8001/ocr/ \
  -F "invoice_file=@sample_invoice.txt" \
  -F "packing_list_file=@sample_packing_list.txt" \
  -F "bill_of_lading_file=@sample_bill_of_lading.txt"
```

### Report 서비스 (Port 8002)
```bash
# Report 서비스 헬스 체크  
curl -X GET http://localhost:8002/docs

# Report 직접 호출
curl -X POST http://localhost:8002/generate-import-declaration \
  -H "Content-Type: application/json" \
  -d '{
    "ocr_data": {...},
    "hsk_data": {...}
  }'
```

## 🚨 트러블슈팅

### 연결 실패 시
```bash
# 포트 확인
netstat -an | findstr :800

# 프로세스 확인  
tasklist | findstr python
```

### 서비스 중지
```bash
# Windows에서 프로세스 종료
taskkill /f /im python.exe
```

### 로그 확인
각 서비스 터미널에서 실시간 로그를 확인할 수 있습니다.

## 📊 성능 벤치마크

### 응답 시간 측정
```bash
# 시간 측정과 함께 요청
curl -w "@curl-format.txt" -X GET http://localhost:8000/
```

**curl-format.txt 파일 생성:**
```
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
```

### 부하 테스트 (간단)
```bash
# 10회 연속 요청
for i in {1..10}; do
  curl -X GET http://localhost:8000/health
  echo "Request $i completed"
done
```

## 🔄 자동화 스크립트

### 모든 테스트 실행
```bash
#!/bin/bash
echo "🧪 Starting comprehensive curl tests..."

echo "1. Testing AI Gateway root..."
curl -X GET http://localhost:8000/

echo -e "\n2. Testing health check..."
curl -X GET http://localhost:8000/api/v1/pipeline/health/services

echo -e "\n3. Testing OCR..."
curl -X POST http://localhost:8000/api/v1/ocr/analyze-documents \
  -F "invoice_file=@sample_invoice.txt" \
  -F "packing_list_file=@sample_packing_list.txt" \
  -F "bill_of_lading_file=@sample_bill_of_lading.txt"

echo -e "\n4. Testing complete workflow..."
curl -X POST http://localhost:8000/api/v1/pipeline/process-complete-workflow \
  -F "declaration_type=import" \
  -F "invoice_file=@sample_invoice.txt" \
  -F "packing_list_file=@sample_packing_list.txt" \
  -F "bill_of_lading_file=@sample_bill_of_lading.txt"

echo -e "\n✅ All tests completed!"
```

이제 curl로 완전한 통합 테스트가 가능합니다!