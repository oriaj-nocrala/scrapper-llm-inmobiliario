"""
Tests for the FastAPI REST interface.
"""
import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from src.api.property_api import app
from src.rag.property_rag_chain import PropertyAnswer


class TestPropertyAPI:
    """Test FastAPI endpoints."""
    
    @pytest.fixture
    @pytest.fixture
    @patch('src.api.property_api.get_rag_chain')
    def test_health_endpoint_healthy(self, mock_get_chain, client, mock_rag_chain):
        """Test health endpoint when system is healthy."""
        mock_get_chain.return_value = mock_rag_chain
        
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "system_stats" in data
        assert data["version"] == "1.0.0"
    
    @patch('src.api.property_api.get_rag_chain')
    @patch('src.api.property_api.get_rag_chain')
    def test_ask_question_success(self, mock_get_chain, client, mock_rag_chain):
        """Test successful question asking."""
        # Mock successful answer
        mock_answer = PropertyAnswer(
            answer="Encontré 3 departamentos en Providencia bajo 3000 UF.",
            sources=[
                {
                    "property_id": "123",
                    "title": "Departamento Providencia",
                    "location": "Providencia, Santiago",
                    "price_uf": "2.500 UF",
                    "url": "https://test.com/123",
                    "bedrooms": 2,
                    "bathrooms": 1
                }
            ],
            confidence=0.85,
            query_type="search",
            property_count=3
        )
        
        mock_rag_chain.ask_question.return_value = mock_answer
        mock_get_chain.return_value = mock_rag_chain
        
        request_data = {
            "question": "¿Hay departamentos en Providencia bajo 3000 UF?",
            "max_sources": 5
        }
        
        response = client.post("/ask", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["answer"] == "Encontré 3 departamentos en Providencia bajo 3000 UF."
        assert data["confidence"] == 0.85
        assert data["query_type"] == "search"
        assert data["property_count"] == 3
        assert len(data["sources"]) == 1
        assert "timestamp" in data
        assert "processing_time_ms" in data
    
    @patch('src.api.property_api.get_rag_chain')
    def test_ask_question_invalid_input(self, mock_get_chain, client):
        """Test question asking with invalid input."""
        request_data = {
            "question": "ab",  # Too short
            "max_sources": 5
        }
        
        response = client.post("/ask", json=request_data)
        assert response.status_code == 422  # Validation error
    
    @patch('src.api.property_api.get_rag_chain')
    def test_ask_question_error(self, mock_get_chain, client, mock_rag_chain):
        """Test question asking with processing error."""
        mock_rag_chain.ask_question.side_effect = Exception("Processing error")
        mock_get_chain.return_value = mock_rag_chain
        
        request_data = {
            "question": "¿Hay departamentos disponibles?",
            "max_sources": 5
        }
        
        response = client.post("/ask", json=request_data)
        assert response.status_code == 500
        
        data = response.json()
        assert "error" in data
        assert "Processing error" in data["error"]
    
    @patch('src.api.property_api.get_rag_chain')
    def test_search_properties_success(self, mock_get_chain, client, mock_rag_chain):
        """Test successful property search."""
        mock_search_results = [
            {
                "property_id": "123",
                "title": "Departamento Moderno",
                "location": "Providencia",
                "price_uf": "2.800 UF",
                "bedrooms": 2,
                "bathrooms": 1,
                "url": "https://test.com/123",
                "similarity_score": 0.92
            },
            {
                "property_id": "456",
                "title": "Departamento Luminoso",
                "location": "Las Condes",
                "price_uf": "3.200 UF",
                "bedrooms": 2,
                "bathrooms": 2,
                "url": "https://test.com/456",
                "similarity_score": 0.88
            }
        ]
        
        mock_rag_chain.search_properties.return_value = mock_search_results
        mock_get_chain.return_value = mock_rag_chain
        
        request_data = {
            "query": "departamento 2 dormitorios",
            "max_results": 10,
            "score_threshold": 0.7
        }
        
        response = client.post("/search", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["query"] == "departamento 2 dormitorios"
        assert data["total_results"] == 2
        assert len(data["properties"]) == 2
        assert data["properties"][0]["similarity_score"] == 0.92
        assert "timestamp" in data
    
    @patch('src.api.property_api.get_rag_chain')
    @patch('src.api.property_api.get_rag_chain')
    def test_get_recommendations_success(self, mock_get_chain, client, mock_rag_chain):
        """Test successful recommendation generation."""
        mock_answer = PropertyAnswer(
            answer="Te recomiendo estas propiedades que cumplen tus criterios:",
            sources=[
                {
                    "property_id": "789",
                    "title": "Departamento Ideal",
                    "location": "Providencia, Santiago",
                    "price_uf": "2.900 UF",
                    "bedrooms": 2,
                    "bathrooms": 2,
                    "url": "https://test.com/789"
                }
            ],
            confidence=0.78,
            query_type="recommendation",
            property_count=1
        )
        
        mock_rag_chain.get_property_recommendations.return_value = mock_answer
        mock_get_chain.return_value = mock_rag_chain
        
        request_data = {
            "property_type": "departamento",
            "location": "Providencia",
            "bedrooms": 2,
            "max_price_uf": 3000,
            "max_recommendations": 3
        }
        
        response = client.post("/recommend", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["query_type"] == "recommendation"
        assert data["confidence"] == 0.78
        assert len(data["sources"]) == 1
        assert "processing_time_ms" in data
    
    @patch('src.api.property_api.get_rag_chain')
    @patch('src.api.property_api.get_rag_chain')
    def test_get_stats_endpoint(self, mock_get_chain, client, mock_rag_chain):
        """Test system statistics endpoint."""
        mock_get_chain.return_value = mock_rag_chain
        
        response = client.get("/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["llm_model"] == "gpt-3.5-turbo"
        assert data["retrieval_k"] == 5
        assert "vector_store_stats" in data
    
    def test_request_validation(self, client):
        """Test request validation for various endpoints."""
        # Test ask endpoint with missing question
        response = client.post("/ask", json={"max_sources": 5})
        assert response.status_code == 422
        
        # Test search endpoint with missing query
        response = client.post("/search", json={"max_results": 10})
        assert response.status_code == 422
        
        # Test invalid max_sources (too high)
        response = client.post("/ask", json={
            "question": "test question",
            "max_sources": 100  # Above limit
        })
        assert response.status_code == 422
        
        # Test invalid score_threshold
        response = client.post("/search", json={
            "query": "test query",
            "score_threshold": 1.5  # Above 1.0
        })
        assert response.status_code == 422


@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests for the API."""
    
    @pytest.fixture
    @pytest.mark.skipif(
        True,  # Skip by default as it requires full setup
        reason="Requires full system setup with OpenAI API key"
    )
    def test_full_api_workflow(self, integration_client):
        """Test complete API workflow."""
        # This would test the full workflow with real data
        # Skip by default as it requires proper setup
        
        # 1. Check health
        health_response = integration_client.get("/health")
        assert health_response.status_code == 200
        
        # 2. Ask a question
        question_response = integration_client.post("/ask", json={
            "question": "¿Hay departamentos disponibles?",
            "max_sources": 3
        })
        assert question_response.status_code == 200
        
        # 3. Search properties
        search_response = integration_client.post("/search", json={
            "query": "departamento Santiago",
            "max_results": 5
        })
        assert search_response.status_code == 200
        
        # 4. Get recommendations
        recommend_response = integration_client.post("/recommend", json={
            "property_type": "departamento",
            "max_recommendations": 3
        })
        assert recommend_response.status_code == 200


class TestAPIErrorHandling:
    """Test API error handling scenarios."""
    
    @pytest.fixture
    @patch('src.api.property_api.get_rag_chain')
    @patch('src.api.property_api.get_rag_chain')
if __name__ == "__main__":
    pytest.main([__file__, "-v"])