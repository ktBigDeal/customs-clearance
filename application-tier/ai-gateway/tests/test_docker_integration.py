"""
Docker-based integration tests for AI Gateway
"""
import pytest
import asyncio
import time
from testcontainers.compose import DockerCompose
from httpx import AsyncClient
import httpx
from pathlib import Path


class TestDockerIntegration:
    """Docker-based integration tests"""
    
    @pytest.mark.docker
    @pytest.mark.slow
    def test_full_stack_with_docker_compose(self):
        """Test full application stack using Docker Compose"""
        # Path to docker-compose file for testing
        compose_path = Path(__file__).parent.parent / "docker-compose.test.yml"
        
        if not compose_path.exists():
            pytest.skip("Docker Compose test file not found")
        
        with DockerCompose(str(compose_path.parent), compose_file_name="docker-compose.test.yml") as compose:
            # Wait for services to be ready
            time.sleep(30)
            
            # Get service URLs  
            gateway_url = compose.get_service_host("ai-gateway", 8000)
            ocr_url = compose.get_service_host("model-ocr", 8001) 
            report_url = compose.get_service_host("model-report", 8002)
            
            # Test service health
            self._test_service_health(f"http://{gateway_url}")
            self._test_service_health(f"http://{ocr_url}")
            self._test_service_health(f"http://{report_url}")
            
            # Test inter-service communication
            self._test_gateway_to_models_communication(
                f"http://{gateway_url}",
                f"http://{ocr_url}",
                f"http://{report_url}"
            )
    
    def _test_service_health(self, base_url: str):
        """Test service health endpoint"""
        try:
            response = httpx.get(f"{base_url}/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
        except Exception as e:
            pytest.fail(f"Health check failed for {base_url}: {e}")
    
    def _test_gateway_to_models_communication(
        self, 
        gateway_url: str, 
        ocr_url: str, 
        report_url: str
    ):
        """Test communication between gateway and model services"""
        # Test OCR service integration
        ocr_data = {
            "invoice_file": "fake_invoice_data",
            "packing_list_file": "fake_packing_data",
            "bill_of_lading_file": "fake_bill_data"
        }
        
        try:
            response = httpx.post(f"{ocr_url}/ocr/", files=ocr_data, timeout=60.0)
            # Should get some response (might be error due to fake data, but service should respond)
            assert response.status_code in [200, 422, 500]
        except Exception as e:
            pytest.fail(f"OCR service communication failed: {e}")
        
        # Test Report service integration
        report_data = {
            "ocr_data": {
                "invoice_number": "TEST-001",
                "total_amount": "1000.00"
            },
            "hsk_data": {
                "hsk_code": "8541.10"
            }
        }
        
        try:
            response = httpx.post(
                f"{report_url}/generate-customs-declaration", 
                json=report_data,
                timeout=60.0
            )
            # Should get some response
            assert response.status_code in [200, 422, 500]
        except Exception as e:
            pytest.fail(f"Report service communication failed: {e}")
        
        # Test Gateway process-document endpoint
        gateway_data = {
            "document_id": "docker-test-001",
            "document_type": "invoice",
            "document_data": {
                "file_name": "test.pdf",
                "file_size": 1024
            }
        }
        
        try:
            response = httpx.post(
                f"{gateway_url}/api/v1/gateway/process-document",
                json=gateway_data,
                timeout=60.0
            )
            assert response.status_code == 200
            result = response.json()
            assert "status" in result
            assert "document_id" in result
        except Exception as e:
            pytest.fail(f"Gateway communication failed: {e}")


@pytest.mark.docker
@pytest.mark.slow  
class TestPerformanceUnderLoad:
    """Performance tests under load"""
    
    def test_concurrent_requests_handling(self):
        """Test handling of concurrent requests"""
        # This would test the gateway's ability to handle
        # multiple concurrent requests to model services
        pass
    
    def test_memory_usage_under_load(self):
        """Test memory usage under sustained load"""
        # This would monitor memory usage during sustained load
        pass
    
    def test_response_time_consistency(self):
        """Test response time consistency under load"""
        # This would measure response time distribution
        pass