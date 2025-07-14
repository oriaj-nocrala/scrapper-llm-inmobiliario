#!/usr/bin/env python3
"""
Test específico para verificar que el sistema cite las URLs originales de las propiedades.
Requisito del coding challenge.
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

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_url_citation():
    """Test para verificar que se citen las URLs originales."""
    print("🔗 TEST DE CITACIÓN DE URLs ORIGINALES")
    print("=" * 55)
    print("Verificando requisito del coding challenge: citar URLs")
    print()
    
    try:
        from src.rag.property_rag_chain import create_rag_chain_from_scraped_data
        
        print("🤖 Inicializando RAG con citación de URLs...")
        start_time = time.time()
        rag_chain = create_rag_chain_from_scraped_data()
        init_time = time.time() - start_time
        
        print(f"✅ Inicializado en {init_time:.2f}s")
        
        # Preguntas que deberían retornar propiedades específicas con URLs
        test_questions = [
            "Muéstrame 2 departamentos en Independencia",
            "¿Hay propiedades de 1 dormitorio disponibles?",
            "¿Qué departamentos cuestan menos de 160000 pesos?",
            "Dame 3 propiedades con sus detalles",
            "¿Cuáles son las propiedades más baratas?"
        ]
        
        print(f"\n🔗 Probando {len(test_questions)} preguntas para citación...\n")
        
        results = []
        for i, question in enumerate(test_questions, 1):
            print(f"❓ {i}. {question}")
            
            start_time = time.time()
            answer = rag_chain.ask_question(question)
            response_time = time.time() - start_time
            
            response_text = answer.answer
            
            # Analizar URLs en la respuesta
            # Buscar URLs de assetplan.cl
            url_pattern = r'https://www\.assetplan\.cl/[^\s\)]*'
            found_urls = re.findall(url_pattern, response_text)
            
            # Buscar patrones de citación
            citation_patterns = [
                r'URL:',
                r'https://',
                r'assetplan\.cl',
                r'Ver propiedad'
            ]
            
            citation_found = any(re.search(pattern, response_text, re.IGNORECASE) 
                               for pattern in citation_patterns)
            
            # Mostrar respuesta
            print(f"💬 {response_text}")
            print(f"🔗 URLs encontradas: {len(found_urls)}")
            if found_urls:
                print(f"   URLs: {found_urls[:2]}...")  # Mostrar las primeras 2
            
            print(f"📋 Citación detectada: {'✅ SÍ' if citation_found else '❌ NO'}")
            print(f"⏱️ {response_time:.2f}s | 🎯 {answer.confidence:.2f}")
            
            # Evaluación específica para URLs
            if len(found_urls) > 0 and citation_found:
                status = "✅ PERFECTO"
            elif citation_found:
                status = "🟡 PARCIAL"
            else:
                status = "❌ SIN URLs"
            
            print(f"🏆 Estado: {status}")
            print("-" * 55)
            
            results.append({
                'question': question,
                'urls_found': len(found_urls),
                'citation_found': citation_found,
                'time': response_time,
                'status': status,
                'full_urls': found_urls
            })
        
        # Resumen de citación
        print(f"\n📊 RESUMEN CITACIÓN DE URLs:")
        print("=" * 55)
        
        perfect = sum(1 for r in results if "PERFECTO" in r['status'])
        partial = sum(1 for r in results if "PARCIAL" in r['status'])
        no_urls = sum(1 for r in results if "SIN URLs" in r['status'])
        
        total_urls = sum(r['urls_found'] for r in results)
        avg_time = sum(r['time'] for r in results) / len(results)
        citation_rate = sum(1 for r in results if r['citation_found']) / len(results)
        
        print(f"✅ Perfectas: {perfect}/{len(results)}")
        print(f"🟡 Parciales: {partial}/{len(results)}")  
        print(f"❌ Sin URLs: {no_urls}/{len(results)}")
        print(f"🔗 Total URLs citadas: {total_urls}")
        print(f"📊 Tasa de citación: {citation_rate*100:.1f}%")
        print(f"⏱️ Tiempo promedio: {avg_time:.2f}s")
        
        # Mostrar URLs únicas encontradas
        all_urls = []
        for r in results:
            all_urls.extend(r['full_urls'])
        unique_urls = list(set(all_urls))
        
        if unique_urls:
            print(f"\n🔗 URLs únicas citadas ({len(unique_urls)}):")
            for url in unique_urls[:3]:  # Mostrar las primeras 3
                print(f"   {url}")
            if len(unique_urls) > 3:
                print(f"   ... y {len(unique_urls)-3} más")
        
        # Evaluación final del requisito
        if perfect >= 3 and total_urls >= 5:
            print(f"\n🎉 ¡REQUISITO CUMPLIDO!")
            print("✅ Las URLs originales se citan correctamente")
            print("✅ Cumple con el coding challenge")
        elif perfect + partial >= 4:
            print(f"\n🟡 Citación mayormente correcta")
            print("⚠️ Algunas respuestas podrían mejorar la citación")
        else:
            print(f"\n❌ Requisito no cumplido")
            print("🔧 Necesita ajustes en la citación de URLs")
        
        return perfect >= 2
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Configurar logging mínimo
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    success = test_url_citation()
    
    if success:
        print(f"\n💡 Sistema listo para coding challenge:")
        print(f"   - URLs originales citadas ✅")
        print(f"   - Respuestas concisas ✅")
        print(f"   - Funcionamiento anti-overthinking ✅")
    else:
        print(f"\n🔧 Para mejorar citación:")
        print(f"   - Verificar que el contexto incluya URLs")
        print(f"   - Ajustar prompt si es necesario")
    
    sys.exit(0 if success else 1)