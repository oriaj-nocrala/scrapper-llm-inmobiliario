"""
LangChain RAG chain for property question answering with source citations.
Supports both OpenAI and local GGUF models via llama.cpp.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_community.llms import LlamaCpp
from langchain_core.documents import Document
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from ..utils.config import settings
from ..vectorstore.faiss_store import PropertyVectorStore

logger = logging.getLogger(__name__)


def create_llm_model() -> BaseLanguageModel:
    """Create and return the appropriate LLM model based on configuration."""
    if settings.use_local_models:
        logger.info("🏠 Initializing LOCAL GGUF model with llama.cpp")
        
        # Check if model file exists
        model_path = Path(settings.local_llm_model_path)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Local model not found: {model_path}. "
                f"Please ensure the GGUF model is in the correct location."
            )
        
        logger.info(f"Loading local model: {model_path}")
        
        # GPU acceleration parameters
        gpu_params = {}
        if settings.use_gpu:
            gpu_params.update({
                "n_gpu_layers": settings.gpu_layers,  # Offload layers to GPU
                "n_batch": 256,  # Optimal batch size for RTX 3050
                "n_ubatch": 128,  # Micro batch size for better memory management
                "f16_kv": True,  # Use half precision for key-value cache
                "use_mmap": True,  # Memory map model for faster loading
                "use_mlock": False,  # Don't lock model in RAM to save memory
            })
            logger.info(f"🚀 GPU acceleration enabled: {settings.gpu_layers} layers, {settings.gpu_memory_limit}GB limit")
        else:
            logger.info("💻 Using CPU-only inference")
        
        return LlamaCpp(
            model_path=str(model_path),
            n_ctx=settings.local_llm_n_ctx,
            n_threads=settings.local_llm_n_threads,
            temperature=0.0,  # Keep deterministic for speed
            max_tokens=400,  # Allow URLs but not too long
            verbose=False,
            streaming=False,
            # Keep some stop tokens for speed
            stop=["Human:", "Usuario:", "Pregunta:", "\n\n\n"],
            top_p=0.8,  # Balance content quality and speed
            top_k=30,   # Moderate vocabulary
            repeat_penalty=1.1,  # Prevent repetition
            **gpu_params
        )
    else:
        logger.info("🌐 Initializing OpenAI model")
        
        if not settings.openai_api_key:
            raise ValueError(
                "OpenAI API key is required when use_local_models=False. "
                "Set OPENAI_API_KEY environment variable or enable local models with USE_LOCAL_MODELS=true"
            )
        
        return ChatOpenAI(
            model=settings.openai_model,
            temperature=0.1,
            openai_api_key=settings.openai_api_key
        )


class PropertyAnswer(BaseModel):
    """Structured answer with sources and confidence."""
    answer: str = Field(description="Natural language answer to the user's question")
    sources: List[Dict[str, Any]] = Field(description="List of source properties with metadata")
    confidence: float = Field(description="Confidence score between 0 and 1", ge=0, le=1)
    query_type: str = Field(description="Type of query: search, comparison, recommendation, etc.")
    property_count: int = Field(description="Number of properties found matching the criteria")


class PropertyRAGChain:
    """RAG chain for answering property-related questions with source citations."""
    
    def __init__(self, 
                 vector_store: PropertyVectorStore,
                 llm: Optional[BaseLanguageModel] = None,
                 retrieval_k: int = 5):
        """Initialize the RAG chain.
        
        Args:
            vector_store: FAISS vector store with property embeddings
            llm: Language model (defaults to OpenAI GPT or local GGUF based on config)
            retrieval_k: Number of documents to retrieve for context
        """
        self.vector_store = vector_store
        self.retrieval_k = retrieval_k
        
        # Initialize LLM (local or OpenAI based on configuration)
        if llm is not None:
            self.llm = llm
        else:
            self.llm = create_llm_model()
        
        # Store model type for logging
        self.model_type = "local" if settings.use_local_models else "openai"
        
        # Setup prompts and chains
        self._setup_prompts()
        self._setup_chains()
        
        logger.info(f"PropertyRAGChain initialized successfully with {self.model_type} model")
    
    def _setup_prompts(self) -> None:
        """Setup prompt templates for different query types."""
        
        # Main RAG prompt for property questions - SIMPLIFIED FOR URL CITATION
        self.rag_prompt = ChatPromptTemplate.from_messages([
            ("system", """Responde sobre propiedades usando SOLO la información del contexto.

REGLAS SIMPLES:
- Lista propiedades del contexto
- SIEMPRE incluye la URL real de cada propiedad
- Copia las URLs exactamente como aparecen en el contexto
- Máximo 3 propiedades por respuesta

FORMATO:
1. Título - Precio, Superficie, Detalles
   URL: https://www.assetplan.cl/...

CONTEXTO:
{context}"""),
            ("human", "{question}")
        ])
        
        # Classification prompt to determine query type
        self.classification_prompt = PromptTemplate(
            input_variables=["question"],
            template="""Clasifica el siguiente tipo de consulta de bienes raíces en una de estas categorías:
            
- search: Búsqueda específica por características (ej: "departamentos 2 dormitorios Providencia")
- comparison: Comparación entre propiedades (ej: "compara estas propiedades")  
- recommendation: Recomendación personalizada (ej: "recomiéndame una propiedad")
- information: Información general sobre una propiedad específica
- price_analysis: Análisis de precios o valuación
- location_info: Información sobre ubicaciones/barrios

Consulta: {question}

Categoría:"""
        )
    
    def _setup_chains(self) -> None:
        """Setup the RAG processing chains."""
        
        # Document retrieval chain
        self.retriever = self.vector_store.get_retriever(k=self.retrieval_k)
        
        # Classification chain
        self.classification_chain = self.classification_prompt | self.llm | StrOutputParser()
        
        # Context formatting chain
        def format_docs(docs: List[Document]) -> str:
            """Format retrieved documents for the prompt."""
            formatted_docs = []
            for i, doc in enumerate(docs, 1):
                metadata = doc.metadata
                content = f"""
PROPIEDAD {i}:
- Título: {metadata.get('title', 'N/A')}
- Tipo: {metadata.get('property_type', 'N/A')}
- Ubicación: {metadata.get('location', 'N/A')}
- Precio: {metadata.get('price', 'N/A')}
- Precio UF: {metadata.get('price_uf', 'N/A')}
- Superficie: {metadata.get('area_m2', 'N/A')} m²
- Dormitorios: {metadata.get('bedrooms', 'N/A')}
- Baños: {metadata.get('bathrooms', 'N/A')}
- URL: {metadata.get('url', 'N/A')}
- Descripción: {doc.page_content}
"""
                formatted_docs.append(content)
            
            return "\n".join(formatted_docs)
        
        # Main RAG chain
        self.rag_chain = (
            RunnableParallel({
                "context": self.retriever | format_docs,
                "question": RunnablePassthrough()
            })
            | self.rag_prompt
            | self.llm
            | StrOutputParser()
        )
    
    def ask_question(self, question: str) -> PropertyAnswer:
        """Ask a question about properties and get a structured answer.
        
        Args:
            question: Natural language question about properties
            
        Returns:
            PropertyAnswer with answer, sources, and confidence
        """
        logger.info(f"Processing property question: {question}")
        
        try:
            # Classify the query type
            query_type = self.classification_chain.invoke({"question": question}).strip().lower()
            
            # Retrieve relevant documents
            relevant_docs = self.retriever.get_relevant_documents(question)
            
            # Generate answer using RAG chain
            answer = self.rag_chain.invoke(question)
            
            # Extract sources from retrieved documents
            sources = self._extract_sources(relevant_docs)
            
            # Calculate confidence based on retrieval quality
            confidence = self._calculate_confidence(relevant_docs, question)
            
            result = PropertyAnswer(
                answer=answer,
                sources=sources,
                confidence=confidence,
                query_type=query_type,
                property_count=len(relevant_docs)
            )
            
            logger.info(f"Successfully processed question with {len(sources)} sources")
            return result
            
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            return PropertyAnswer(
                answer=f"Lo siento, ocurrió un error al procesar tu pregunta: {str(e)}",
                sources=[],
                confidence=0.0,
                query_type="error",
                property_count=0
            )
    
    def _extract_sources(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Extract source information from retrieved documents.
        
        Args:
            documents: Retrieved documents
            
        Returns:
            List of source dictionaries with property metadata
        """
        sources = []
        
        for doc in documents:
            metadata = doc.metadata
            source = {
                "property_id": metadata.get("property_id"),
                "title": metadata.get("title"),
                "property_type": metadata.get("property_type"),
                "location": metadata.get("location"),
                "price": metadata.get("price"),
                "price_uf": metadata.get("price_uf"),
                "area_m2": metadata.get("area_m2"),
                "bedrooms": metadata.get("bedrooms"),
                "bathrooms": metadata.get("bathrooms"),
                "url": metadata.get("url"),
                "source": metadata.get("source", "assetplan.cl")
            }
            sources.append(source)
        
        return sources
    
    def _calculate_confidence(self, documents: List[Document], question: str) -> float:
        """Calculate confidence score based on retrieval quality.
        
        Args:
            documents: Retrieved documents
            question: Original question
            
        Returns:
            Confidence score between 0 and 1
        """
        if not documents:
            return 0.0
        
        # Base confidence on number of retrieved documents
        doc_count_score = min(len(documents) / self.retrieval_k, 1.0)
        
        # Check if documents have complete information
        complete_docs = 0
        for doc in documents:
            metadata = doc.metadata
            required_fields = ["title", "location", "price_uf", "url"]
            if all(metadata.get(field) for field in required_fields):
                complete_docs += 1
        
        completeness_score = complete_docs / len(documents) if documents else 0.0
        
        # Combine scores (weighted average)
        confidence = (doc_count_score * 0.4 + completeness_score * 0.6)
        
        return round(confidence, 2)
    
    def search_properties(self, 
                         query: str, 
                         max_results: int = 10,
                         score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search properties using semantic similarity.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            score_threshold: Minimum similarity score
            
        Returns:
            List of property dictionaries with similarity scores
        """
        try:
            # Use vector store search
            search_results = self.vector_store.search_properties(
                query=query,
                k=max_results,
                score_threshold=score_threshold
            )
            
            # Format results
            properties = []
            for doc, score in search_results:
                property_data = doc.metadata.copy()
                property_data["similarity_score"] = score
                property_data["content"] = doc.page_content
                properties.append(property_data)
            
            logger.info(f"Search returned {len(properties)} properties for query: {query}")
            return properties
            
        except Exception as e:
            logger.error(f"Error in property search: {e}")
            return []
    
    def get_property_recommendations(self, 
                                   criteria: Dict[str, Any],
                                   max_recommendations: int = 5) -> PropertyAnswer:
        """Get property recommendations based on criteria.
        
        Args:
            criteria: Dictionary with search criteria
            max_recommendations: Maximum number of recommendations
            
        Returns:
            PropertyAnswer with recommendations
        """
        # Build search query from criteria
        query_parts = []
        
        if criteria.get("property_type"):
            query_parts.append(f"tipo {criteria['property_type']}")
        
        if criteria.get("location"):
            query_parts.append(f"ubicación {criteria['location']}")
        
        if criteria.get("bedrooms"):
            query_parts.append(f"{criteria['bedrooms']} dormitorios")
        
        if criteria.get("max_price_uf"):
            query_parts.append(f"precio máximo {criteria['max_price_uf']} UF")
        
        if criteria.get("min_area_m2"):
            query_parts.append(f"mínimo {criteria['min_area_m2']} metros cuadrados")
        
        search_query = " ".join(query_parts)
        
        if not search_query:
            search_query = "propiedades disponibles"
        
        # Use the question answering system
        question = f"Recomiéndame propiedades que cumplan estos criterios: {search_query}"
        
        return self.ask_question(question)
    
    def get_chain_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG chain.
        
        Returns:
            Dictionary with chain statistics
        """
        vector_stats = self.vector_store.get_stats()
        
        return {
            "llm_model": self.llm.model_name,
            "retrieval_k": self.retrieval_k,
            "vector_store_stats": vector_stats,
            "status": "ready" if vector_stats.get("document_count", 0) > 0 else "no_data"
        }


def create_rag_chain_from_scraped_data(json_path: Optional[str] = None,
                                     retrieval_k: int = 5) -> PropertyRAGChain:
    """Create a RAG chain from scraped property data.
    
    Args:
        json_path: Path to scraped properties JSON file
        retrieval_k: Number of documents to retrieve
        
    Returns:
        Configured PropertyRAGChain with appropriate LLM (local or OpenAI)
    """
    from ..vectorstore.faiss_store import create_vector_store_from_scraped_data

    # Create vector store from scraped data
    vector_store = create_vector_store_from_scraped_data(json_path)
    
    # Create LLM (local or OpenAI based on configuration)
    llm = create_llm_model()
    
    # Create RAG chain
    rag_chain = PropertyRAGChain(
        vector_store=vector_store,
        llm=llm,
        retrieval_k=retrieval_k
    )
    
    return rag_chain


def demo_rag_chain():
    """Demo function to test the RAG chain."""
    try:
        # Create RAG chain
        rag_chain = create_rag_chain_from_scraped_data()
        
        # Test questions
        test_questions = [
            "¿Qué departamentos de 2 dormitorios hay en Providencia bajo 3000 UF?",
            "Muéstrame propiedades con más de 80 metros cuadrados",
            "¿Cuáles son las propiedades más baratas disponibles?",
            "Recomiéndame un departamento en Las Condes",
            "¿Hay casas disponibles en la zona oriente?"
        ]
        
        print("🏠 Probando el sistema RAG de propiedades...\n")
        
        for question in test_questions:
            print(f"❓ Pregunta: {question}")
            answer = rag_chain.ask_question(question)
            
            print(f"💬 Respuesta: {answer.answer}")
            print(f"📊 Confianza: {answer.confidence:.2f}")
            print(f"📝 Tipo: {answer.query_type}")
            print(f"🔍 Propiedades encontradas: {answer.property_count}")
            print(f"📋 Fuentes: {len(answer.sources)}")
            print("-" * 80 + "\n")
        
        # Show chain stats
        stats = rag_chain.get_chain_stats()
        print("📈 Estadísticas del sistema:")
        print(f"- Modelo LLM: {stats['llm_model']}")
        print(f"- Documentos indexados: {stats['vector_store_stats'].get('document_count', 0)}")
        print(f"- Estado: {stats['status']}")
        
    except Exception as e:
        print(f"❌ Error en la demo: {e}")


if __name__ == "__main__":
    demo_rag_chain()