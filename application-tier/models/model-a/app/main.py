"""
Document Classifier Model Serving API

This service provides document classification capabilities
for customs clearance documents.
"""

import time
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from ..shared.app.schemas import (
    InferenceRequest, InferenceResponse, BatchInferenceRequest, 
    BatchInferenceResponse, ModelHealthResponse, ModelStatus
)
from ..shared.app.utils import measure_time, validate_input_data, sanitize_input, ModelLoader

# Model information
MODEL_NAME = "document-classifier"
MODEL_VERSION = "1.0.0"

app = FastAPI(
    title="Document Classifier Model API",
    description="Document classification model for customs clearance",
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


class DocumentClassifierLoader(ModelLoader):
    """Document classifier model loader"""
    
    async def load_model(self):
        """Load the document classification model"""
        await super().load_model()
        
        # In a real implementation, load your actual model here
        # self.model = load_your_model(self.model_path)
        self.model = {"status": "loaded", "type": "document_classifier"}
    
    @measure_time
    async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Classify document type"""
        
        # Validate inputs
        validate_input_data(inputs, ["document_content"])
        inputs = sanitize_input(inputs)
        
        # Update last inference time
        self.last_inference_time = time.time()
        
        # Mock classification logic - replace with actual model inference
        document_content = inputs.get("document_content", "")
        confidence_threshold = inputs.get("confidence_threshold", 0.5)
        
        # Simulate classification
        predictions = self._classify_document(document_content)
        
        # Filter by confidence threshold
        filtered_predictions = {
            k: v for k, v in predictions.items() 
            if v >= confidence_threshold
        }
        
        return {
            "model_name": self.model_name,
            "model_version": MODEL_VERSION,
            "predictions": {
                "document_type": max(predictions.keys(), key=predictions.get),
                "confidence_scores": predictions,
                "filtered_predictions": filtered_predictions
            },
            "metadata": {
                "confidence_threshold": confidence_threshold,
                "total_classes": len(predictions)
            }
        }
    
    def _classify_document(self, content: str) -> Dict[str, float]:
        """Mock document classification"""
        
        # Simple keyword-based classification for demo
        content_lower = content.lower()
        
        scores = {
            "invoice": 0.1,
            "packing_list": 0.1,
            "bill_of_lading": 0.1,
            "certificate_of_origin": 0.1,
            "customs_declaration": 0.1,
            "other": 0.1
        }
        
        # Update scores based on keywords
        if any(word in content_lower for word in ["invoice", "bill", "payment", "amount"]):
            scores["invoice"] = 0.85
        elif any(word in content_lower for word in ["packing", "package", "weight", "dimensions"]):
            scores["packing_list"] = 0.82
        elif any(word in content_lower for word in ["lading", "shipping", "vessel", "cargo"]):
            scores["bill_of_lading"] = 0.88
        elif any(word in content_lower for word in ["origin", "certificate", "country"]):
            scores["certificate_of_origin"] = 0.79
        elif any(word in content_lower for word in ["declaration", "customs", "duty", "tariff"]):
            scores["customs_declaration"] = 0.91
        else:
            scores["other"] = 0.75
        
        # Normalize scores
        total = sum(scores.values())
        normalized_scores = {k: v/total for k, v in scores.items()}
        
        return normalized_scores


@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    global model_loader
    
    model_loader = DocumentClassifierLoader(
        model_name=MODEL_NAME,
        model_path="./models/document-classifier",
        config={"confidence_threshold": 0.5}
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
            "supported_document_types": [
                "invoice", "packing_list", "bill_of_lading", 
                "certificate_of_origin", "customs_declaration", "other"
            ]
        }
    )


@app.post("/predict", response_model=InferenceResponse)
async def predict(request: InferenceRequest):
    """Classify document type"""
    
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
            detail=f"Prediction failed: {str(e)}"
        )


@app.post("/batch-predict", response_model=BatchInferenceResponse)
async def batch_predict(request: BatchInferenceRequest):
    """Batch document classification"""
    
    if not model_loader or not model_loader.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not ready"
        )
    
    try:
        from ..shared.app.utils import BatchProcessor
        
        processor = BatchProcessor(max_batch_size=100, max_workers=4)
        
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
            detail=f"Batch prediction failed: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "model_name": MODEL_NAME,
        "version": MODEL_VERSION,
        "description": "Document classification model for customs clearance",
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "batch_predict": "/batch-predict"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)