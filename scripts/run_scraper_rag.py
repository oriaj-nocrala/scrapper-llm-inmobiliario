#!/usr/bin/env python3
"""
Comando unificado para ejecutar scraping + RAG + API en un solo proceso.
Permite ejecutar todo el pipeline desde scraping hasta tener la API lista.
"""
import argparse
import sys
import time
import signal
import subprocess
from pathlib import Path
from threading import Thread
from typing import Optional

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.integration.scraper_rag_pipeline import (
    ScraperRAGPipeline, 
    create_quick_pipeline, 
    create_comprehensive_pipeline
)
from src.utils.config import settings


class UnifiedPipelineRunner:
    """Ejecutor unificado para todo el pipeline Scraper + RAG + API."""
    
    def __init__(self):
        self.pipeline: Optional[ScraperRAGPipeline] = None
        self.api_process: Optional[subprocess.Popen] = None
        self.should_stop = False
        
    def signal_handler(self, signum, frame):
        """Manejar señales de interrupción."""
        print("\n🛑 Interrupción recibida, deteniendo pipeline...")
        self.should_stop = True
        
        if self.pipeline:
            self.pipeline.cleanup()
            
        if self.api_process:
            print("🔌 Deteniendo servidor API...")
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.api_process.kill()
                
        sys.exit(0)
        
    def run_complete_pipeline(self, args) -> bool:
        """Ejecutar pipeline completo: scraping + RAG + API."""
        print("🚀 PIPELINE COMPLETO SCRAPER + RAG + API")
        print("=" * 60)
        
        # Configurar callback de progreso
        def progress_callback(data):
            if not args.quiet:
                print(f"📈 {data['message']} ({data.get('percentage', 0):.1f}%)")
        
        try:
            # Fase 1: Scraping + RAG
            if args.mode == "quick":
                print("🔥 Modo: RÁPIDO (velocidad extrema)")
                self.pipeline = create_quick_pipeline(progress_callback=progress_callback)
                stats = self.pipeline.run_quick_pipeline(
                    max_properties=args.max_properties,
                    base_url=args.url
                )
            elif args.mode == "comprehensive":
                print("🏗️ Modo: COMPREHENSIVE (calidad máxima)")
                self.pipeline = create_comprehensive_pipeline(progress_callback=progress_callback)
                stats = self.pipeline.run_comprehensive_pipeline(
                    max_properties=args.max_properties,
                    base_url=args.url
                )
            else:
                print("⚙️ Modo: PERSONALIZADO")
                from src.scraper.services.scraper_manager import ScrapingConfig
                
                config = ScrapingConfig(
                    max_properties=args.max_properties,
                    behavior_mode=args.behavior or "fast",
                    enable_validation=args.enable_validation,
                    enable_performance_monitoring=args.enable_monitoring,
                    debug_mode=args.debug
                )
                
                self.pipeline = ScraperRAGPipeline(
                    auto_rebuild_index=True,
                    validate_data=args.enable_validation,
                    progress_callback=progress_callback
                )
                
                stats = self.pipeline.run_custom_pipeline(
                    scraping_config=config,
                    base_url=args.url
                )
            
            if not stats["success"]:
                print("❌ Pipeline falló")
                return False
                
            # Mostrar estadísticas
            if not args.quiet:
                print(f"\n✅ PIPELINE COMPLETADO")
                print(f"📊 Propiedades scraped: {stats['properties_scraped']}")
                print(f"⏱️ Tiempo total: {stats['total_pipeline_duration']:.2f}s")
                print(f"🚀 Scraping: {stats['scraping_duration']:.2f}s")
                print(f"📊 Indexing: {stats['indexing_duration']:.2f}s")
                print(f"🤖 RAG init: {stats['rag_initialization_duration']:.2f}s")
            
            # Fase 2: Iniciar API si está solicitado
            if args.start_api:
                print(f"\n🌐 Iniciando servidor API en puerto {args.api_port}...")
                
                # Verificar que el sistema RAG esté listo
                rag_chain = self.pipeline.get_rag_chain()
                if not rag_chain:
                    print("❌ Sistema RAG no está listo para iniciar API")
                    return False
                
                # Iniciar servidor API en proceso separado
                api_cmd = [
                    sys.executable, "run_api.py"
                ]
                
                # Configurar variables de entorno para la API
                import os
                env = os.environ.copy()
                env["API_PORT"] = str(args.api_port)
                env["API_HOST"] = args.api_host
                
                self.api_process = subprocess.Popen(
                    api_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=env
                )
                
                # Esperar un poco para que la API inicie
                time.sleep(3)
                
                print(f"🎯 API lista en: http://{args.api_host}:{args.api_port}")
                print(f"📖 Documentación: http://{args.api_host}:{args.api_port}/docs")
                
                if args.wait_for_api:
                    print("\n⏳ Manteniendo API activa... (Ctrl+C para detener)")
                    try:
                        # Mantener el proceso principal activo
                        while not self.should_stop:
                            if self.api_process.poll() is not None:
                                print("❌ El servidor API se detuvo inesperadamente")
                                break
                            time.sleep(1)
                    except KeyboardInterrupt:
                        pass
            
            return True
            
        except Exception as e:
            print(f"❌ Error en pipeline: {e}")
            if args.debug:
                import traceback
                traceback.print_exc()
            return False
            
    def test_rag_system(self, args) -> bool:
        """Probar el sistema RAG con consultas de ejemplo."""
        print("🧪 PRUEBA DEL SISTEMA RAG")
        print("=" * 40)
        
        try:
            from src.rag.property_rag_chain import create_rag_chain_from_scraped_data
            
            # Verificar que existan datos
            properties_file = Path(settings.properties_json_path)
            if not properties_file.exists():
                print(f"❌ No se encontró archivo de propiedades: {properties_file}")
                print("Ejecuta primero el scraping con --mode quick o --mode comprehensive")
                return False
            
            print("🤖 Inicializando sistema RAG...")
            rag_chain = create_rag_chain_from_scraped_data()
            
            # Consultas de prueba
            test_questions = [
                "¿Cuántas propiedades hay disponibles?",
                "Muéstrame departamentos en Providencia",
                "¿Hay propiedades bajo 2000 UF?",
                "Recomiéndame una propiedad con 2 dormitorios",
                "¿Cuáles son las propiedades más baratas?"
            ]
            
            print(f"\n📝 Ejecutando {len(test_questions)} consultas de prueba...\n")
            
            for i, question in enumerate(test_questions, 1):
                print(f"❓ Pregunta {i}: {question}")
                
                start_time = time.time()
                answer = rag_chain.ask_question(question)
                response_time = time.time() - start_time
                
                print(f"💬 Respuesta: {answer.answer[:150]}...")
                print(f"📊 Confianza: {answer.confidence:.2f}")
                print(f"📋 Fuentes: {len(answer.sources)}")
                print(f"⏱️ Tiempo: {response_time*1000:.0f}ms")
                print("-" * 50)
            
            print("✅ Todas las pruebas completadas exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error en pruebas RAG: {e}")
            if args.debug:
                import traceback
                traceback.print_exc()
            return False


def main():
    """Función principal del comando unificado."""
    parser = argparse.ArgumentParser(
        description="Pipeline Unificado: Scraper + RAG + API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Pipeline rápido + API
  python run_scraper_rag.py --mode quick --max-properties 20 --start-api

  # Pipeline comprehensive sin API
  python run_scraper_rag.py --mode comprehensive --max-properties 50

  # Solo probar sistema RAG existente
  python run_scraper_rag.py --test-only

  # Pipeline personalizado con API en puerto específico
  python run_scraper_rag.py --mode custom --behavior fast --api-port 8080 --start-api
        """)
    
    # Modos de ejecución
    parser.add_argument(
        "--mode",
        choices=["quick", "comprehensive", "custom"],
        default="quick",
        help="Modo de pipeline: quick (rápido), comprehensive (completo), custom (personalizado)"
    )
    
    parser.add_argument(
        "--test-only",
        action="store_true",
        help="Solo probar sistema RAG existente (sin scraping)"
    )
    
    # Configuración de scraping
    parser.add_argument(
        "--max-properties", "-n",
        type=int,
        default=30,
        help="Máximo número de propiedades a scraper (default: 30)"
    )
    
    parser.add_argument(
        "--url",
        type=str,
        default="https://www.assetplan.cl/arriendo/departamento",
        help="URL base para scraping"
    )
    
    parser.add_argument(
        "--behavior",
        choices=["extreme", "fast", "normal", "slow"],
        default="fast",
        help="Comportamiento del scraper (solo para modo custom)"
    )
    
    # Configuración de API
    parser.add_argument(
        "--start-api",
        action="store_true",
        help="Iniciar servidor API después del pipeline"
    )
    
    parser.add_argument(
        "--api-port",
        type=int,
        default=8000,
        help="Puerto para el servidor API (default: 8000)"
    )
    
    parser.add_argument(
        "--api-host",
        type=str,
        default="0.0.0.0",
        help="Host para el servidor API (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--wait-for-api",
        action="store_true",
        help="Mantener el proceso activo después de iniciar la API"
    )
    
    # Opciones adicionales
    parser.add_argument(
        "--enable-validation",
        action="store_true",
        help="Habilitar validación de datos (solo para modo custom)"
    )
    
    parser.add_argument(
        "--enable-monitoring",
        action="store_true",
        help="Habilitar monitoreo de performance (solo para modo custom)"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Modo silencioso (menos output)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Modo debug con información detallada"
    )
    
    args = parser.parse_args()
    
    # Crear runner y configurar manejo de señales
    runner = UnifiedPipelineRunner()
    signal.signal(signal.SIGINT, runner.signal_handler)
    signal.signal(signal.SIGTERM, runner.signal_handler)
    
    # Configurar logging básico
    import logging
    level = logging.DEBUG if args.debug else (logging.WARNING if args.quiet else logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ejecutar según el modo solicitado
    try:
        if args.test_only:
            success = runner.test_rag_system(args)
        else:
            success = runner.run_complete_pipeline(args)
        
        if success:
            if not args.quiet:
                print("\n🎉 Operación completada exitosamente!")
            return 0
        else:
            if not args.quiet:
                print("\n❌ Operación falló")
            return 1
            
    except KeyboardInterrupt:
        if not args.quiet:
            print("\n👋 Proceso interrumpido por el usuario")
        return 0
    except Exception as e:
        print(f"\n💥 Error inesperado: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())