#!/usr/bin/env python3
"""
Startup script for the AssetPlan Property Assistant API.
"""
import sys
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.config import settings


def setup_directories():
    """Create necessary directories."""
    directories = [
        settings.data_dir,
        settings.logs_dir,
        Path(settings.faiss_index_path).parent
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")


def check_requirements():
    """Check if all requirements are met."""
    print("🔍 Checking requirements...")
    
    # Check if properties data exists
    properties_file = Path(settings.properties_json_path)
    if not properties_file.exists():
        print(f"❌ Properties file not found: {properties_file}")
        print("Run the scraper first: python -m src.scraper.professional_scraper")
        return False
    
    # Check API key requirements based on model configuration
    if settings.use_local_models:
        print("🏠 Using LOCAL models (GGUF)")
        # Check if local model files exist
        local_model = Path(settings.local_llm_model_path)
        if not local_model.exists():
            print(f"❌ Local model not found: {local_model}")
            print("Ensure GGUF model is in ml-models/ directory")
            return False
        print(f"✓ Local model found: {local_model}")
    else:
        print("🌐 Using OpenAI models")
        if not settings.openai_api_key:
            print("❌ OPENAI_API_KEY environment variable not set")
            print("Set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
            print("Or enable local models: export USE_LOCAL_MODELS=true")
            return False
    
    print("✓ All requirements met")
    return True


def main():
    """Main startup function."""
    print("🏠 AssetPlan Property Assistant API")
    print("=" * 50)
    
    # Setup directories
    setup_directories()
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(settings.log_file, encoding='utf-8')
        ]
    )
    
    print("\n🚀 Starting API server...")
    print(f"📍 Host: {settings.api_host}:{settings.api_port}")
    
    if settings.use_local_models:
        print(f"🏠 Model: LOCAL ({Path(settings.local_llm_model_path).name})")
        print(f"⚙️  Context: {settings.local_llm_n_ctx}, Threads: {settings.local_llm_n_threads}")
    else:
        print(f"🌐 Model: OpenAI ({settings.openai_model})")
    
    print(f"📚 Properties: {settings.properties_json_path}")
    print(f"🔗 Documentation: http://localhost:{settings.api_port}/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        # Start the API server
        import uvicorn
        from src.api.property_api import app
        
        uvicorn.run(
            app,
            host=settings.api_host,
            port=settings.api_port,
            reload=settings.api_debug,
            log_level=settings.log_level.lower()
        )
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()