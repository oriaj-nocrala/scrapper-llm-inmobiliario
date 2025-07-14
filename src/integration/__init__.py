"""
Módulo de integración entre componentes del sistema.
"""
from .scraper_rag_pipeline import (ScraperRAGPipeline, ScrapingPipelineError,
                                   create_comprehensive_pipeline,
                                   create_quick_pipeline)

__all__ = [
    "ScraperRAGPipeline",
    "ScrapingPipelineError", 
    "create_quick_pipeline",
    "create_comprehensive_pipeline"
]