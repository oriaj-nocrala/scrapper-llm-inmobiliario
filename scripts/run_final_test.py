#!/usr/bin/env python3
"""
Test final del pipeline completo con configuración GPU optimizada.
"""
import os
import sys
import time
from pathlib import Path

# Configuración GPU optimizada para RTX 3050
os.environ["USE_LOCAL_MODELS"] = "true"
os.environ["USE_GPU"] = "true"
os.environ["GPU_LAYERS"] = "25"
os.environ["GPU_MEMORY_LIMIT"] = "5.5"

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Test final completo."""
    print("🎯 TEST FINAL DEL PIPELINE SCRAPER-RAG CON GPU")
    print("=" * 60)
    print("Configuración GPU RTX 3050: 25 layers, 5.5GB limit")
    print()
    
    # Verificar datos
    properties_file = Path("data/properties.json")
    if not properties_file.exists():
        print("❌ No hay datos scraped")
        print("🔄 Ejecutando scraping rápido...")
        
        # Ejecutar scraping
        from src.integration.scraper_rag_pipeline import create_quick_pipeline
        
        pipeline = create_quick_pipeline()
        stats = pipeline.run_quick_pipeline(max_properties=15)
        
        if not stats["success"]:
            print("❌ Scraping falló")
            return False
        
        print(f"✅ Scraping completado: {stats['properties_scraped']} propiedades")
    
    # Test del sistema RAG
    print("\n🤖 Probando sistema RAG...")
    
    try:
        from src.rag.property_rag_chain import create_rag_chain_from_scraped_data
        
        # Inicializar
        start_time = time.time()
        rag_chain = create_rag_chain_from_scraped_data()
        init_time = time.time() - start_time
        
        print(f"✅ RAG inicializado en {init_time:.2f}s")
        
        # Preguntas de test
        questions = [
            "¿Cuántas propiedades hay?",
            "¿Hay departamentos disponibles?",
            "¿Cuál es el precio promedio?"
        ]
        
        total_time = 0
        for i, question in enumerate(questions, 1):
            print(f"\n❓ {i}. {question}")
            
            start_time = time.time()
            answer = rag_chain.ask_question(question)
            response_time = time.time() - start_time
            total_time += response_time
            
            print(f"💬 {answer.answer[:120]}...")
            print(f"⏱️ {response_time:.2f}s | 📊 {answer.confidence:.2f} | 📋 {len(answer.sources)} fuentes")
        
        avg_time = total_time / len(questions)
        print(f"\n📊 RESUMEN:")
        print(f"   - Tiempo promedio: {avg_time:.2f}s")
        print(f"   - Tiempo total: {total_time:.2f}s")
        
        if avg_time < 10:
            print("🚀 ¡Rendimiento excelente!")
        elif avg_time < 30:
            print("✅ Rendimiento bueno")
        else:
            print("⚠️ Rendimiento mejorable")
        
        # Verificar memoria GPU
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,nounits,noheader'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                memory_info = result.stdout.strip().split(', ')
                used_mb = int(memory_info[0])
                total_mb = int(memory_info[1])
                
                print(f"\n🔧 Memoria GPU: {used_mb}MB / {total_mb}MB ({used_mb/total_mb*100:.1f}%)")
        except:
            pass
        
        print(f"\n🎉 TEST COMPLETO EXITOSO!")
        print(f"\n💡 Para usar el sistema:")
        print(f"   - API completa: python run_gpu_optimized.py --full-pipeline --start-api")
        print(f"   - Solo test: python run_gpu_optimized.py --test-only")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Configurar logging mínimo
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    success = main()
    sys.exit(0 if success else 1)