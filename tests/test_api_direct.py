#!/usr/bin/env python3
"""
Test directo de la API para verificar que las respuestas anti-overthinking funcionen.
"""
import requests
import json
import time

def test_api():
    """Test de la API con las optimizaciones anti-overthinking."""
    base_url = "http://localhost:8000"
    
    print("🌐 TEST API CON ANTI-OVERTHINKING")
    print("=" * 50)
    
    # Verificar que la API esté corriendo
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ API está activa y saludable")
        else:
            print(f"⚠️ API responde pero con status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ API no disponible: {e}")
        print("Asegúrate de que la API esté corriendo en puerto 8000")
        return False
    
    # Preguntas de test
    test_questions = [
        "¿Cuántas propiedades hay disponibles?",
        "¿Hay departamentos en Independencia?",
        "¿Cuál es el precio promedio?",
        "Muéstrame propiedades de 1 dormitorio",
        "¿Qué departamentos cuestan menos de 160000 pesos?"
    ]
    
    print(f"\n🧪 Probando {len(test_questions)} preguntas via API...\n")
    
    results = []
    for i, question in enumerate(test_questions, 1):
        print(f"❓ {i}. {question}")
        
        # Request payload
        payload = {
            "question": question,
            "max_sources": 3
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{base_url}/ask",
                json=payload,
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                answer_text = data.get("answer", "")
                confidence = data.get("confidence", 0)
                sources_count = len(data.get("sources", []))
                
                # Análisis de la respuesta
                word_count = len(answer_text.split())
                
                # Detectar overthinking
                overthinking_words = ["además", "también", "por otro lado", "en conclusión", "finalmente"]
                overthinking_count = sum(1 for word in overthinking_words if word.lower() in answer_text.lower())
                
                print(f"💬 {answer_text[:100]}{'...' if len(answer_text) > 100 else ''}")
                print(f"📊 Palabras: {word_count} | Overthinking: {overthinking_count}")
                print(f"⏱️ {response_time:.2f}s | 🎯 {confidence:.2f} | 📋 {sources_count} fuentes")
                
                # Evaluación
                if word_count <= 150 and overthinking_count == 0 and response_time <= 20:
                    status = "✅ EXCELENTE"
                elif word_count <= 200 and overthinking_count <= 1:
                    status = "🟡 BUENO" 
                else:
                    status = "❌ MEJORAR"
                
                print(f"📋 Estado: {status}")
                
                results.append({
                    'question': question,
                    'words': word_count,
                    'overthinking': overthinking_count,
                    'time': response_time,
                    'status': status,
                    'success': True
                })
                
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                print(f"   {response.text}")
                results.append({
                    'question': question,
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                })
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
            results.append({
                'question': question,
                'success': False,
                'error': str(e)
            })
        
        print("-" * 50)
    
    # Resumen
    print(f"\n📈 RESUMEN API ANTI-OVERTHINKING:")
    print("=" * 50)
    
    successful = [r for r in results if r.get('success')]
    excellent = sum(1 for r in successful if "EXCELENTE" in r.get('status', ''))
    good = sum(1 for r in successful if "BUENO" in r.get('status', ''))
    
    if successful:
        avg_words = sum(r['words'] for r in successful) / len(successful)
        avg_time = sum(r['time'] for r in successful) / len(successful)
        total_overthinking = sum(r['overthinking'] for r in successful)
        
        print(f"✅ Exitosos: {len(successful)}/{len(results)}")
        print(f"✅ Excelentes: {excellent}/{len(successful)}")
        print(f"🟡 Buenos: {good}/{len(successful)}")
        print(f"📊 Promedio palabras: {avg_words:.1f}")
        print(f"⏱️ Promedio tiempo: {avg_time:.2f}s")
        print(f"🧠 Total overthinking: {total_overthinking}")
        
        if excellent >= 3 and total_overthinking <= 2:
            print(f"\n🎉 ¡API ANTI-OVERTHINKING PERFECTA!")
            print("Las optimizaciones funcionan correctamente via API")
            return True
        elif excellent + good >= 4:
            print(f"\n✅ API anti-overthinking funciona bien")
            return True
        else:
            print(f"\n⚠️ API necesita más optimización")
            return False
    else:
        print("❌ No se pudieron completar las pruebas")
        return False

if __name__ == "__main__":
    success = test_api()
    
    if success:
        print(f"\n💡 La API está lista para uso:")
        print(f"   - Endpoint: http://localhost:8000/ask")
        print(f"   - Docs: http://localhost:8000/docs")
        print(f"   - Respuestas concisas y directas ✅")
    else:
        print(f"\n🔧 Verifica que la API esté ejecutándose")
    
    exit(0 if success else 1)