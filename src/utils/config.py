import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Model Configuration - Switch between OpenAI and Local
    use_local_models: bool = os.getenv("USE_LOCAL_MODELS", "false").lower() == "true"
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = "gpt-3.5-turbo"
    
    # Local Models Configuration (GGUF files)
    local_llm_model_path: str = "ml-models/DeepSeek-R1-0528-Qwen3-8B-Q6_K.gguf"
    local_embedding_model_path: str = "ml-models/Qwen3-Embedding-8B-Q6_K.gguf"
    local_embedding_hf_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # Fallback embedding model
    local_llm_n_ctx: int = 4096  # Context window size
    local_llm_n_threads: int = 8  # Number of threads
    local_llm_temperature: float = 0.1  # Low temperature for factual responses
    
    # GPU Configuration
    use_gpu: bool = os.getenv("USE_GPU", "true").lower() == "true"  # Enable GPU by default if available
    gpu_layers: int = int(os.getenv("GPU_LAYERS", "25"))  # Number of layers to offload to GPU (RTX 3050: 25-30 optimal)
    gpu_memory_limit: float = float(os.getenv("GPU_MEMORY_LIMIT", "5.5"))  # GPU memory limit in GB (conservative for 8GB)
    embedding_device: str = "cuda" if use_gpu else "cpu"  # Device for embeddings
    
    # Scraping Configuration
    scraping_delay: float = 0.5
    max_properties: int = 50  # Updated for challenge requirement
    headless_browser: bool = True
    
    # Vector Store Configuration
    embedding_model: str = "text-embedding-ada-002"  # Will be overridden if using local models
    faiss_index_path: str = "data/faiss_index"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    
    # RAG Configuration
    retrieval_k: int = 5
    similarity_threshold: float = 0.7
    max_sources: int = 10
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/application.log"
    
    # Data Paths
    properties_json_path: str = "data/properties.json"
    logs_dir: str = "logs"
    data_dir: str = "data"
    
    model_config = {"env_file": ".env"}


settings = Settings()