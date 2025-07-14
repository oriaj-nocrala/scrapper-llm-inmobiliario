#!/usr/bin/env python3
"""
Test rápido de GPU para verificar que la aceleración funciona.
"""
import os
import sys
import time
from pathlib import Path

# Configurar GPU antes de importar
os.environ["USE_LOCAL_MODELS"] = "true"
os.environ["USE_GPU"] = "true"
os.environ["GPU_LAYERS"] = "35"

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_gpu_quick():
    """Test rápido de GPU."""
    print("🚀 TEST RÁPIDO DE ACELERACIÓN GPU")
    print("=" * 50)
    
    # Verificar datos
    properties_file = Path("data/properties.json")
    if not properties_file.exists():
        print("❌ No hay datos scraped disponibles")
        print("Ejecuta: python run_scraper_rag.py --mode quick --max-properties 10")
        return False
    
    try:
        print("🤖 Inicializando sistema RAG con GPU...")
        
        from src.rag.property_rag_chain import create_rag_chain_from_scraped_data
        
        start_time = time.time()
        rag_chain = create_rag_chain_from_scraped_data()
        init_time = time.time() - start_time
        
        print(f"✅ Sistema inicializado en {init_time:.2f}s")
        
        # Test simple
        test_question = "¿Cuántas propiedades hay disponibles?"
        print(f"\n❓ Pregunta: {test_question}")
        
        start_time = time.time()
        answer = rag_chain.ask_question(test_question)
        response_time = time.time() - start_time
        
        print(f"💬 Respuesta: {answer.answer}")
        print(f"⏱️ Tiempo de respuesta: {response_time:.2f}s")
        print(f"📊 Confianza: {answer.confidence:.2f}")
        print(f"📋 Fuentes: {len(answer.sources)}")
        
        # Verificar estadísticas del sistema
        stats = rag_chain.get_chain_stats()
        print(f"\n📈 Estadísticas:")
        print(f"   - Documentos: {stats.get('document_count', 'N/A')}")
        print(f"   - Estado: {stats.get('status', 'N/A')}")
        
        if response_time < 10:
            print(f"\n🎉 ¡GPU funcionando! Respuesta rápida en {response_time:.2f}s")
        elif response_time < 30:
            print(f"\n✅ GPU funcionando normalmente en {response_time:.2f}s")
        else:
            print(f"\n⚠️ Respuesta lenta ({response_time:.2f}s), verifica configuración GPU")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Configurar logging mínimo
    import logging
    logging.basicConfig(level=logging.INFO)
    
    success = test_gpu_quick()
    
    if success:
        print(f"\n💡 Para ajustar rendimiento:")
        print(f"   - Más velocidad: export GPU_LAYERS=40")
        print(f"   - Menos memoria: export GPU_LAYERS=25")
    
    sys.exit(0 if success else 1)