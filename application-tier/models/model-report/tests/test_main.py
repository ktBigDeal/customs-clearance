"""
Unit tests for model-report main functionality
"""
import pytest  
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi import status
from httpx import AsyncClient
from langchain.schema import Document

# Import functions to test
from main import (
    process_entry, get_documents_by_main_item_name, extract_stat_code,
    get_stat_documents_by_section, map_ocr_data, process_main_item,
    process_item_detail, process_all_items, app
)


class TestProcessEntry:
    """Test process_entry function"""
    
    @pytest.mark.unit
    def test_process_entry_with_type(self):
        """Test processing entry with TYPE field"""
        항목명 = "신고구분"
        내용 = {
            "조건": "필수",
            "TYPE": "string",
            "SIZE": "2",
            "작성요령": "수입신고는 '01' 입력",
            "예시": "01"
        }
        
        result = process_entry(항목명, 내용)
        
        assert len(result) == 1
        doc = result[0]
        assert isinstance(doc, Document)
        assert "신고구분" in doc.page_content
        assert "필수" in doc.page_content
        assert "string" in doc.page_content
        assert doc.metadata["항목"] == "신고구분"
    
    @pytest.mark.unit
    def test_process_entry_with_stat_code(self):
        """Test processing entry with statistical code"""
        항목명 = "세번번호"
        내용 = {
            "TYPE": "string",
            "SIZE": "10",
            "작성요령": "HS 코드 입력",
            "통계부호": "품목분류"
        }
        
        result = process_entry(항목명, 내용)
        
        assert len(result) == 1
        doc = result[0]
        assert "[통계부호] 품목분류" in doc.page_content
    
    @pytest.mark.unit
    def test_process_entry_nested(self):
        """Test processing nested entry structure"""
        항목명 = "수입자"
        내용 = {
            "회사명": {
                "TYPE": "string",
                "SIZE": "100",
                "작성요령": "수입자 회사명"
            },
            "주소": {
                "TYPE": "string", 
                "SIZE": "200",
                "작성요령": "수입자 주소"
            }
        }
        
        result = process_entry(항목명, 내용)
        
        assert len(result) == 2
        assert any("수입자 - 회사명" in doc.metadata["항목"] for doc in result)
        assert any("수입자 - 주소" in doc.metadata["항목"] for doc in result)


class TestDocumentSearch:
    """Test document search functions"""
    
    @pytest.mark.unit
    def test_get_documents_by_main_item_name(self, sample_documents):
        """Test getting documents by main item name"""
        result = get_documents_by_main_item_name(sample_documents, "신고구분")
        
        assert len(result) == 1
        assert result[0].metadata["항목"] == "신고구분"
    
    @pytest.mark.unit
    def test_get_documents_by_main_item_name_with_sub_items(self):
        """Test getting documents including sub-items"""
        documents = [
            Document(
                page_content="test content 1",
                metadata={"항목": "수입자"}
            ),
            Document(
                page_content="test content 2", 
                metadata={"항목": "수입자 - 회사명"}
            ),
            Document(
                page_content="test content 3",
                metadata={"항목": "수입자 - 주소"}
            ),
            Document(
                page_content="test content 4",
                metadata={"항목": "다른항목"}
            )
        ]
        
        result = get_documents_by_main_item_name(documents, "수입자")
        
        assert len(result) == 3
        assert all("수입자" in doc.metadata["항목"] for doc in result)
    
    @pytest.mark.unit
    def test_extract_stat_code(self):
        """Test extracting statistical code from document content"""
        content = "[항목명] 세번번호 [TYPE] string [통계부호] 품목분류 [예시] 8541.10"
        
        result = extract_stat_code(content)
        
        assert result == "품목분류"
    
    @pytest.mark.unit
    def test_extract_stat_code_none(self):
        """Test extracting statistical code when none exists"""
        content = "[항목명] 신고구분 [TYPE] string [예시] 01"
        
        result = extract_stat_code(content)
        
        assert result is None
    
    @pytest.mark.unit
    def test_get_stat_documents_by_section(self, sample_stat_code_documents):
        """Test getting statistical documents by section"""
        result = get_stat_documents_by_section(sample_stat_code_documents, "수출입구분")
        
        assert len(result) == 1
        assert result[0].metadata["section"] == "수출입구분"


class TestMapOcrData:
    """Test OCR data mapping function"""
    
    @pytest.mark.unit
    def test_map_ocr_data_simple(self):
        """Test simple OCR data mapping"""
        ocr_data = {
            "invoice_number": "INV-001",
            "country_export": "Korea"
        }
        
        mapping = {
            "invoice_number": "인보이스 번호",
            "country_export": "수출국명"
        }
        
        result = map_ocr_data(ocr_data, mapping)
        
        assert result["인보이스 번호"] == "INV-001"
        assert result["수출국명"] == "Korea"
    
    @pytest.mark.unit
    def test_map_ocr_data_with_items(self):
        """Test OCR data mapping with items array"""
        ocr_data = {
            "items": [
                {
                    "item_name": "Product A",
                    "quantity": "100"
                },
                {
                    "item_name": "Product B", 
                    "quantity": "50"
                }
            ]
        }
        
        mapping = {
            "items": [
                {
                    "item_name": "상품명",
                    "quantity": "수량"
                }
            ]
        }
        
        result = map_ocr_data(ocr_data, mapping)
        
        assert len(result["items"]) == 2
        assert result["items"][0]["상품명"] == "Product A"
        assert result["items"][0]["수량"] == "100"
        assert result["items"][1]["상품명"] == "Product B"
        assert result["items"][1]["수량"] == "50"
    
    @pytest.mark.unit
    def test_map_ocr_data_unmapped_keys(self):
        """Test OCR data mapping with unmapped keys"""
        ocr_data = {
            "invoice_number": "INV-001",
            "unmapped_field": "some_value"
        }
        
        mapping = {
            "invoice_number": "인보이스 번호"
        }
        
        result = map_ocr_data(ocr_data, mapping)
        
        assert result["인보이스 번호"] == "INV-001"
        assert result["unmapped_field"] == "some_value"


class TestProcessingFunctions:
    """Test processing functions"""
    
    @pytest.mark.unit
    async def test_process_main_item(self, mock_llm_chain, sample_documents, sample_stat_code_documents):
        """Test processing main item"""
        mock_llm_chain.arun.return_value = "01"
        
        result = await process_main_item(
            "수입",
            "신고구분",
            mock_llm_chain,
            sample_documents,
            sample_stat_code_documents,
            {"test": "data"}
        )
        
        assert result == ("신고구분", "01")
        mock_llm_chain.arun.assert_called_once()
    
    @pytest.mark.unit
    async def test_process_item_detail(self, mock_llm_chain, sample_documents, sample_stat_code_documents):
        """Test processing item detail"""
        mock_llm_chain.arun.return_value = "Electronics"
        
        result = await process_item_detail(
            "수입",
            "거래품명",
            mock_llm_chain,
            sample_documents,
            sample_stat_code_documents,
            {"item_name": "Electronics"},
            {"hsk_code": "8541.10"}
        )
        
        assert result == ("거래품명", "Electronics")
        mock_llm_chain.arun.assert_called_once()
    
    @pytest.mark.unit
    async def test_process_all_items(self, mock_llm_chain, sample_documents, sample_stat_code_documents):
        """Test processing all items"""
        mock_llm_chain.arun.return_value = "test_value"
        
        items_data = [
            {"item_name": "Product A"},
            {"item_name": "Product B"}
        ]
        
        물품_list = ["거래품명", "세번번호"]
        
        result = await process_all_items(
            "수입",
            items_data,
            물품_list,
            mock_llm_chain,
            sample_documents,
            sample_stat_code_documents,
            {"hsk_code": "8541.10"}
        )
        
        assert len(result) == 2
        assert all("거래품명" in item for item in result)
        assert all("세번번호" in item for item in result)
        
        # Should be called 4 times (2 items * 2 fields)
        assert mock_llm_chain.arun.call_count == 4


class TestApiEndpoints:
    """Test API endpoints"""
    
    @pytest.mark.unit
    @patch('main.llm_chain')
    @patch('main.item_llm_chain')
    async def test_generate_declaration_success(
        self,
        mock_item_chain,
        mock_main_chain,
        async_client,
        sample_raw_ocr_data,
        sample_hsk_data
    ):
        """Test successful declaration generation"""
        # Setup mocks
        mock_main_chain.arun.return_value = "test_value"
        mock_item_chain.arun.return_value = "test_item_value"
        
        request_data = {
            "ocr_data": sample_raw_ocr_data,
            "hsk_data": sample_hsk_data
        }
        
        response = await async_client.post("/generate-customs-declaration/import", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert "신고구분" in result
        assert "품목별_결과" in result
        assert len(result["품목별_결과"]) >= 0
    
    @pytest.mark.unit
    async def test_generate_declaration_invalid_request(self, async_client):
        """Test declaration generation with invalid request"""
        request_data = {
            "invalid_field": "test"
        }
        
        response = await async_client.post("/generate-customs-declaration/import", json=request_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.unit
    @patch('main.llm_chain')
    async def test_generate_declaration_llm_error(
        self,
        mock_main_chain,
        async_client,
        sample_raw_ocr_data,
        sample_hsk_data
    ):
        """Test declaration generation with LLM error"""
        # Setup mock to raise exception
        mock_main_chain.arun.side_effect = Exception("OpenAI API error")
        
        request_data = {
            "ocr_data": sample_raw_ocr_data,
            "hsk_data": sample_hsk_data
        }
        
        response = await async_client.post("/generate-customs-declaration/import", json=request_data)
        
        # Should handle the error gracefully and return 500
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestIntegrationModelReport:
    """Integration tests for model-report"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_full_declaration_workflow_mock(self, async_client):
        """Test full declaration workflow with mocked LLM"""
        # This would test the full workflow but with mocked LLM
        pass
    
    @pytest.mark.openai
    @pytest.mark.slow
    async def test_declaration_with_real_openai(self, async_client):
        """Test declaration with real OpenAI API (requires valid API key)"""
        # This test would only run when OpenAI API key is available
        pytest.skip("Requires real OpenAI API key")