# 🏗️ Architecture Diagram - AssetPlan Property Assistant

## 📊 Sistema Completo: Scraper + RAG Agent

```mermaid
graph TB
    subgraph "🌐 Input Sources"
        ASSETPLAN[AssetPlan.cl Website]
        USER[User Queries]
        CLIENT[Client Applications]
    end
    
    subgraph "🕷️ Web Scraping Layer"
        SCRAPER[Professional Scraper]
        WDF[WebDriver Factory]
        HBS[Human Behavior Simulator]
        AE[AssetPlan Extractor v2]
        DV[Data Validator]
        RM[Retry Manager]
        PM[Performance Monitor]
        
        ASSETPLAN --> SCRAPER
        SCRAPER --> WDF
        SCRAPER --> HBS  
        SCRAPER --> AE
        SCRAPER --> DV
        SCRAPER --> RM
        SCRAPER --> PM
    end
    
    subgraph "💾 Data Storage Layer"
        JSON[properties.json<br/>30+ Properties]
        LOGS[Application Logs]
        
        SCRAPER --> JSON
        SCRAPER --> LOGS
    end
    
    subgraph "🧠 AI/ML Layer"
        VS[FAISS Vector Store]
        EMB[HuggingFace Embeddings<br/>Qwen3-8B-Q6_K]
        LLM[DeepSeek R1 GGUF<br/>8B-Q6_K Local Model]
        RAG[LangChain RAG Chain]
        
        JSON --> VS
        VS --> EMB
        VS --> RAG
        RAG --> LLM
    end
    
    subgraph "⚡ GPU Acceleration"
        CUDA[CUDA 12.1+]
        VRAM[GPU Memory<br/>25 Layers Offloaded]
        BATCH[Optimized Batching<br/>n_batch=256]
        
        LLM --> CUDA
        CUDA --> VRAM
        CUDA --> BATCH
    end
    
    subgraph "🔧 Core Features"
        URLS[URL Citation Engine]
        ANTI[Anti-Overthinking System]
        CONF[Confidence Scoring]
        CLASS[Query Classification]
        
        RAG --> URLS
        RAG --> ANTI
        RAG --> CONF
        RAG --> CLASS
    end
    
    subgraph "🌐 Interface Layer"
        API[FastAPI REST Server<br/>Port 8000]
        CLI[Interactive CLI Chat]
        DOCS[Auto Documentation<br/>/docs, /redoc]
        
        RAG --> API
        RAG --> CLI
        API --> DOCS
    end
    
    subgraph "🧪 Testing & Monitoring"
        TESTS[Test Suite]
        STATUS[System Status Monitor]
        DEBUG[Debug Tools]
        
        API --> TESTS
        CLI --> TESTS
        TESTS --> STATUS
        TESTS --> DEBUG
    end
    
    subgraph "👤 User Interaction"
        USER --> CLI
        CLIENT --> API
        
        API --> RESPONSE[JSON Responses with URLs]
        CLI --> CHAT[Natural Language Chat]
    end
    
    %% Styling
    style URLS fill:#FFD700,stroke:#FF8C00,stroke-width:3px
    style ANTI fill:#87CEEB,stroke:#4682B4,stroke-width:3px
    style CUDA fill:#90EE90,stroke:#32CD32,stroke-width:3px
    style JSON fill:#FFA07A,stroke:#FF6347,stroke-width:2px
    style RAG fill:#DDA0DD,stroke:#9370DB,stroke-width:3px
    style API fill:#F0E68C,stroke:#DAA520,stroke-width:2px
    style CLI fill:#F0E68C,stroke:#DAA520,stroke-width:2px
```

## 🔄 Data Flow: Scraping to Response

```mermaid
sequenceDiagram
    participant User
    participant CLI/API
    participant RAG
    participant VectorStore
    participant LLM
    participant GPU
    participant Data

    Note over User,Data: 1. Initial Setup Phase
    User->>CLI/API: make scrape-quick
    CLI/API->>Data: Execute Professional Scraper
    Data->>Data: Extract 30+ properties with URLs
    Data->>VectorStore: Create FAISS index with embeddings
    
    Note over User,Data: 2. Query Processing Phase
    User->>CLI/API: "Muestra departamento en Independencia"
    CLI/API->>RAG: Process question
    RAG->>VectorStore: Retrieve relevant documents (k=5)
    VectorStore->>RAG: Return properties with URLs
    
    Note over User,Data: 3. Response Generation Phase  
    RAG->>LLM: Generate answer with context
    LLM->>GPU: Offload 25 layers to VRAM
    GPU->>LLM: Accelerated inference
    LLM->>RAG: Generated response
    
    Note over User,Data: 4. Feature Processing Phase
    RAG->>RAG: Apply Anti-Overthinking (temp=0.0)
    RAG->>RAG: Extract URLs from context
    RAG->>RAG: Calculate confidence score
    
    Note over User,Data: 5. Final Response Phase
    RAG->>CLI/API: Complete answer with URLs
    CLI/API->>User: Natural language response with citations
```

## 🎯 Component Interaction Matrix

```mermaid
graph LR
    subgraph "Input Processing"
        A[User Query] --> B[Query Classification]
        B --> C[Context Retrieval]
    end
    
    subgraph "Core Processing"
        C --> D[LLM Generation]
        D --> E[GPU Acceleration]
        E --> F[Response Processing]
    end
    
    subgraph "Output Enhancement"
        F --> G[URL Extraction]
        F --> H[Anti-Overthinking]
        F --> I[Confidence Scoring]
    end
    
    subgraph "Final Output"
        G --> J[Formatted Response]
        H --> J
        I --> J
        J --> K[User Response]
    end
    
    style D fill:#DDA0DD
    style E fill:#90EE90
    style G fill:#FFD700
    style H fill:#87CEEB
```

## 🔧 Technology Stack

```mermaid
mindmap
  root((AssetPlan Assistant))
    Web Scraping
      Selenium WebDriver
      Chrome/Chromium
      Anti-detection techniques
      Human behavior simulation
    
    AI/ML Stack
      LangChain Framework
      DeepSeek R1 Model (GGUF)
      HuggingFace Embeddings
      FAISS Vector Database
      llama.cpp Runtime
    
    GPU Acceleration
      CUDA 12.1+
      RTX 3050+ Support
      Memory Optimization
      Layer Offloading
    
    API & Interface
      FastAPI REST
      Interactive CLI
      Auto Documentation
      CORS Support
    
    Features
      URL Citation
      Anti-Overthinking
      Confidence Scoring
      Query Classification
    
    Testing & Deploy
      Make Commands
      Functional Tests
      Status Monitoring
      Debug Tools
```

## 📊 Performance Metrics Flow

```mermaid
graph TD
    subgraph "Performance Monitoring"
        START[System Start] --> INIT[Model Initialization<br/>~60s]
        INIT --> READY[System Ready]
        
        READY --> QUERY[User Query]
        QUERY --> RETRIEVAL[Vector Retrieval<br/>~1s]
        RETRIEVAL --> GENERATION[LLM Generation<br/>~8-12s]
        GENERATION --> FEATURES[Feature Processing<br/>~1s]
        FEATURES --> RESPONSE[Final Response<br/>Total: ~10s]
        
        RESPONSE --> METRICS[Performance Metrics]
        METRICS --> QUERY
    end
    
    subgraph "GPU Utilization"
        GPU_START[GPU Available] --> GPU_LOAD[Load 25 Layers]
        GPU_LOAD --> GPU_ACCEL[2-3x Speedup]
        GPU_ACCEL --> GPU_MEM[5.5GB VRAM Used]
    end
    
    GENERATION --> GPU_ACCEL
    
    style INIT fill:#FFA07A
    style GENERATION fill:#DDA0DD
    style GPU_ACCEL fill:#90EE90
    style RESPONSE fill:#FFD700
```

## 🛠️ System Architecture Benefits

### ✅ **Scalability Features**
- **Modular Design**: Independent scraping, RAG, and API layers
- **GPU Acceleration**: Horizontal scaling with multiple GPUs
- **Local Models**: No API rate limits or external dependencies
- **Caching**: Persistent FAISS index and embeddings

### ✅ **Reliability Features**  
- **Retry Mechanisms**: Circuit breaker patterns in scraping
- **Error Handling**: Comprehensive error management
- **Health Monitoring**: Real-time system status checks
- **Fallback Options**: CPU fallback when GPU unavailable

### ✅ **Performance Features**
- **Anti-Overthinking**: Optimized response generation
- **Memory Optimization**: Efficient GPU memory usage
- **Vector Caching**: Fast document retrieval
- **Batch Processing**: Optimized inference batching

### ✅ **User Experience Features**
- **URL Citation**: Direct links to original properties
- **Natural Language**: Conversational interface
- **Multiple Interfaces**: API and CLI options
- **Real-time Feedback**: Confidence scoring and metrics

---

**Architecture Status**: ✅ Fully Operational | All components integrated and tested