"""
Shared utilities for model serving.
"""

import time
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)


def measure_time(func: Callable) -> Callable:
    """Decorator to measure function execution time"""
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Add timing info to result if it's a dict
            if isinstance(result, dict):
                result['processing_time_ms'] = execution_time
            
            logger.info(f"{func.__name__} executed in {execution_time:.2f}ms")
            return result
        except Exception as e:
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000
            logger.error(f"{func.__name__} failed after {execution_time:.2f}ms: {e}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000
            
            if isinstance(result, dict):
                result['processing_time_ms'] = execution_time
            
            logger.info(f"{func.__name__} executed in {execution_time:.2f}ms")
            return result
        except Exception as e:
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000
            logger.error(f"{func.__name__} failed after {execution_time:.2f}ms: {e}")
            raise
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def validate_input_data(data: Dict[str, Any], required_fields: list) -> None:
    """Validate input data contains required fields"""
    
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")


def sanitize_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize input data for security"""
    
    sanitized = {}
    
    for key, value in data.items():
        # Remove potentially dangerous keys
        if key.startswith('_') or key in ['__class__', '__dict__', '__module__']:
            continue
        
        # Sanitize string values
        if isinstance(value, str):
            # Remove null bytes and control characters
            value = value.replace('\x00', '').strip()
            # Limit string length
            if len(value) > 10000:
                value = value[:10000]
        
        sanitized[key] = value
    
    return sanitized


def format_error_response(error: Exception, model_name: str) -> Dict[str, Any]:
    """Format error response for API"""
    
    return {
        "error": {
            "type": type(error).__name__,
            "message": str(error),
            "model_name": model_name
        },
        "status": "error",
        "timestamp": time.time()
    }


class ModelLoader:
    """Base class for model loading and management"""
    
    def __init__(self, model_name: str, model_path: str, config: Optional[Dict[str, Any]] = None):
        self.model_name = model_name
        self.model_path = model_path
        self.config = config or {}
        self.model = None
        self.load_time = None
        self.last_inference_time = None
    
    async def load_model(self):
        """Load the model (to be implemented by subclasses)"""
        start_time = time.time()
        
        # Simulate model loading
        await asyncio.sleep(1.0)
        
        self.load_time = time.time()
        logger.info(f"Model {self.model_name} loaded in {self.load_time - start_time:.2f}s")
    
    def is_ready(self) -> bool:
        """Check if model is ready for inference"""
        return self.model is not None
    
    def get_uptime(self) -> float:
        """Get model uptime in seconds"""
        if self.load_time:
            return time.time() - self.load_time
        return 0.0
    
    async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction (to be implemented by subclasses)"""
        if not self.is_ready():
            raise RuntimeError(f"Model {self.model_name} is not ready")
        
        self.last_inference_time = time.time()
        
        # Base prediction logic
        return {
            "model_name": self.model_name,
            "predictions": {},
            "timestamp": self.last_inference_time
        }


class BatchProcessor:
    """Utility for processing batch requests"""
    
    def __init__(self, max_batch_size: int = 100, max_workers: int = 4):
        self.max_batch_size = max_batch_size
        self.max_workers = max_workers
    
    async def process_batch(
        self,
        inputs: list,
        processor_func: Callable,
        **kwargs
    ) -> Dict[str, Any]:
        """Process a batch of inputs"""
        
        if len(inputs) > self.max_batch_size:
            raise ValueError(f"Batch size {len(inputs)} exceeds maximum {self.max_batch_size}")
        
        start_time = time.perf_counter()
        results = []
        successful_items = 0
        failed_items = 0
        
        # Process in parallel with semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def process_single(index: int, input_data: Dict[str, Any]):
            async with semaphore:
                try:
                    result = await processor_func(input_data, **kwargs)
                    return {"index": index, "result": result, "status": "success"}
                except Exception as e:
                    return {"index": index, "error": str(e), "status": "error"}
        
        # Create tasks for all inputs
        tasks = [
            process_single(i, input_data)
            for i, input_data in enumerate(inputs)
        ]
        
        # Wait for all tasks to complete
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for task_result in task_results:
            if isinstance(task_result, Exception):
                results.append({"error": str(task_result), "status": "error"})
                failed_items += 1
            else:
                results.append(task_result)
                if task_result["status"] == "success":
                    successful_items += 1
                else:
                    failed_items += 1
        
        end_time = time.perf_counter()
        processing_time = (end_time - start_time) * 1000
        
        return {
            "results": results,
            "total_items": len(inputs),
            "successful_items": successful_items,
            "failed_items": failed_items,
            "processing_time_ms": processing_time
        }