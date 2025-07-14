"""
FastAPI REST interface for the property RAG system.
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..rag.property_rag_chain import (PropertyAnswer, PropertyRAGChain,
                                      create_rag_chain_from_scraped_data)

logger = logging.getLogger(__name__)

# Global RAG chain instance
rag_chain: Optional[PropertyRAGChain] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global rag_chain
    
    # Startup
    logger.info("Initializing PropertyRAGChain...")
    try:
        rag_chain = create_rag_chain_from_scraped_data()
        logger.info("PropertyRAGChain initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG chain: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")


# FastAPI app
app = FastAPI(
    title="AssetPlan Property Assistant API",
    description="REST API for querying real estate properties using AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class QuestionRequest(BaseModel):
    """Request model for property questions."""
    question: str = Field(..., description="Natural language question about properties", min_length=3)
    max_sources: int = Field(default=5, description="Maximum number of sources to return", ge=1, le=20)


class SearchRequest(BaseModel):
    """Request model for property search."""
    query: str = Field(..., description="Search query", min_length=3)
    max_results: int = Field(default=10, description="Maximum number of results", ge=1, le=50)
    score_threshold: float = Field(default=0.7, description="Minimum similarity score", ge=0.0, le=1.0)


class RecommendationRequest(BaseModel):
    """Request model for property recommendations."""
    property_type: Optional[str] = Field(default=None, description="Type of property (departamento, casa, etc.)")
    location: Optional[str] = Field(default=None, description="Preferred location")
    bedrooms: Optional[int] = Field(default=None, description="Number of bedrooms", ge=0, le=10)
    bathrooms: Optional[int] = Field(default=None, description="Number of bathrooms", ge=0, le=10)
    max_price_uf: Optional[float] = Field(default=None, description="Maximum price in UF", gt=0)
    min_area_m2: Optional[float] = Field(default=None, description="Minimum area in square meters", gt=0)
    max_recommendations: int = Field(default=5, description="Maximum recommendations", ge=1, le=20)


class PropertyResponse(BaseModel):
    """Response model for property data."""
    property_id: Optional[str] = None
    title: Optional[str] = None
    property_type: Optional[str] = None
    location: Optional[str] = None
    price: Optional[str] = None
    price_uf: Optional[str] = None
    area_m2: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    url: Optional[str] = None
    similarity_score: Optional[float] = None


class QuestionResponse(PropertyAnswer):
    """Extended response model for questions."""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    processing_time_ms: Optional[float] = None


class SearchResponse(BaseModel):
    """Response model for search results."""
    query: str
    total_results: int
    properties: List[PropertyResponse]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0.0"
    system_stats: Optional[Dict[str, Any]] = None


# Dependency to get RAG chain
def get_rag_chain() -> PropertyRAGChain:
    """Get the global RAG chain instance."""
    if rag_chain is None:
        raise HTTPException(status_code=503, detail="RAG chain not initialized")
    return rag_chain


# API Endpoints
@app.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint with API information."""
    return {
        "service": "AssetPlan Property Assistant API",
        "version": "1.0.0",
        "description": "AI-powered real estate property search and recommendations",
        "endpoints": {
            "ask": "/ask - Ask questions about properties",
            "search": "/search - Search properties by query",
            "recommend": "/recommend - Get property recommendations",
            "health": "/health - Health check",
            "docs": "/docs - API documentation"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check(chain: PropertyRAGChain = Depends(get_rag_chain)):
    """Health check endpoint."""
    try:
        stats = chain.get_chain_stats()
        
        return HealthResponse(
            status="healthy" if stats.get("status") == "ready" else "degraded",
            system_stats=stats
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            system_stats={"error": str(e)}
        )


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    chain: PropertyRAGChain = Depends(get_rag_chain)
):
    """Ask a natural language question about properties.
    
    This endpoint accepts natural language questions and returns AI-generated answers
    with source citations and confidence scores.
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"Processing question: {request.question}")
        
        # Get answer from RAG chain
        answer = chain.ask_question(request.question)
        
        # Limit sources if requested
        if len(answer.sources) > request.max_sources:
            answer.sources = answer.sources[:request.max_sources]
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Create response
        response = QuestionResponse(
            **answer.model_dump(),
            processing_time_ms=processing_time
        )
        
        logger.info(f"Question processed successfully in {processing_time:.2f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process question: {str(e)}"
        )


@app.post("/search", response_model=SearchResponse)
async def search_properties(
    request: SearchRequest,
    chain: PropertyRAGChain = Depends(get_rag_chain)
):
    """Search properties using semantic similarity.
    
    This endpoint performs semantic search across property descriptions and metadata
    to find relevant properties matching the search query.
    """
    try:
        logger.info(f"Searching properties with query: {request.query}")
        
        # Perform search
        properties = chain.search_properties(
            query=request.query,
            max_results=request.max_results,
            score_threshold=request.score_threshold
        )
        
        # Convert to response format
        property_responses = [
            PropertyResponse(**prop) for prop in properties
        ]
        
        response = SearchResponse(
            query=request.query,
            total_results=len(property_responses),
            properties=property_responses
        )
        
        logger.info(f"Search completed, found {len(properties)} properties")
        return response
        
    except Exception as e:
        logger.error(f"Error in property search: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@app.post("/recommend", response_model=QuestionResponse)
async def get_recommendations(
    request: RecommendationRequest,
    chain: PropertyRAGChain = Depends(get_rag_chain)
):
    """Get property recommendations based on criteria.
    
    This endpoint provides personalized property recommendations based on
    specified criteria like location, price range, size, etc.
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"Getting recommendations with criteria: {request.model_dump()}")
        
        # Convert request to criteria dict
        criteria = request.model_dump(exclude_unset=True, exclude={"max_recommendations"})
        
        # Get recommendations
        answer = chain.get_property_recommendations(
            criteria=criteria,
            max_recommendations=request.max_recommendations
        )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        response = QuestionResponse(
            **answer.model_dump(),
            processing_time_ms=processing_time
        )
        
        logger.info(f"Recommendations generated in {processing_time:.2f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


@app.get("/stats")
async def get_system_stats(chain: PropertyRAGChain = Depends(get_rag_chain)):
    """Get detailed system statistics."""
    try:
        stats = chain.get_chain_stats()
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system stats: {str(e)}"
        )


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the server
    uvicorn.run(
        "src.api.property_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )