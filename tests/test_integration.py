#!/usr/bin/env python3
"""
Test simple de integración para verificar que el pipeline Scraper-RAG funciona.
"""
import sys
import time
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_rag_simple():
    """Test simple del sistema RAG."""
    print("🧪 Test simple de integración Scraper-RAG")
    print("=" * 50)
    
    try:
        # Verificar datos
        properties_file = Path("data/properties.json")
        if not properties_file.exists():
            print("❌ No hay datos scraped disponibles")
            return False
        
        print("✅ Datos scraped encontrados")
        
        # Inicializar RAG
        print("🤖 Inicializando sistema RAG...")
        from src.rag.property_rag_chain import create_rag_chain_from_scraped_data
        
        rag_chain = create_rag_chain_from_scraped_data()
        print("✅ Sistema RAG inicializado")
        
        # Pregunta simple
        print("\n❓ Pregunta: ¿Cuántas propiedades hay disponibles?")
        
        start_time = time.time()
        answer = rag_chain.ask_question("¿Cuántas propiedades hay disponibles?")
        response_time = time.time() - start_time
        
        print(f"💬 Respuesta: {answer.answer}")
        print(f"📊 Confianza: {answer.confidence:.2f}")
        print(f"📋 Fuentes: {len(answer.sources)}")
        print(f"⏱️ Tiempo: {response_time:.2f}s")
        
        # Estadísticas del sistema
        stats = rag_chain.get_chain_stats()
        print(f"\n📈 Estadísticas del sistema:")
        print(f"   - Documentos indexados: {stats.get('document_count', 'N/A')}")
        print(f"   - Estado: {stats.get('status', 'N/A')}")
        
        print("\n🎉 Test de integración EXITOSO!")
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

if __name__ == "__main__":
    import os
    
    # Configurar para usar modelos locales
    os.environ["USE_LOCAL_MODELS"] = "true"
    
    success = test_rag_simple()
    sys.exit(0 if success else 1)