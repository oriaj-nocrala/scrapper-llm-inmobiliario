#!/usr/bin/env python3
"""
Test de GPU solo para llama.cpp LLM, usando OpenAI embeddings para evitar conflictos.
"""
import os
import sys
import time
from pathlib import Path

# Configurar para usar LLM local con embeddings OpenAI
os.environ["USE_LOCAL_MODELS"] = "true"
os.environ["USE_GPU"] = "true"
os.environ["GPU_LAYERS"] = "35"

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_gpu_llama_only():
    """Test GPU solo para LLM llama.cpp."""
    print("🚀 TEST GPU LLAMA.CPP (con OpenAI embeddings)")
    print("=" * 55)
    
    # Verificar datos
    properties_file = Path("data/properties.json")
    if not properties_file.exists():
        print("❌ No hay datos scraped disponibles")
        return False
    
    # Verificar API key de OpenAI para embeddings
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OPENAI_API_KEY no configurado")
        print("Para test completo con embeddings locales, configura la API key")
        print("Por ahora solo probamos el LLM local")
    
    try:
        print("🤖 Inicializando LLM local con GPU...")
        
        from src.rag.property_rag_chain import create_llm_model
        
        start_time = time.time()
        llm = create_llm_model()
        init_time = time.time() - start_time
        
        print(f"✅ LLM GPU inicializado en {init_time:.2f}s")
        
        # Test directo del LLM
        test_prompt = "¿Cuántas propiedades inmobiliarias hay en total?"
        print(f"\n❓ Prompt: {test_prompt}")
        
        start_time = time.time()
        response = llm.invoke(test_prompt)
        response_time = time.time() - start_time
        
        print(f"💬 Respuesta: {response[:200]}...")
        print(f"⏱️ Tiempo de respuesta: {response_time:.2f}s")
        
        if response_time < 5:
            print(f"\n🚀 ¡GPU súper rápido! Respuesta en {response_time:.2f}s")
        elif response_time < 15:
            print(f"\n✅ GPU funcionando bien en {response_time:.2f}s")
        else:
            print(f"\n⚠️ Respuesta lenta ({response_time:.2f}s)")
            print("   Intenta: export GPU_LAYERS=40 para más velocidad")
        
        # Verificar uso de memoria GPU
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,nounits,noheader'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                memory_info = result.stdout.strip().split(', ')
                used_mb = int(memory_info[0])
                total_mb = int(memory_info[1])
                
                print(f"\n📊 Memoria GPU: {used_mb}MB / {total_mb}MB ({used_mb/total_mb*100:.1f}%)")
                
                if used_mb > total_mb * 0.8:
                    print("⚠️ Memoria GPU alta, considera reducir GPU_LAYERS")
                else:
                    print("✅ Uso de memoria GPU normal")
        except:
            pass
        
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
    
    success = test_gpu_llama_only()
    
    if success:
        print(f"\n💡 Optimización GPU:")
        print(f"   - Más capas GPU: export GPU_LAYERS=40")
        print(f"   - Menos memoria: export GPU_LAYERS=25")
        print(f"   - Solo CPU: export USE_GPU=false")
    
    sys.exit(0 if success else 1)