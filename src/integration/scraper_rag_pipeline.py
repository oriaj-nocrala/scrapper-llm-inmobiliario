"""
Pipeline de integración automatizada entre scraper y sistema RAG.
Coordina el proceso completo: scraping → procesamiento → índice vectorial → API RAG.
"""
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.rag.property_rag_chain import (PropertyRAGChain,
                                        create_rag_chain_from_scraped_data)
from src.scraper.services.scraper_manager import (
    ScraperManager, ScrapingConfig, scrape_properties_comprehensive,
    scrape_properties_quick)
from src.vectorstore.faiss_store import (PropertyVectorStore,
                                         rebuild_vector_store)

logger = logging.getLogger(__name__)


class ScrapingPipelineError(Exception):
    """Error específico del pipeline de scraping-RAG."""


class ScraperRAGPipeline:
    """Pipeline integrado para scraping automatizado y actualización del sistema RAG."""
    
    def __init__(self, 
                 auto_rebuild_index: bool = True,
                 validate_data: bool = True,
                 progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Inicializar el pipeline de integración.
        
        Args:
            auto_rebuild_index: Reconstruir índice FAISS automáticamente después del scraping
            validate_data: Validar datos scraped antes de procesarlos
            progress_callback: Función callback para reportar progreso
        """
        self.auto_rebuild_index = auto_rebuild_index
        self.validate_data = validate_data
        self.progress_callback = progress_callback or self._default_progress_callback
        
        self.scraper_manager: Optional[ScraperManager] = None
        self.vector_store: Optional[PropertyVectorStore] = None
        self.rag_chain: Optional[PropertyRAGChain] = None
        
        # Pipeline statistics
        self.stats = {
            "scraping_start_time": None,
            "scraping_duration": 0,
            "properties_scraped": 0,
            "indexing_duration": 0,
            "rag_initialization_duration": 0,
            "total_pipeline_duration": 0,
            "success": False,
            "errors": []
        }
        
    def _report_progress(self, step: str, message: str, percentage: float = 0) -> None:
        """Reportar progreso del pipeline."""
        self.progress_callback({
            "step": step,
            "message": message,
            "percentage": percentage,
            "timestamp": datetime.now().isoformat()
        })
        
    def run_quick_pipeline(self, 
                          max_properties: int = 50,
                          base_url: str = "https://www.assetplan.cl/arriendo/departamento") -> Dict[str, Any]:
        """
        Ejecutar pipeline rápido: scraping extremo + RAG básico.
        
        Args:
            max_properties: Máximo número de propiedades a scraper
            base_url: URL base para scraping
            
        Returns:
            Diccionario con estadísticas del pipeline
        """
        pipeline_start = time.time()
        self.stats["scraping_start_time"] = datetime.now()
        
        try:
            self._report_progress("scraping", "🚀 Iniciando scraping rápido...", 10)
            
            # Scraping rápido usando preset
            scraping_start = time.time()
            collection = scrape_properties_quick(max_properties=max_properties)
            self.stats["scraping_duration"] = time.time() - scraping_start
            self.stats["properties_scraped"] = collection.total_count
            
            if collection.total_count == 0:
                raise ScrapingPipelineError("No se obtuvieron propiedades del scraping")
                
            self._report_progress("scraping", f"✅ Scraping completado: {collection.total_count} propiedades", 40)
            
            # Validación de datos si está habilitada
            if self.validate_data:
                self._report_progress("validation", "🔍 Validando datos scraped...", 50)
                self._validate_scraped_data(collection)
                
            # Construcción/actualización del índice vectorial
            if self.auto_rebuild_index:
                self._report_progress("indexing", "📊 Construyendo índice vectorial...", 60)
                indexing_start = time.time()
                
                self.vector_store = rebuild_vector_store(force=True)
                self.stats["indexing_duration"] = time.time() - indexing_start
                
                self._report_progress("indexing", "✅ Índice vectorial actualizado", 80)
            
            # Inicialización del sistema RAG
            self._report_progress("rag", "🤖 Inicializando sistema RAG...", 90)
            rag_start = time.time()
            
            self.rag_chain = create_rag_chain_from_scraped_data()
            self.stats["rag_initialization_duration"] = time.time() - rag_start
            
            self._report_progress("rag", "✅ Sistema RAG listo", 100)
            
            # Estadísticas finales
            self.stats["total_pipeline_duration"] = time.time() - pipeline_start
            self.stats["success"] = True
            
            logger.info("Pipeline rápido completado exitosamente", extra=self.stats)
            return self.stats
            
        except Exception as e:
            self.stats["errors"].append(str(e))
            self.stats["total_pipeline_duration"] = time.time() - pipeline_start
            logger.error(f"Error en pipeline rápido: {e}")
            raise ScrapingPipelineError(f"Pipeline falló: {e}") from e
            
    def run_comprehensive_pipeline(self, 
                                  max_properties: int = 50,
                                  base_url: str = "https://www.assetplan.cl/arriendo/departamento") -> Dict[str, Any]:
        """
        Ejecutar pipeline completo: scraping comprehensive + validación + RAG optimizado.
        
        Args:
            max_properties: Máximo número de propiedades a scraper
            base_url: URL base para scraping
            
        Returns:
            Diccionario con estadísticas del pipeline
        """
        pipeline_start = time.time()
        self.stats["scraping_start_time"] = datetime.now()
        
        try:
            self._report_progress("scraping", "🏗️ Iniciando scraping comprehensive...", 5)
            
            # Scraping comprehensive usando preset
            scraping_start = time.time()
            collection = scrape_properties_comprehensive(max_properties=max_properties)
            self.stats["scraping_duration"] = time.time() - scraping_start
            self.stats["properties_scraped"] = collection.total_count
            
            if collection.total_count == 0:
                raise ScrapingPipelineError("No se obtuvieron propiedades del scraping")
                
            self._report_progress("scraping", f"✅ Scraping completado: {collection.total_count} propiedades", 30)
            
            # Validación completa de datos
            self._report_progress("validation", "🔍 Ejecutando validación completa...", 40)
            validation_report = self._validate_scraped_data(collection)
            
            self._report_progress("validation", "✅ Validación completada", 50)
            
            # Construcción optimizada del índice
            self._report_progress("indexing", "📊 Construyendo índice vectorial optimizado...", 60)
            indexing_start = time.time()
            
            self.vector_store = rebuild_vector_store(force=True)
            self.stats["indexing_duration"] = time.time() - indexing_start
            
            self._report_progress("indexing", "✅ Índice vectorial optimizado", 80)
            
            # Inicialización del sistema RAG con configuración avanzada
            self._report_progress("rag", "🤖 Inicializando sistema RAG avanzado...", 90)
            rag_start = time.time()
            
            self.rag_chain = create_rag_chain_from_scraped_data(retrieval_k=7)  # Más contexto
            self.stats["rag_initialization_duration"] = time.time() - rag_start
            
            # Test del sistema RAG
            self._report_progress("testing", "🧪 Probando sistema RAG...", 95)
            test_result = self._test_rag_system()
            
            self._report_progress("complete", "✅ Pipeline comprehensive completado", 100)
            
            # Estadísticas finales
            self.stats["total_pipeline_duration"] = time.time() - pipeline_start
            self.stats["success"] = True
            self.stats["validation_report"] = validation_report
            self.stats["rag_test_result"] = test_result
            
            logger.info("Pipeline comprehensive completado exitosamente", extra=self.stats)
            return self.stats
            
        except Exception as e:
            self.stats["errors"].append(str(e))
            self.stats["total_pipeline_duration"] = time.time() - pipeline_start
            logger.error(f"Error en pipeline comprehensive: {e}")
            raise ScrapingPipelineError(f"Pipeline falló: {e}") from e
            
    def run_custom_pipeline(self, 
                           scraping_config: ScrapingConfig,
                           base_url: str = "https://www.assetplan.cl/arriendo/departamento",
                           rebuild_index: bool = True,
                           rag_retrieval_k: int = 5) -> Dict[str, Any]:
        """
        Ejecutar pipeline con configuración personalizada.
        
        Args:
            scraping_config: Configuración personalizada para el scraper
            base_url: URL base para scraping
            rebuild_index: Si reconstruir el índice vectorial
            rag_retrieval_k: Número de documentos a recuperar para RAG
            
        Returns:
            Diccionario con estadísticas del pipeline
        """
        pipeline_start = time.time()
        self.stats["scraping_start_time"] = datetime.now()
        
        try:
            self._report_progress("scraping", "⚙️ Iniciando scraping personalizado...", 5)
            
            # Scraping con configuración personalizada
            scraping_start = time.time()
            
            with ScraperManager(scraping_config) as manager:
                collection = manager.scrape_properties(
                    base_url=base_url,
                    progress_callback=lambda data: self._report_progress(
                        "scraping", 
                        f"Scraping: {data.get('message', '')}", 
                        5 + (data.get('percentage', 0) * 0.3)  # 5-35%
                    )
                )
                
            self.stats["scraping_duration"] = time.time() - scraping_start
            self.stats["properties_scraped"] = collection.total_count
            
            if collection.total_count == 0:
                raise ScrapingPipelineError("No se obtuvieron propiedades del scraping")
                
            self._report_progress("scraping", f"✅ Scraping completado: {collection.total_count} propiedades", 40)
            
            # Validación si está habilitada
            if self.validate_data:
                self._report_progress("validation", "🔍 Validando datos...", 50)
                self._validate_scraped_data(collection)
                self._report_progress("validation", "✅ Validación completada", 60)
            
            # Índice vectorial si está habilitado
            if rebuild_index:
                self._report_progress("indexing", "📊 Actualizando índice vectorial...", 70)
                indexing_start = time.time()
                
                self.vector_store = rebuild_vector_store(force=True)
                self.stats["indexing_duration"] = time.time() - indexing_start
                
                self._report_progress("indexing", "✅ Índice actualizado", 85)
            
            # Sistema RAG
            self._report_progress("rag", "🤖 Inicializando sistema RAG...", 90)
            rag_start = time.time()
            
            self.rag_chain = create_rag_chain_from_scraped_data(retrieval_k=rag_retrieval_k)
            self.stats["rag_initialization_duration"] = time.time() - rag_start
            
            self._report_progress("complete", "✅ Pipeline personalizado completado", 100)
            
            # Estadísticas finales
            self.stats["total_pipeline_duration"] = time.time() - pipeline_start
            self.stats["success"] = True
            
            logger.info("Pipeline personalizado completado exitosamente", extra=self.stats)
            return self.stats
            
        except Exception as e:
            self.stats["errors"].append(str(e))
            self.stats["total_pipeline_duration"] = time.time() - pipeline_start
            logger.error(f"Error en pipeline personalizado: {e}")
            raise ScrapingPipelineError(f"Pipeline falló: {e}") from e
            
    def _validate_scraped_data(self, collection) -> Dict[str, Any]:
        """Validar datos scraped."""
        try:
            from src.scraper.domain.data_validator import (
                DataQualityReporter, PropertyCollectionValidator)
            
            validator = PropertyCollectionValidator()
            _, validation_summary = validator.validate_collection(collection.properties)
            
            # Generar reporte de calidad
            quality_report = DataQualityReporter.generate_report(
                collection.properties, 
                validation_summary
            )
            
            logger.info("Validación de datos completada", extra=validation_summary)
            return {
                "validation_summary": validation_summary,
                "quality_report": quality_report
            }
            
        except Exception as e:
            logger.warning(f"Error en validación de datos: {e}")
            return {"error": str(e)}
            
    def _test_rag_system(self) -> Dict[str, Any]:
        """Probar el sistema RAG con consultas de prueba."""
        if not self.rag_chain:
            return {"error": "Sistema RAG no inicializado"}
            
        test_questions = [
            "¿Cuántas propiedades hay disponibles?",
            "Muéstrame departamentos en Providencia",
            "¿Hay propiedades bajo 2000 UF?"
        ]
        
        test_results = []
        
        for question in test_questions:
            try:
                start_time = time.time()
                answer = self.rag_chain.ask_question(question)
                response_time = time.time() - start_time
                
                test_results.append({
                    "question": question,
                    "success": True,
                    "response_time_ms": response_time * 1000,
                    "confidence": answer.confidence,
                    "sources_count": len(answer.sources)
                })
                
            except Exception as e:
                test_results.append({
                    "question": question,
                    "success": False,
                    "error": str(e)
                })
                
        return {
            "total_tests": len(test_questions),
            "successful_tests": sum(1 for r in test_results if r.get("success")),
            "results": test_results
        }
        
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas completas del pipeline."""
        return self.stats.copy()
        
    def get_rag_chain(self) -> Optional[PropertyRAGChain]:
        """Obtener la instancia del RAG chain."""
        return self.rag_chain
        
    def cleanup(self) -> None:
        """Limpiar recursos del pipeline."""
        if self.scraper_manager:
            self.scraper_manager.cleanup()
            
        self.vector_store = None
        self.rag_chain = None
        logger.info("Pipeline cleanup completado")


def create_quick_pipeline(**kwargs) -> ScraperRAGPipeline:
    """Crear pipeline rápido con configuraciones optimizadas para velocidad."""
    return ScraperRAGPipeline(
        auto_rebuild_index=True,
        validate_data=False,  # Deshabilitado para velocidad
        **kwargs
    )


def create_comprehensive_pipeline(**kwargs) -> ScraperRAGPipeline:
    """Crear pipeline comprehensive con todas las validaciones."""
    return ScraperRAGPipeline(
        auto_rebuild_index=True,
        validate_data=True,
        **kwargs
    )


def demo_pipeline():
    """Demostración del pipeline integrado."""
    print("🚀 DEMO: Pipeline Integrado Scraper-RAG")
    print("=" * 60)
    
    def progress_callback(data):
        print(f"📈 {data['message']} ({data.get('percentage', 0):.1f}%)")
    
    try:
        # Pipeline rápido
        print("🔥 Ejecutando Pipeline RÁPIDO...")
        pipeline = create_quick_pipeline(progress_callback=progress_callback)
        stats = pipeline.run_quick_pipeline(max_properties=10)
        
        print(f"✅ Pipeline completado en {stats['total_pipeline_duration']:.2f}s")
        print(f"📊 Propiedades scraped: {stats['properties_scraped']}")
        print(f"🤖 Sistema RAG: {'✅ Listo' if stats['success'] else '❌ Error'}")
        
        # Test del sistema RAG
        if pipeline.get_rag_chain():
            print("🧪 Probando sistema RAG...")
            rag_chain = pipeline.get_rag_chain()
            
            test_question = "¿Qué propiedades hay disponibles?"
            answer = rag_chain.ask_question(test_question)
            
            print(f"❓ Pregunta: {test_question}")
            print(f"💬 Respuesta: {answer.answer[:200]}...")
            print(f"📊 Confianza: {answer.confidence:.2f}")
            print(f"📋 Fuentes: {len(answer.sources)}")
        
        print(f"🎉 DEMO completada exitosamente!")
        
    except Exception as e:
        print(f"❌ Error en demo: {e}")


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ejecutar demo
    demo_pipeline()