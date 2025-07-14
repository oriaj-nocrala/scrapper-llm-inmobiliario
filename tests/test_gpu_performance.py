#!/usr/bin/env python3
"""
Test de rendimiento GPU vs CPU para el sistema RAG.
Compara velocidad de inferencia entre configuraciones.
"""
import os
import sys
import time
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_gpu_performance():
    """Test comparativo de rendimiento GPU vs CPU."""
    print("🚀 TEST DE RENDIMIENTO GPU vs CPU")
    print("=" * 60)
    
    # Verificar datos
    properties_file = Path("data/properties.json")
    if not properties_file.exists():
        print("❌ No hay datos scraped disponibles")
        print("Ejecuta: python run_scraper_rag.py --mode quick --max-properties 10")
        return False
    
    test_questions = [
        "¿Cuántas propiedades hay disponibles?",
        "Muéstrame departamentos en Independencia",
        "¿Hay propiedades bajo 200000 pesos?"
    ]
    
    results = {}
    
    # Test 1: GPU
    print("\n🚀 PRUEBA 1: GPU ACELERADO")
    print("-" * 40)
    
    os.environ["USE_LOCAL_MODELS"] = "true"
    os.environ["USE_GPU"] = "true"
    os.environ["GPU_LAYERS"] = "35"
    
    try:
        # Reiniciar importaciones para aplicar nueva configuración
        for module in list(sys.modules.keys()):
            if module.startswith('src.'):
                del sys.modules[module]
        
        from src.rag.property_rag_chain import create_rag_chain_from_scraped_data
        
        print("🤖 Inicializando RAG con GPU...")
        start_init = time.time()
        rag_gpu = create_rag_chain_from_scraped_data()
        init_time_gpu = time.time() - start_init
        
        print(f"✅ RAG GPU inicializado en {init_time_gpu:.2f}s")
        
        # Test de velocidad
        gpu_times = []
        for i, question in enumerate(test_questions, 1):
            print(f"\n❓ Pregunta {i}: {question}")
            
            start_time = time.time()
            answer = rag_gpu.ask_question(question)
            response_time = time.time() - start_time
            gpu_times.append(response_time)
            
            print(f"💬 Respuesta: {answer.answer[:100]}...")
            print(f"⏱️ Tiempo: {response_time:.2f}s")
            print(f"📊 Confianza: {answer.confidence:.2f}")
        
        results['gpu'] = {
            'init_time': init_time_gpu,
            'response_times': gpu_times,
            'avg_response_time': sum(gpu_times) / len(gpu_times),
            'total_time': sum(gpu_times)
        }
        
        print(f"\n✅ GPU Test completado - Promedio: {results['gpu']['avg_response_time']:.2f}s")
        
    except Exception as e:
        print(f"❌ Error en test GPU: {e}")
        results['gpu'] = {'error': str(e)}
    
    # Test 2: CPU
    print("\n\n💻 PRUEBA 2: CPU SOLO")
    print("-" * 40)
    
    os.environ["USE_GPU"] = "false"
    
    try:
        # Reiniciar importaciones para aplicar nueva configuración
        for module in list(sys.modules.keys()):
            if module.startswith('src.'):
                del sys.modules[module]
        
        from src.rag.property_rag_chain import create_rag_chain_from_scraped_data
        
        print("🤖 Inicializando RAG con CPU...")
        start_init = time.time()
        rag_cpu = create_rag_chain_from_scraped_data()
        init_time_cpu = time.time() - start_init
        
        print(f"✅ RAG CPU inicializado en {init_time_cpu:.2f}s")
        
        # Test de velocidad
        cpu_times = []
        for i, question in enumerate(test_questions, 1):
            print(f"\n❓ Pregunta {i}: {question}")
            
            start_time = time.time()
            answer = rag_cpu.ask_question(question)
            response_time = time.time() - start_time
            cpu_times.append(response_time)
            
            print(f"💬 Respuesta: {answer.answer[:100]}...")
            print(f"⏱️ Tiempo: {response_time:.2f}s")
            print(f"📊 Confianza: {answer.confidence:.2f}")
        
        results['cpu'] = {
            'init_time': init_time_cpu,
            'response_times': cpu_times,
            'avg_response_time': sum(cpu_times) / len(cpu_times),
            'total_time': sum(cpu_times)
        }
        
        print(f"\n✅ CPU Test completado - Promedio: {results['cpu']['avg_response_time']:.2f}s")
        
    except Exception as e:
        print(f"❌ Error en test CPU: {e}")
        results['cpu'] = {'error': str(e)}
    
    # Comparación final
    print("\n\n📊 COMPARACIÓN DE RENDIMIENTO")
    print("=" * 60)
    
    if 'gpu' in results and 'cpu' in results and 'error' not in results['gpu'] and 'error' not in results['cpu']:
        gpu_avg = results['gpu']['avg_response_time']
        cpu_avg = results['cpu']['avg_response_time']
        speedup = cpu_avg / gpu_avg
        
        print(f"🚀 GPU - Tiempo promedio: {gpu_avg:.2f}s")
        print(f"💻 CPU - Tiempo promedio: {cpu_avg:.2f}s")
        print(f"⚡ Aceleración GPU: {speedup:.2f}x más rápido")
        
        if speedup > 1.5:
            print("🎉 ¡GPU proporciona aceleración significativa!")
        elif speedup > 1.1:
            print("✅ GPU es más rápido que CPU")
        else:
            print("⚠️ Diferencia mínima, considera verificar configuración GPU")
            
        # Detalles por pregunta
        print(f"\n📋 Detalles por pregunta:")
        for i, question in enumerate(test_questions):
            gpu_time = results['gpu']['response_times'][i]
            cpu_time = results['cpu']['response_times'][i]
            question_speedup = cpu_time / gpu_time
            print(f"   {i+1}. GPU: {gpu_time:.2f}s | CPU: {cpu_time:.2f}s | Speedup: {question_speedup:.2f}x")
            
    else:
        print("❌ No se pudo completar la comparación debido a errores")
        if 'gpu' in results and 'error' in results['gpu']:
            print(f"   GPU Error: {results['gpu']['error']}")
        if 'cpu' in results and 'error' in results['cpu']:
            print(f"   CPU Error: {results['cpu']['error']}")
    
    return True

def test_gpu_memory_usage():
    """Test para verificar uso de memoria GPU."""
    print("\n🔍 VERIFICACIÓN DE MEMORIA GPU")
    print("-" * 40)
    
    try:
        import subprocess
        result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,nounits,noheader'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            memory_info = result.stdout.strip().split(', ')
            used_mb = int(memory_info[0])
            total_mb = int(memory_info[1])
            
            print(f"📊 Memoria GPU: {used_mb}MB / {total_mb}MB ({used_mb/total_mb*100:.1f}%)")
            
            if used_mb > total_mb * 0.9:
                print("⚠️ Advertencia: Memoria GPU casi llena, considera reducir GPU_LAYERS")
            elif used_mb > total_mb * 0.7:
                print("✅ Uso de memoria GPU normal")
            else:
                print("💡 Memoria GPU disponible, puedes aumentar GPU_LAYERS para más velocidad")
        else:
            print("❌ No se pudo obtener información de memoria GPU")
            
    except Exception as e:
        print(f"❌ Error verificando memoria GPU: {e}")

if __name__ == "__main__":
    # Configurar logging mínimo
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    print("🎯 Test de Rendimiento RAG - GPU vs CPU")
    print("Este test compara la velocidad de inferencia entre GPU y CPU")
    print()
    
    success = test_gpu_performance()
    
    if success:
        test_gpu_memory_usage()
        print(f"\n🎉 Test de rendimiento completado!")
        
        print(f"\n💡 CONSEJOS DE OPTIMIZACIÓN:")
        print(f"   - Para más velocidad GPU: export GPU_LAYERS=40")
        print(f"   - Para menos memoria GPU: export GPU_LAYERS=25")
        print(f"   - Para solo embeddings GPU: export GPU_LAYERS=0")
        print(f"   - Para CPU solamente: export USE_GPU=false")
    
    sys.exit(0 if success else 1)