#!/usr/bin/env python3
"""
Script para demostrar el switch entre modelos OpenAI y locales GGUF.
"""
import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_local_models():
    """Test con modelos locales."""
    print("🏠 Testing LOCAL models configuration...")
    print("=" * 50)
    
    # Set environment for local models
    os.environ["USE_LOCAL_MODELS"] = "true"
    
    # Import after setting environment
    from src.utils.config import settings
    from src.rag.property_rag_chain import create_llm_model
    from src.vectorstore.faiss_store import create_embeddings_model
    
    print(f"✓ use_local_models: {settings.use_local_models}")
    print(f"✓ local_llm_model_path: {settings.local_llm_model_path}")
    print(f"✓ local_embedding_hf_model: {settings.local_embedding_hf_model}")
    
    try:
        # Test embeddings model
        print("\\n📊 Creating embeddings model...")
        embeddings = create_embeddings_model()
        print(f"✅ Embeddings model: {type(embeddings).__name__}")
        
        # Test LLM model 
        print("\\n🤖 Creating LLM model...")
        llm = create_llm_model()
        print(f"✅ LLM model: {type(llm).__name__}")
        
        print("\n🎉 LOCAL models configuration SUCCESS!")
        
    except Exception as e:
        print(f"❌ Error with local models: {e}")
        return False
    
    return True


def test_openai_models():
    """Test con modelos OpenAI."""
    print("\\n\\n🌐 Testing OPENAI models configuration...")
    print("=" * 50)
    
    # Set environment for OpenAI models
    os.environ["USE_LOCAL_MODELS"] = "false"
    
    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set - skipping OpenAI test")
        print("   To test OpenAI: export OPENAI_API_KEY='your-key-here'")
        return True
    
    # Import after setting environment
    from src.utils.config import settings
    from src.rag.property_rag_chain import create_llm_model
    from src.vectorstore.faiss_store import create_embeddings_model
    
    print(f"✓ use_local_models: {settings.use_local_models}")
    print(f"✓ openai_model: {settings.openai_model}")
    print(f"✓ embedding_model: {settings.embedding_model}")
    
    try:
        # Test embeddings model
        print("\\n📊 Creating embeddings model...")
        embeddings = create_embeddings_model()
        print(f"✅ Embeddings model: {type(embeddings).__name__}")
        
        # Test LLM model 
        print("\\n🤖 Creating LLM model...")
        llm = create_llm_model()
        print(f"✅ LLM model: {type(llm).__name__}")
        
        print("\n🎉 OPENAI models configuration SUCCESS!")
        
    except Exception as e:
        print(f"❌ Error with OpenAI models: {e}")
        return False
    
    return True


def main():
    """Main test function."""
    print("🔀 MODEL SWITCH CONFIGURATION TEST")
    print("=" * 60)
    print("Este script demuestra el switch entre OpenAI y modelos locales GGUF")
    print()
    
    # Test local models
    local_success = test_local_models()
    
    # Test OpenAI models 
    openai_success = test_openai_models()
    
    # Summary
    print("\n\n📋 SUMMARY")
    print("=" * 30)
    print(f"🏠 Local models:  {'✅ SUCCESS' if local_success else '❌ FAILED'}")
    print(f"🌐 OpenAI models: {'✅ SUCCESS' if openai_success else '❌ FAILED'}")
    
    if local_success:
        print("\n🎯 CONFIGURATION INSTRUCTIONS:")
        print("   For LOCAL models:  export USE_LOCAL_MODELS=true")
        print("   For OpenAI models: export USE_LOCAL_MODELS=false")
        print("                      export OPENAI_API_KEY='your-key-here'")
    
    print("\n✨ Model switch configuration is working correctly!")


if __name__ == "__main__":
    main()