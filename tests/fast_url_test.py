#!/usr/bin/env python3
"""
Test rápido y focalizado para verificar citación de URLs.
"""
import os
import sys
import time
import re
from pathlib import Path

# Configuración optimizada
os.environ["USE_LOCAL_MODELS"] = "true"
os.environ["USE_GPU"] = "true"
os.environ["GPU_LAYERS"] = "25"

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_url_citation_fast():
    """Test rápido para verificar que se citen las URLs originales."""
    print("🔗 TEST RÁPIDO CITACIÓN URLs")
    print("=" * 40)
    
    try:
        from src.rag.property_rag_chain import create_rag_chain_from_scraped_data
        
        print("🤖 Inicializando RAG...")
        rag_chain = create_rag_chain_from_scraped_data()
        print("✅ RAG inicializado")
        
        # Solo 3 preguntas para rapidez
        test_questions = [
            "Muestra 1 departamento en Independencia",
            "¿Hay propiedades de 1 dormitorio?",
            "Dame la propiedad más barata"
        ]
        
        print(f"🧪 Probando {len(test_questions)} preguntas...")
        
        results = []
        for i, question in enumerate(test_questions, 1):
            print(f"❓ {i}. {question}")
            
            start_time = time.time()
            answer = rag_chain.ask_question(question)
            response_time = time.time() - start_time
            
            response_text = answer.answer
            
            # Buscar URLs de assetplan.cl
            url_pattern = r'https://www\.assetplan\.cl/[^\s\)]*'
            found_urls = re.findall(url_pattern, response_text)
            
            # Mostrar resultado compacto
            print(f"💬 {response_text[:80]}...")
            print(f"🔗 URLs: {len(found_urls)} | ⏱️ {response_time:.1f}s")
            
            if len(found_urls) > 0:
                status = "✅ CON URLs"
                print(f"   URL ejemplo: {found_urls[0][:50]}...")
            else:
                status = "❌ SIN URLs"
            
            print(f"📋 {status}")
            print("-" * 40)
            
            results.append({
                'urls_found': len(found_urls),
                'time': response_time,
                'status': status
            })
        
        # Resumen
        print(f"\n📊 RESUMEN RÁPIDO:")
        print("=" * 40)
        
        with_urls = sum(1 for r in results if r['urls_found'] > 0)
        total_urls = sum(r['urls_found'] for r in results)
        avg_time = sum(r['time'] for r in results) / len(results)
        
        print(f"✅ Con URLs: {with_urls}/{len(results)}")
        print(f"🔗 Total URLs citadas: {total_urls}")
        print(f"⏱️ Tiempo promedio: {avg_time:.1f}s")
        
        # Evaluación final
        if with_urls >= 2 and total_urls >= 2:
            print(f"\n🎉 ¡CITACIÓN DE URLs FUNCIONA!")
            print("✅ Cumple requisito del coding challenge")
            return True
        else:
            print(f"\n⚠️ Citación necesita ajustes")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    success = test_url_citation_fast()
    
    if success:
        print(f"\n💡 Sistema listo para coding challenge")
        print(f"   - URLs originales citadas ✅")
        print(f"   - Funcionamiento correcto ✅")
    else:
        print(f"\n🔧 Revisar configuración URL")
    
    sys.exit(0 if success else 1)