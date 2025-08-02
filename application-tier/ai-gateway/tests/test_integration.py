"""
Integration tests for AI Gateway with model services
"""
import pytest
import asyncio
import io
from unittest.mock import patch, AsyncMock
from fastapi import status
from httpx import AsyncClient
import httpx
from aioresponses import aioresponses

from app.routers.ai_gateway import get_spring_boot_client


class TestModelOcrIntegration:
    """Integration tests with model-ocr service"""
    
    @pytest.mark.integration
    async def test_gateway_to_ocr_service_success(
        self,
        async_client,
        mock_model_ocr_response
    ):
        """Test successful integration with model-ocr service"""
        with aioresponses() as mock_http:
            # Mock model-ocr service response
            mock_http.post(
                "http://localhost:8001/ocr/",
                payload=mock_model_ocr_response,
                status=200
            )
            
            # Mock gateway endpoints that would call model-ocr
            with patch('app.routers.ai_gateway._process_document_workflow') as mock_workflow:
                mock_workflow.return_value = mock_model_ocr_response
                
                request_data = {
                    "document_id": "test-doc-001",
                    "document_type": "invoice",
                    "document_data": {
                        "file_name": "test.pdf",
                        "file_size": 1024
                    }
                }
                
                response = await async_client.post(
                    "/api/v1/gateway/process-document",
                    json=request_data
                )
                
                assert response.status_code == status.HTTP_200_OK
                result = response.json()
                
                assert result["status"] == "SUCCESS"
                assert result["document_id"] == "test-doc-001"
                assert result["processing_status"] == "COMPLETED"
                assert "extracted_data" in result
    
    @pytest.mark.integration
    async def test_gateway_to_ocr_service_failure(self, async_client):
        """Test integration failure with model-ocr service"""
        with aioresponses() as mock_http:
            # Mock model-ocr service failure
            mock_http.post(
                "http://localhost:8001/ocr/",
                status=500,
                payload={"detail": "OCR service error"}
            )
            
            with patch('app.routers.ai_gateway._process_document_workflow') as mock_workflow:
                mock_workflow.side_effect = Exception("OCR service unavailable")
                
                request_data = {
                    "document_id": "test-doc-001",
                    "document_type": "invoice",
                    "document_data": {
                        "file_name": "test.pdf",
                        "file_size": 1024
                    }
                }
                
                response = await async_client.post(
                    "/api/v1/gateway/process-document",
                    json=request_data
                )
                
                assert response.status_code == status.HTTP_200_OK
                result = response.json()
                
                assert result["status"] == "ERROR"
                assert result["processing_status"] == "ERROR"
                assert len(result["errors"]) > 0


class TestModelReportIntegration:
    """Integration tests with model-report service"""
    
    @pytest.mark.integration
    async def test_gateway_to_report_service_success(
        self,
        async_client,
        mock_model_report_response
    ):
        """Test successful integration with model-report service"""
        with aioresponses() as mock_http:
            # Mock model-report service response
            mock_http.post(
                "http://localhost:8002/generate-customs-declaration",
                payload=mock_model_report_response,
                status=200
            )
            
            # This would be a new endpoint that integrates with model-report
            # For now, we'll test the concept through process-document
            with patch('app.routers.ai_gateway._process_document_workflow') as mock_workflow:
                # Simulate a workflow that calls model-report
                mock_workflow.return_value = mock_model_report_response
                
                request_data = {
                    "document_id": "test-decl-001",
                    "document_type": "customs_declaration",
                    "document_data": {
                        "ocr_data": {
                            "invoice_number": "INV-2024-001",
                            "total_amount": "15000.00"
                        },
                        "hsk_data": {
                            "hsk_code": "8541.10-0000"
                        }
                    }
                }
                
                response = await async_client.post(
                    "/api/v1/gateway/process-document",
                    json=request_data
                )
                
                assert response.status_code == status.HTTP_200_OK
                result = response.json()
                
                assert result["status"] == "SUCCESS"
                assert result["processing_status"] == "COMPLETED"
    
    @pytest.mark.integration
    async def test_gateway_to_report_service_failure(self, async_client):
        """Test integration failure with model-report service"""
        with aioresponses() as mock_http:
            # Mock model-report service failure
            mock_http.post(
                "http://localhost:8002/generate-customs-declaration",
                status=500,
                payload={"detail": "Report generation failed"}
            )
            
            with patch('app.routers.ai_gateway._process_document_workflow') as mock_workflow:
                mock_workflow.side_effect = Exception("Report service unavailable")
                
                request_data = {
                    "document_id": "test-decl-001",
                    "document_type": "customs_declaration",
                    "document_data": {}
                }
                
                response = await async_client.post(
                    "/api/v1/gateway/process-document",
                    json=request_data
                )
                
                assert response.status_code == status.HTTP_200_OK
                result = response.json()
                
                assert result["status"] == "ERROR"
                assert len(result["errors"]) > 0


class TestEndToEndWorkflow:
    """End-to-end workflow tests"""
    
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_full_document_processing_workflow(
        self,
        async_client,
        mock_model_ocr_response,
        mock_model_report_response
    ):
        """Test complete document processing workflow"""
        with aioresponses() as mock_http:
            # Mock OCR service
            mock_http.post(
                "http://localhost:8001/ocr/",
                payload=mock_model_ocr_response,
                status=200
            )
            
            # Mock report service  
            mock_http.post(
                "http://localhost:8002/generate-customs-declaration",
                payload=mock_model_report_response,
                status=200
            )
            
            # Mock Spring Boot backend notification
            mock_http.post(
                "http://localhost:8080/api/v1/documents/ai-processed",
                payload={"status": "received"},
                status=200
            )
            
            # Test the workflow
            with patch('app.routers.ai_gateway._process_document_workflow') as mock_workflow:
                # Simulate calling both OCR and report services
                mock_workflow.return_value = {
                    "ocr_result": mock_model_ocr_response,
                    "declaration_result": mock_model_report_response,
                    "processing_time": 5.2,
                    "confidence": 0.89
                }
                
                request_data = {
                    "document_id": "e2e-test-001",
                    "document_type": "invoice",
                    "document_data": {
                        "files": ["invoice.pdf", "packing.pdf", "bill.pdf"]
                    },
                    "processing_options": {
                        "extract_fields": True,
                        "generate_declaration": True,
                        "notify_backend": True
                    }
                }
                
                response = await async_client.post(
                    "/api/v1/gateway/process-document",
                    json=request_data
                )
                
                assert response.status_code == status.HTTP_200_OK
                result = response.json()
                
                assert result["status"] == "SUCCESS"
                assert result["processing_status"] == "COMPLETED"
                assert result["document_id"] == "e2e-test-001"
                assert "extracted_data" in result
                assert result["confidence_score"] > 0.8
    
    @pytest.mark.e2e
    async def test_risk_assessment_workflow(
        self,
        async_client,
        sample_risk_assessment_request
    ):
        """Test risk assessment workflow"""
        response = await async_client.post(
            "/api/v1/gateway/assess-risk",
            json=sample_risk_assessment_request
        )
        
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        
        assert result["status"] == "SUCCESS"
        assert result["declaration_id"] == "decl-001"
        assert "overall_risk_level" in result
        assert "risk_factors" in result
        assert "recommendations" in result
        assert isinstance(result["requires_inspection"], bool)
    
    @pytest.mark.e2e
    async def test_validation_workflow(
        self,
        async_client,
        sample_validation_request
    ):
        """Test validation workflow"""
        response = await async_client.post(
            "/api/v1/gateway/validate",
            json=sample_validation_request
        )
        
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        
        assert result["status"] == "SUCCESS"
        assert "is_valid" in result
        assert "validation_errors" in result
        assert "warnings" in result


class TestSpringBootIntegration:
    """Integration tests with Spring Boot backend"""
    
    @pytest.mark.integration
    async def test_spring_boot_notification_success(self, mock_spring_boot_client):
        """Test successful notification to Spring Boot backend"""
        with patch('app.routers.ai_gateway.get_spring_boot_client') as mock_get_client:
            mock_get_client.return_value.__aenter__.return_value = mock_spring_boot_client
            
            # Import the function to test
            from app.routers.ai_gateway import _notify_spring_boot_backend
            
            await _notify_spring_boot_backend(
                "test-doc-001",
                {"extracted": "data"}
            )
            
            mock_spring_boot_client.post.assert_called_once()
            call_args = mock_spring_boot_client.post.call_args
            
            assert "/api/v1/documents/ai-processed" in call_args[0][0]
            assert "document_id" in call_args[1]["json"]
            assert call_args[1]["json"]["document_id"] == "test-doc-001"
    
    @pytest.mark.integration
    async def test_spring_boot_notification_failure(self):
        """Test handling of Spring Boot notification failure"""
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_client.post.return_value = mock_response
        
        with patch('app.routers.ai_gateway.get_spring_boot_client') as mock_get_client:
            mock_get_client.return_value.__aenter__.return_value = mock_client
            
            from app.routers.ai_gateway import _notify_spring_boot_backend
            
            # Should not raise exception, just log warning
            await _notify_spring_boot_backend(
                "test-doc-001",
                {"extracted": "data"}
            )
            
            mock_client.post.assert_called_once()


class TestErrorHandlingAndResilience:
    """Test error handling and service resilience"""
    
    @pytest.mark.integration
    async def test_circuit_breaker_pattern(self, async_client):
        """Test circuit breaker pattern for service failures"""
        # This would test implementing circuit breaker pattern
        # for when model services are repeatedly failing
        pass
    
    @pytest.mark.integration
    async def test_timeout_handling(self, async_client):
        """Test timeout handling for slow model services"""
        with patch('app.routers.ai_gateway._process_document_workflow') as mock_workflow:
            # Simulate slow response
            async def slow_response(*args, **kwargs):
                await asyncio.sleep(10)  # Longer than typical timeout
                return {"result": "data"}
            
            mock_workflow.side_effect = slow_response
            
            request_data = {
                "document_id": "timeout-test",
                "document_type": "invoice",
                "document_data": {}
            }
            
            # This should timeout and handle gracefully
            response = await async_client.post(
                "/api/v1/gateway/process-document",
                json=request_data
            )
            
            # Should still return a response, not hang
            assert response.status_code in [200, 500, 504]
    
    @pytest.mark.integration
    async def test_retry_mechanism(self, async_client):
        """Test retry mechanism for transient failures"""
        call_count = 0
        
        def failing_then_success(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Transient error")
            return {"result": "success"}
        
        with patch('app.routers.ai_gateway._process_document_workflow') as mock_workflow:
            mock_workflow.side_effect = failing_then_success
            
            request_data = {
                "document_id": "retry-test",
                "document_type": "invoice", 
                "document_data": {}
            }
            
            response = await async_client.post(
                "/api/v1/gateway/process-document",
                json=request_data
            )
            
            # Should eventually succeed after retries
            assert response.status_code == status.HTTP_200_OK
            result = response.json()
            assert result["status"] == "SUCCESS"