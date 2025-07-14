"""
FAISS Vector Store implementation for property embeddings with LangChain integration.
"""
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from ..scraper.models import Property, PropertyCollection
from ..utils.config import settings

logger = logging.getLogger(__name__)


def create_embeddings_model() -> Embeddings:
    """Create and return the appropriate embeddings model based on configuration."""
    if settings.use_local_models:
        logger.info("🏠 Initializing LOCAL embeddings model with HuggingFace")
        
        # Use HuggingFace multilingual model for better Spanish support
        device = settings.embedding_device if settings.use_gpu else 'cpu'
        
        model_kwargs = {
            'device': device,
            'trust_remote_code': True
        }
        
        # Add GPU-specific optimizations
        if settings.use_gpu and device == 'cuda':
            logger.info(f"🚀 Embeddings GPU acceleration enabled on {device}")
            # Note: torch_dtype is not supported in SentenceTransformer constructor
            # Half precision optimization is handled internally by the model
        else:
            logger.info(f"💻 Embeddings using device: {device}")
        
        return HuggingFaceEmbeddings(
            model_name=settings.local_embedding_hf_model,
            model_kwargs=model_kwargs,
            encode_kwargs={
                'normalize_embeddings': True,
                'batch_size': 32 if settings.use_gpu else 8,  # Larger batch for GPU
                'convert_to_tensor': True,
                'device': device
            }
        )
    else:
        logger.info("🌐 Initializing OpenAI embeddings model")
        return OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key,
            model=settings.embedding_model
        )


class PropertyVectorStore:
    """FAISS-based vector store for property documents with LangChain integration."""
    
    def __init__(self, 
                 embeddings: Optional[Embeddings] = None,
                 index_path: Optional[str] = None):
        """Initialize the property vector store.
        
        Args:
            embeddings: Embedding model to use (defaults to OpenAI)
            index_path: Path to save/load FAISS index
        """
        # Initialize embeddings based on configuration
        self.embeddings = embeddings or create_embeddings_model()
        self.index_path = index_path or settings.faiss_index_path
        self.vector_store: Optional[FAISS] = None
        self.property_metadata: List[Dict[str, Any]] = []
        
        # Ensure index directory exists
        Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)
        
    def create_documents_from_properties(self, properties: List[Property]) -> List[Document]:
        """Convert Property objects to LangChain Documents.
        
        Args:
            properties: List of Property objects
            
        Returns:
            List of LangChain Document objects
        """
        documents = []
        
        for prop in properties:
            # Create comprehensive text content for embedding
            content_parts = []
            
            # Basic information
            content_parts.append(f"Título: {prop.title}")
            
            if prop.property_type:
                content_parts.append(f"Tipo: {prop.property_type}")
            
            if prop.location:
                content_parts.append(f"Ubicación: {prop.location}")
            
            # Price information
            if prop.price:
                content_parts.append(f"Precio: {prop.price}")
            if prop.price_uf:
                content_parts.append(f"Precio UF: {prop.price_uf}")
            
            # Physical characteristics
            if prop.area_m2:
                content_parts.append(f"Superficie: {prop.area_m2} m²")
            if prop.bedrooms is not None:
                content_parts.append(f"Dormitorios: {prop.bedrooms}")
            if prop.bathrooms is not None:
                content_parts.append(f"Baños: {prop.bathrooms}")
            
            # Description
            if prop.description:
                content_parts.append(f"Descripción: {prop.description}")
            
            # Combine all content
            page_content = " | ".join(content_parts)
            
            # Create metadata for retrieval and citation
            metadata = {
                "property_id": prop.id or str(hash(str(prop.url))),
                "title": prop.title,
                "property_type": prop.property_type,
                "location": prop.location,
                "price": prop.price,
                "price_uf": prop.price_uf,
                "area_m2": prop.area_m2,
                "bedrooms": prop.bedrooms,
                "bathrooms": prop.bathrooms,
                "url": str(prop.url),
                "images": prop.images,
                "source": "assetplan.cl"
            }
            
            # Create LangChain Document
            document = Document(
                page_content=page_content,
                metadata=metadata
            )
            
            documents.append(document)
        
        logger.info(f"Created {len(documents)} documents from properties")
        return documents
    
    def load_properties_and_create_index(self, properties: List[Property]) -> None:
        """Load properties and create FAISS index.
        
        Args:
            properties: List of Property objects to index
        """
        logger.info(f"Creating FAISS index from {len(properties)} properties")
        
        # Convert properties to documents
        documents = self.create_documents_from_properties(properties)
        
        if not documents:
            logger.warning("No documents to index")
            return
        
        # Create FAISS vector store from documents
        try:
            self.vector_store = FAISS.from_documents(
                documents=documents,
                embedding=self.embeddings
            )
            
            # Store metadata separately for easy access
            self.property_metadata = [doc.metadata for doc in documents]
            
            logger.info(f"Successfully created FAISS index with {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"Failed to create FAISS index: {e}")
            raise
    
    def load_from_json(self, json_path: str) -> None:
        """Load properties from JSON file and create index.
        
        Args:
            json_path: Path to JSON file with property data
        """
        import json
        
        logger.info(f"Loading properties from {json_path}")
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Parse as PropertyCollection
            if isinstance(data, dict) and 'properties' in data:
                collection = PropertyCollection(**data)
                properties = collection.properties
            else:
                # Assume it's a list of properties
                properties = [Property(**prop_data) for prop_data in data]
            
            self.load_properties_and_create_index(properties)
            
        except Exception as e:
            logger.error(f"Failed to load properties from JSON: {e}")
            raise
    
    def save_index(self, path: Optional[str] = None) -> None:
        """Save FAISS index to disk.
        
        Args:
            path: Path to save index (optional)
        """
        if not self.vector_store:
            logger.warning("No vector store to save")
            return
        
        save_path = path or self.index_path
        
        try:
            # Save FAISS index
            self.vector_store.save_local(save_path)
            
            # Save metadata separately
            metadata_path = Path(save_path) / "metadata.pkl"
            with open(metadata_path, 'wb') as f:
                pickle.dump(self.property_metadata, f)
            
            logger.info(f"FAISS index saved to {save_path}")
            
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")
            raise
    
    def load_index(self, path: Optional[str] = None) -> bool:
        """Load FAISS index from disk.
        
        Args:
            path: Path to load index from (optional)
            
        Returns:
            True if loaded successfully, False otherwise
        """
        load_path = path or self.index_path
        
        try:
            if not Path(load_path).exists():
                logger.info(f"Index path {load_path} does not exist")
                return False
            
            # Load FAISS index
            self.vector_store = FAISS.load_local(
                load_path, 
                self.embeddings,
                allow_dangerous_deserialization=True  # Required for FAISS loading
            )
            
            # Load metadata
            metadata_path = Path(load_path) / "metadata.pkl"
            if metadata_path.exists():
                with open(metadata_path, 'rb') as f:
                    self.property_metadata = pickle.load(f)
            
            logger.info(f"FAISS index loaded from {load_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            return False
    
    def search_properties(self, 
                         query: str, 
                         k: int = 5,
                         score_threshold: float = 0.7) -> List[Tuple[Document, float]]:
        """Search for properties using semantic similarity.
        
        Args:
            query: Search query
            k: Number of results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of (Document, score) tuples
        """
        if not self.vector_store:
            logger.warning("No vector store available for search")
            return []
        
        try:
            # Perform similarity search with scores
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=k
            )
            
            # Filter by score threshold (FAISS returns distance, lower is better)
            # Convert distance to similarity: similarity = 1 / (1 + distance)
            filtered_results = []
            for doc, distance in results:
                similarity = 1 / (1 + distance)
                if similarity >= score_threshold:
                    filtered_results.append((doc, similarity))
            
            logger.info(f"Found {len(filtered_results)} properties matching query: {query}")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error during property search: {e}")
            return []
    
    def get_retriever(self, k: int = 5):
        """Get LangChain retriever for RAG applications.
        
        Args:
            k: Number of documents to retrieve
            
        Returns:
            LangChain VectorStoreRetriever
        """
        if not self.vector_store:
            raise ValueError("No vector store available. Load or create index first.")
        
        return self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store.
        
        Returns:
            Dictionary with statistics
        """
        if not self.vector_store:
            return {"status": "empty", "document_count": 0}
        
        try:
            # Get FAISS index info
            index = self.vector_store.index
            document_count = index.ntotal if hasattr(index, 'ntotal') else len(self.property_metadata)
            
            # Analyze property types and locations
            property_types = {}
            locations = {}
            price_ranges = {"with_price": 0, "without_price": 0}
            
            for metadata in self.property_metadata:
                # Property types
                prop_type = metadata.get('property_type', 'Unknown')
                property_types[prop_type] = property_types.get(prop_type, 0) + 1
                
                # Locations
                location = metadata.get('location', 'Unknown')
                locations[location] = locations.get(location, 0) + 1
                
                # Price info
                if metadata.get('price_uf') or metadata.get('price'):
                    price_ranges["with_price"] += 1
                else:
                    price_ranges["without_price"] += 1
            
            return {
                "status": "loaded",
                "document_count": document_count,
                "embedding_dimension": index.d if hasattr(index, 'd') else "unknown",
                "property_types": property_types,
                "top_locations": dict(sorted(locations.items(), key=lambda x: x[1], reverse=True)[:5]),
                "price_coverage": price_ranges,
                "index_path": self.index_path
            }
            
        except Exception as e:
            logger.error(f"Error getting vector store stats: {e}")
            return {"status": "error", "error": str(e)}


def create_vector_store_from_scraped_data(json_path: Optional[str] = None) -> PropertyVectorStore:
    """Convenience function to create vector store from scraped data.
    
    Args:
        json_path: Path to JSON file with scraped properties
        
    Returns:
        Configured PropertyVectorStore
    """
    json_path = json_path or settings.properties_json_path
    
    if not Path(json_path).exists():
        raise FileNotFoundError(f"Properties file not found: {json_path}")
    
    # Check if we need OpenAI API key (only when not using local models)
    if not settings.use_local_models and not settings.openai_api_key:
        raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY environment variable.")
    
    # Create vector store
    vector_store = PropertyVectorStore()
    
    # Try to load existing index first
    if vector_store.load_index():
        logger.info("Loaded existing FAISS index")
    else:
        logger.info("Creating new FAISS index from scraped data")
        vector_store.load_from_json(json_path)
        vector_store.save_index()
    
    return vector_store


def rebuild_vector_store(json_path: Optional[str] = None, 
                        force: bool = False) -> PropertyVectorStore:
    """Rebuild vector store from scratch.
    
    Args:
        json_path: Path to JSON file with scraped properties
        force: Force rebuild even if index exists
        
    Returns:
        Rebuilt PropertyVectorStore
    """
    json_path = json_path or settings.properties_json_path
    
    if not Path(json_path).exists():
        raise FileNotFoundError(f"Properties file not found: {json_path}")
    
    vector_store = PropertyVectorStore()
    
    if not force and vector_store.load_index():
        logger.info("Index already exists. Use force=True to rebuild.")
        return vector_store
    
    logger.info("Rebuilding FAISS index from scraped data")
    vector_store.load_from_json(json_path)
    vector_store.save_index()
    
    return vector_store