"""
Text Extractor Model Serving API

This service provides OCR and text extraction capabilities
for customs clearance documents.
"""

import time
import base64
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from ..shared.app.schemas import (
    InferenceRequest, InferenceResponse, BatchInferenceRequest, 
    BatchInferenceResponse, ModelHealthResponse, ModelStatus
)
from ..shared.app.utils import measure_time, validate_input_data, sanitize_input, ModelLoader

# Model information
MODEL_NAME = "text-extractor"
MODEL_VERSION = "1.0.0"

app = FastAPI(
    title="Text Extractor Model API",
    description="OCR and text extraction model for customs documents",
    version=MODEL_VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Model loader instance
model_loader = None
start_time = time.time()


class TextExtractorLoader(ModelLoader):
    """Text extractor model loader"""
    
    async def load_model(self):
        """Load the text extraction model"""
        await super().load_model()
        
        # In a real implementation, load your OCR model here
        # self.model = load_ocr_model(self.model_path)
        self.model = {"status": "loaded", "type": "text_extractor"}
    
    @measure_time
    async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text from document"""
        
        # Validate inputs
        required_fields = ["image_data"]  # Base64 encoded image or image_url
        if "image_url" not in inputs:
            validate_input_data(inputs, required_fields)
        
        inputs = sanitize_input(inputs)
        
        # Update last inference time
        self.last_inference_time = time.time()
        
        # Extract parameters
        language = inputs.get("language", "ko")
        confidence_threshold = inputs.get("confidence_threshold", 0.8)
        extract_tables = inputs.get("extract_tables", False)
        
        # Mock text extraction - replace with actual OCR
        extracted_text, word_confidences, tables = self._extract_text(
            inputs, language, confidence_threshold, extract_tables
        )
        
        return {
            "model_name": self.model_name,
            "model_version": MODEL_VERSION,
            "predictions": {
                "extracted_text": extracted_text,
                "language": language,
                "word_count": len(extracted_text.split()),
                "average_confidence": sum(word_confidences) / len(word_confidences) if word_confidences else 0,
                "word_confidences": word_confidences,
                "tables": tables if extract_tables else [],
                "text_regions": self._get_text_regions()
            },
            "metadata": {
                "confidence_threshold": confidence_threshold,
                "extract_tables": extract_tables,
                "processing_language": language
            }
        }
    
    def _extract_text(self, inputs: Dict[str, Any], language: str, 
                     confidence_threshold: float, extract_tables: bool) -> tuple:
        """Mock text extraction function"""
        
        # Simulate OCR results based on input type
        if "image_url" in inputs:
            # Mock text for image URL
            extracted_text = """
            상업송장 (COMMERCIAL INVOICE)
            
            발행자: ABC Trading Co., Ltd.
            주소: 123 Main St, Seoul, Korea
            전화: +82-2-1234-5678
            
            수취인: XYZ Import Corporation
            주소: 456 Oak Avenue, Busan, Korea
            
            송장번호: INV-2024-001
            발행일자: 2024년 1월 15일
            
            품목명: 전자부품 (Electronic Components)
            수량: 100개
            단가: $150.00
            총액: $15,000.00
            
            HS코드: 8541.10.00
            원산지: 대한민국
            """
        else:
            # Mock text for base64 image data
            extracted_text = """
            포장명세서 (PACKING LIST)
            
            포장일자: 2024년 1월 14일
            총 포장수: 5박스
            총 중량: 250.5kg
            
            박스 1: 전자부품, 50.1kg, 40x30x20cm
            박스 2: 전자부품, 50.2kg, 40x30x20cm
            박스 3: 전자부품, 50.0kg, 40x30x20cm
            박스 4: 전자부품, 50.1kg, 40x30x20cm
            박스 5: 전자부품, 50.1kg, 40x30x20cm
            """
        
        # Mock word confidences
        words = extracted_text.split()
        word_confidences = [0.95 - (i % 10) * 0.02 for i in range(len(words))]
        
        # Mock table extraction
        tables = []
        if extract_tables:
            tables = [
                {
                    "table_id": 1,
                    "rows": 5,
                    "columns": 4,
                    "data": [
                        ["품목", "수량", "단가", "금액"],
                        ["전자부품", "100", "$150.00", "$15,000.00"],
                        ["포장비", "1", "$50.00", "$50.00"],
                        ["운송비", "1", "$100.00", "$100.00"],
                        ["총계", "", "", "$15,150.00"]
                    ],
                    "confidence": 0.92
                }
            ]
        
        return extracted_text.strip(), word_confidences, tables
    
    def _get_text_regions(self) -> List[Dict[str, Any]]:
        """Mock text region detection"""
        return [
            {
                "region_id": 1,
                "text": "상업송장 (COMMERCIAL INVOICE)",
                "bbox": [100, 50, 400, 80],
                "confidence": 0.95,
                "type": "title"
            },
            {
                "region_id": 2,
                "text": "발행자: ABC Trading Co., Ltd.",
                "bbox": [100, 100, 300, 120],
                "confidence": 0.92,
                "type": "text"
            },
            {
                "region_id": 3,
                "text": "총액: $15,000.00",
                "bbox": [300, 400, 450, 420],
                "confidence": 0.98,
                "type": "amount"
            }
        ]


@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    global model_loader
    
    model_loader = TextExtractorLoader(
        model_name=MODEL_NAME,
        model_path="./models/text-extractor",
        config={"confidence_threshold": 0.8}
    )
    
    await model_loader.load_model()


@app.get("/health", response_model=ModelHealthResponse)
async def health_check():
    """Health check endpoint"""
    
    if not model_loader:
        return ModelHealthResponse(
            model_name=MODEL_NAME,
            status=ModelStatus.ERROR,
            version=MODEL_VERSION,
            uptime_seconds=time.time() - start_time,
            error_message="Model not initialized"
        )
    
    return ModelHealthResponse(
        model_name=MODEL_NAME,
        status=ModelStatus.READY if model_loader.is_ready() else ModelStatus.ERROR,
        version=MODEL_VERSION,
        uptime_seconds=model_loader.get_uptime(),
        last_inference=model_loader.last_inference_time,
        metadata={
            "model_path": model_loader.model_path,
            "supported_languages": ["ko", "en", "ja", "zh"],
            "supported_formats": ["jpg", "jpeg", "png", "pdf"],
            "features": ["ocr", "table_extraction", "text_regions", "confidence_scores"]
        }
    )


@app.post("/predict", response_model=InferenceResponse)
async def predict(request: InferenceRequest):
    """Extract text from document image"""
    
    if not model_loader or not model_loader.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not ready"
        )
    
    try:
        result = await model_loader.predict(request.inputs)
        
        return InferenceResponse(
            model_name=result["model_name"],
            model_version=result["model_version"],
            predictions=result["predictions"],
            metadata=result.get("metadata", {}),
            processing_time_ms=result.get("processing_time_ms")
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text extraction failed: {str(e)}"
        )


@app.post("/batch-predict", response_model=BatchInferenceResponse)
async def batch_predict(request: BatchInferenceRequest):
    """Batch text extraction"""
    
    if not model_loader or not model_loader.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not ready"
        )
    
    try:
        from ..shared.app.utils import BatchProcessor
        
        processor = BatchProcessor(max_batch_size=50, max_workers=2)  # OCR is CPU intensive
        
        async def process_single(input_data: Dict[str, Any]):
            return await model_loader.predict(input_data)
        
        batch_result = await processor.process_batch(
            request.inputs,
            process_single
        )
        
        return BatchInferenceResponse(
            model_name=MODEL_NAME,
            model_version=MODEL_VERSION,
            results=batch_result["results"],
            total_items=batch_result["total_items"],
            successful_items=batch_result["successful_items"],
            failed_items=batch_result["failed_items"],
            processing_time_ms=batch_result["processing_time_ms"]
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch text extraction failed: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "model_name": MODEL_NAME,
        "version": MODEL_VERSION,
        "description": "OCR and text extraction model for customs documents",
        "supported_languages": ["ko", "en", "ja", "zh"],
        "supported_formats": ["jpg", "jpeg", "png", "pdf"],
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "batch_predict": "/batch-predict"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)