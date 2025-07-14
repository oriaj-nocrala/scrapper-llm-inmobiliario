#!/usr/bin/env python3
"""
Quick test para una sola pregunta sobre URLs.
"""
import os
import sys
import time
from pathlib import Path

# Configuración optimizada
os.environ["USE_LOCAL_MODELS"] = "true"
os.environ["USE_GPU"] = "true"
os.environ["GPU_LAYERS"] = "25"

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def quick_test():
    """Test rápido para una pregunta."""
    try:
        from src.rag.property_rag_chain import create_rag_chain_from_scraped_data
        
        print("🔗 Quick URL Test")
        print("=" * 30)
        
        rag_chain = create_rag_chain_from_scraped_data()
        
        question = "Muestra 1 departamento en Independencia con su URL"
        print(f"❓ {question}")
        
        start_time = time.time()
        answer = rag_chain.ask_question(question)
        response_time = time.time() - start_time
        
        print(f"💬 Respuesta: {answer.answer}")
        print(f"⏱️ Tiempo: {response_time:.2f}s")
        
        # Check if URL is included
        if "https://" in answer.answer:
            print("✅ URL encontrada en respuesta")
        else:
            print("❌ No URL en respuesta")
            
        # Show sources
        print(f"\n📋 Fuentes disponibles: {len(answer.sources)}")
        for i, source in enumerate(answer.sources[:2]):
            print(f"  {i+1}. {source.get('title', 'N/A')}")
            print(f"     URL: {source.get('url', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.WARNING)
    quick_test()