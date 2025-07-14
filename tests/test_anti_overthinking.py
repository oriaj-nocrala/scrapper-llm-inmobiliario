#!/usr/bin/env python3
"""
Test anti-overthinking para verificar que el modelo DeepSeek responda concisamente.
"""
import os
import sys
import time
from pathlib import Path

# Configuración optimizada anti-overthinking
os.environ["USE_LOCAL_MODELS"] = "true"
os.environ["USE_GPU"] = "true"
os.environ["GPU_LAYERS"] = "25"

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_anti_overthinking():
    """Test para verificar respuestas concisas sin divagación."""
    print("🎯 TEST ANTI-OVERTHINKING DEEPSEEK")
    print("=" * 50)
    print("Objetivo: Respuestas directas y concisas sin divagación")
    print()
    
    try:
        from src.rag.property_rag_chain import create_rag_chain_from_scraped_data
        
        print("🤖 Inicializando RAG con configuración anti-overthinking...")
        start_time = time.time()
        rag_chain = create_rag_chain_from_scraped_data()
        init_time = time.time() - start_time
        
        print(f"✅ Inicializado en {init_time:.2f}s")
        
        # Preguntas diseñadas para provocar overthinking
        test_questions = [
            "¿Cuántas propiedades hay disponibles?",
            "¿Hay departamentos en Independencia?", 
            "¿Cuál es el precio promedio?",
            "Muéstrame propiedades de 1 dormitorio",
            "¿Qué departamentos cuestan menos de 200000 pesos?"
        ]
        
        print(f"\n🧪 Probando {len(test_questions)} preguntas específicas...\n")
        
        results = []
        for i, question in enumerate(test_questions, 1):
            print(f"❓ {i}. {question}")
            
            start_time = time.time()
            answer = rag_chain.ask_question(question)
            response_time = time.time() - start_time
            
            # Análisis de la respuesta
            response_text = answer.answer
            word_count = len(response_text.split())
            line_count = len(response_text.split('\\n'))
            
            # Detectar signos de overthinking
            overthinking_words = ["además", "también", "por otro lado", "en conclusión", "finalmente", "cabe mencionar"]
            overthinking_count = sum(1 for word in overthinking_words if word.lower() in response_text.lower())
            
            # Mostrar resultado
            print(f"💬 {response_text[:100]}{'...' if len(response_text) > 100 else ''}")
            print(f"📊 Palabras: {word_count} | Líneas: {line_count} | Overthinking: {overthinking_count}")
            print(f"⏱️ {response_time:.2f}s | 🎯 {answer.confidence:.2f}")
            
            # Evaluación
            if word_count <= 150 and overthinking_count == 0 and response_time <= 15:
                status = "✅ EXCELENTE"
            elif word_count <= 200 and overthinking_count <= 1 and response_time <= 25:
                status = "🟡 BUENO"
            else:
                status = "❌ MEJORAR"
            
            print(f"📋 Estado: {status}")
            print("-" * 50)
            
            results.append({
                'question': question,
                'words': word_count,
                'overthinking': overthinking_count,
                'time': response_time,
                'status': status
            })
        
        # Resumen final
        print(f"\n📈 RESUMEN ANTI-OVERTHINKING:")
        print("=" * 50)
        
        excellent = sum(1 for r in results if "EXCELENTE" in r['status'])
        good = sum(1 for r in results if "BUENO" in r['status'])
        poor = sum(1 for r in results if "MEJORAR" in r['status'])
        
        avg_words = sum(r['words'] for r in results) / len(results)
        avg_time = sum(r['time'] for r in results) / len(results)
        total_overthinking = sum(r['overthinking'] for r in results)
        
        print(f"✅ Excelentes: {excellent}/{len(results)}")
        print(f"🟡 Buenos: {good}/{len(results)}")  
        print(f"❌ Mejorables: {poor}/{len(results)}")
        print(f"📊 Promedio palabras: {avg_words:.1f}")
        print(f"⏱️ Promedio tiempo: {avg_time:.2f}s")
        print(f"🧠 Total overthinking: {total_overthinking}")
        
        # Evaluación global
        if excellent >= 3 and total_overthinking <= 2:
            print(f"\n🎉 ¡ANTI-OVERTHINKING EXITOSO!")
            print("El modelo responde de forma concisa y directa")
        elif excellent + good >= 4:
            print(f"\n✅ Anti-overthinking funciona bien")
            print("Mayormente respuestas directas")
        else:
            print(f"\n⚠️ Necesita más optimización")
            print("Aún hay tendencia a divagar")
        
        return excellent >= 2
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Configurar logging mínimo
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    success = test_anti_overthinking()
    
    if success:
        print(f"\n💡 Configuración optimizada funcionando")
        print(f"   - Temperature: 0.0 (determinístico)")
        print(f"   - Max tokens: 300 (conciso)")
        print(f"   - Stop tokens: agresivos")
        print(f"   - Prompt: directo y estructurado")
    else:
        print(f"\n🔧 Para mejorar aún más:")
        print(f"   - Considera probar otro modelo GGUF")
        print(f"   - Reducir más max_tokens")
        print(f"   - Ajustar stop tokens")
    
    sys.exit(0 if success else 1)