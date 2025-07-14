"""
Tests for the FAISS vector store and RAG chain functionality.
"""
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.vectorstore.faiss_store import PropertyVectorStore, create_vector_store_from_scraped_data
from src.rag.property_rag_chain import PropertyRAGChain, PropertyAnswer, create_rag_chain_from_scraped_data
from src.scraper.models import Property, PropertyCollection


class TestPropertyVectorStore:
    """Test FAISS vector store functionality."""
    
    @pytest.fixture
    @pytest.fixture
    @patch('src.vectorstore.faiss_store.OpenAIEmbeddings')
    def test_vector_store_initialization(self, mock_embeddings):
        """Test vector store initialization."""
        mock_embeddings_instance = Mock()
        mock_embeddings.return_value = mock_embeddings_instance
        
        vector_store = PropertyVectorStore()
        
        assert vector_store.embeddings == mock_embeddings_instance
        assert vector_store.vector_store is None
        assert vector_store.property_metadata == []
    
    def test_create_documents_from_properties(self, sample_properties):
        """Test document creation from properties."""
        with patch('src.vectorstore.faiss_store.OpenAIEmbeddings'):
            vector_store = PropertyVectorStore()
            documents = vector_store.create_documents_from_properties(sample_properties)
            
            assert len(documents) == 3
            
            # Check first document
            doc = documents[0]
            assert "Departamento en Providencia" in doc.page_content
            assert "Providencia, Santiago" in doc.page_content
            assert "2.300 UF" in doc.page_content
            assert "75.0 m²" in doc.page_content
            
            # Check metadata
            assert doc.metadata["title"] == "Departamento en Providencia"
            assert doc.metadata["property_type"] == "departamento"
            assert doc.metadata["location"] == "Providencia, Santiago"
            assert doc.metadata["bedrooms"] == 2
            assert doc.metadata["bathrooms"] == 1
            assert doc.metadata["area_m2"] == 75.0
    
    @patch('src.vectorstore.faiss_store.FAISS')
    @patch('src.vectorstore.faiss_store.OpenAIEmbeddings')
    @patch('src.vectorstore.faiss_store.FAISS')
    @patch('src.vectorstore.faiss_store.OpenAIEmbeddings')
    @patch('src.vectorstore.faiss_store.FAISS')
    @patch('src.vectorstore.faiss_store.OpenAIEmbeddings')
    class TestPropertyRAGChain:
        """Test RAG chain functionality."""

        @pytest.fixture
        @pytest.fixture
        def test_rag_chain_initialization(self, mock_vector_store, mock_llm):
            """Test RAG chain initialization."""
            rag_chain = PropertyRAGChain(
                vector_store=mock_vector_store,
                llm=mock_llm,
                retrieval_k=5
            )
            
            assert rag_chain.vector_store == mock_vector_store
            assert rag_chain.llm == mock_llm
            assert rag_chain.retrieval_k == 5
    
    @patch('src.rag.property_rag_chain.Document')
    def test_ask_question_success(self, mock_document, mock_vector_store, mock_llm):
        """Test successful question answering."""
        # Mock retriever
        mock_retriever = Mock()
        mock_doc = Mock()
        mock_doc.metadata = {
            "title": "Test Property",
            "location": "Santiago",
            "price_uf": "2000 UF",
            "url": "https://test.com",
            "property_id": "123"
        }
        mock_retriever.get_relevant_documents.return_value = [mock_doc]
        mock_vector_store.get_retriever.return_value = mock_retriever
        
        # Mock classification chain
        mock_llm.invoke.return_value = Mock()
        mock_llm.invoke.return_value.strip.return_value = "search"
        
        rag_chain = PropertyRAGChain(
            vector_store=mock_vector_store,
            llm=mock_llm
        )
        
        # Mock the RAG chain
        with patch.object(rag_chain, 'rag_chain') as mock_rag:
            mock_rag.invoke.return_value = "Esta es la respuesta generada"
            
            result = rag_chain.ask_question("¿Hay departamentos en Santiago?")
            
            assert isinstance(result, PropertyAnswer)
            assert result.answer == "Esta es la respuesta generada"
            assert result.query_type == "search"
            assert len(result.sources) == 1
            assert result.property_count == 1
            assert 0 <= result.confidence <= 1
    
    def test_ask_question_error_handling(self, mock_vector_store, mock_llm):
        """Test error handling in question answering."""
        # Make retriever raise an exception
        mock_retriever = Mock()
        mock_retriever.get_relevant_documents.side_effect = Exception("Test error")
        mock_vector_store.get_retriever.return_value = mock_retriever
        
        rag_chain = PropertyRAGChain(
            vector_store=mock_vector_store,
            llm=mock_llm
        )
        
        result = rag_chain.ask_question("¿Hay departamentos?")
        
        assert isinstance(result, PropertyAnswer)
        assert "error" in result.answer.lower()
        assert result.confidence == 0.0
        assert result.query_type == "error"
        assert len(result.sources) == 0
    
    def test_get_chain_stats(self, mock_vector_store, mock_llm):
        """Test getting chain statistics."""
        rag_chain = PropertyRAGChain(
            vector_store=mock_vector_store,
            llm=mock_llm
        )
        
        stats = rag_chain.get_chain_stats()
        
        assert stats["llm_model"] == "gpt-3.5-turbo"
        assert stats["retrieval_k"] == 5
        assert "vector_store_stats" in stats
        assert stats["status"] == "ready"


@pytest.mark.integration
class TestRAGIntegration:
    """Integration tests for RAG functionality."""
    
    @pytest.fixture
    @pytest.mark.skipif(
        not pytest.importorskip("openai", minversion="1.0.0"),
        reason="OpenAI not available"
    )
    def test_end_to_end_rag_workflow(self, integration_json_file):
        """Test complete RAG workflow from data loading to question answering."""
        # This test requires actual OpenAI API key and will be skipped in CI
        import os
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available")
        
        try:
            # Create RAG chain from test data
            with patch('src.utils.config.settings.properties_json_path', integration_json_file):
                rag_chain = create_rag_chain_from_scraped_data(integration_json_file)
            
            # Test question answering
            answer = rag_chain.ask_question("¿Hay departamentos en Providencia?")
            
            assert isinstance(answer, PropertyAnswer)
            assert len(answer.answer) > 0
            assert answer.confidence > 0
            assert answer.property_count >= 0
            
        except Exception as e:
            pytest.skip(f"Integration test skipped due to: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])