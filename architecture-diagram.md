# 🏗️ Arquitectura - Scrapper LLM Inmobiliario

## 📊 Diagrama de Arquitectura Principal

```mermaid
graph TB
    %% Usuarios y Interfaces
    User[👤 Usuario] --> Dashboard[🎛️ Dashboard Web]
    User --> API[🔌 FastAPI]
    User --> CLI[💻 CLI Tools]
    
    %% Capa de Aplicación
    subgraph "🌐 Capa de Presentación"
        Dashboard --> |HTTP| DashboardServer[📊 Dashboard Server]
        API --> |REST| APIServer[🔌 API Server]
        CLI --> |Direct| CLITools[⚙️ CLI Tools]
    end
    
    %% Capa de Servicios
    subgraph "⚙️ Capa de Servicios"
        DashboardServer --> ScraperService[🕷️ Scraper Service]
        APIServer --> ScraperService
        CLITools --> ScraperService
        
        ScraperService --> RAGService[🤖 RAG Service]
        ScraperService --> AnalysisService[📊 Analysis Service]
        ScraperService --> GodClassService[🧠 God Class Service]
    end
    
    %% Capa de Dominio
    subgraph "🏢 Capa de Dominio"
        ScraperService --> AssetPlan[🏠 AssetPlan Extractor]
        ScraperService --> DataValidator[✅ Data Validator]
        ScraperService --> NavigationManager[🧭 Navigation Manager]
        
        RAGService --> PropertyRAG[🏡 Property RAG Chain]
        AnalysisService --> SmartAnalyzer[🔍 Smart Code Analyzer]
        GodClassService --> GodClassRefactor[🧠 God Class Refactor]
    end
    
    %% Capa de Infraestructura
    subgraph "🔧 Capa de Infraestructura"
        AssetPlan --> WebDriver[🌐 Selenium WebDriver]
        DataValidator --> DataParser[📝 Data Parser]
        NavigationManager --> HumanBehavior[👤 Human Behavior]
        
        PropertyRAG --> VectorStore[📚 FAISS Vector Store]
        SmartAnalyzer --> CodeAnalysis[📊 Code Analysis Tools]
        GodClassRefactor --> AIModels[🤖 Local AI Models]
    end
    
    %% Persistencia
    subgraph "💾 Capa de Persistencia"
        VectorStore --> FAISSIndex[(🗂️ FAISS Index)]
        DataParser --> JSONData[(📄 JSON Data)]
        CodeAnalysis --> Metrics[(📊 Metrics)]
        AIModels --> EmbeddingModels[(🧠 Embedding Models)]
    end
    
    %% Recursos Externos
    subgraph "🌍 Recursos Externos"
        WebDriver --> AssetPlanSite[🏢 AssetPlan.cl]
        WebDriver --> ChromeDriver[🚗 Chrome Driver]
        AIModels --> Qwen3Model[🤖 Qwen3 Model]
    end
    
    %% Estilos
    classDef userInterface fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef service fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef domain fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef infrastructure fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef persistence fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef external fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    
    class User,Dashboard,API,CLI userInterface
    class DashboardServer,APIServer,CLITools,ScraperService,RAGService,AnalysisService,GodClassService service
    class AssetPlan,DataValidator,NavigationManager,PropertyRAG,SmartAnalyzer,GodClassRefactor domain
    class WebDriver,DataParser,HumanBehavior,VectorStore,CodeAnalysis,AIModels infrastructure
    class FAISSIndex,JSONData,Metrics,EmbeddingModels persistence
    class AssetPlanSite,ChromeDriver,Qwen3Model external
```

## 🔄 Diagrama de Flujo de Scraping

```mermaid
sequenceDiagram
    participant U as 👤 Usuario
    participant D as 🎛️ Dashboard
    participant S as 🕷️ Scraper
    participant W as 🌐 WebDriver
    participant A as 🏢 AssetPlan.cl
    participant P as 📝 Parser
    participant V as 📚 VectorStore
    participant R as 🤖 RAG
    
    U->>D: Iniciar Scraping
    D->>S: Ejecutar Scraper
    S->>W: Configurar WebDriver
    W->>A: Navegar a AssetPlan
    A-->>W: Página HTML
    W-->>S: Elementos extraídos
    S->>P: Parsear datos
    P-->>S: Propiedades estructuradas
    S->>V: Almacenar en vector store
    V-->>S: Confirmación
    S->>R: Indexar para RAG
    R-->>S: Índice actualizado
    S-->>D: Resultados
    D-->>U: Mostrar propiedades
```

## 🧠 Diagrama de Análisis de God Classes

```mermaid
flowchart TD
    Start[🚀 Iniciar Análisis] --> Scan[🔍 Escanear Código Python]
    Scan --> Detect{🎯 Detectar God Classes<br/>≥10 métodos}
    
    Detect -->|No encontradas| NoGodClasses[✅ No God Classes]
    Detect -->|Encontradas| LoadModel[📥 Cargar Modelo Qwen3]
    
    LoadModel --> OptimalConfig[⚙️ Configuración Óptima VRAM]
    OptimalConfig --> GenerateEmbeddings[🧮 Generar Embeddings]
    GenerateEmbeddings --> SemanticAnalysis[🔍 Análisis Semántico]
    
    SemanticAnalysis --> ClusterMethods[🎯 Agrupar Métodos]
    ClusterMethods --> RiskAnalysis[⚠️ Análisis de Riesgos]
    RiskAnalysis --> RefactorPlan[📋 Plan de Refactorización]
    
    RefactorPlan --> Output[📊 Reporte Final]
    NoGodClasses --> Output
    
    Output --> Dashboard[🎛️ Dashboard]
    Output --> JSONReport[📄 Reporte JSON]
    
    style Start fill:#4caf50,color:#fff
    style NoGodClasses fill:#8bc34a,color:#fff
    style LoadModel fill:#2196f3,color:#fff
    style Output fill:#ff9800,color:#fff
    style Dashboard fill:#9c27b0,color:#fff
```

## 🐳 Diagrama de Containerización

```mermaid
graph TB
    subgraph "🐳 Docker Container"
        subgraph "📦 Application Layer"
            API[🔌 FastAPI Server :8000]
            Dashboard[🎛️ Dashboard Server :8080]
            Scraper[🕷️ Scraper Service]
            Tools[⚙️ CLI Tools]
        end
        
        subgraph "🤖 AI Layer"
            Qwen3[🧠 Qwen3 Models]
            FAISS[📚 FAISS Index]
            Cache[⚡ Analysis Cache]
        end
        
        subgraph "🌐 Browser Layer"
            Chrome[🌐 Chrome Browser]
            ChromeDriver[🚗 ChromeDriver]
        end
        
        subgraph "💾 Data Layer"
            Data[📁 /app/data]
            Logs[📝 /app/logs]
            Models[🤖 /app/ml-models]
        end
    end
    
    subgraph "🌍 Host System"
        DataVol[📁 ./data:/app/data]
        LogsVol[📝 ./logs:/app/logs]
        ModelsVol[🤖 ./ml-models:/app/ml-models]
    end
    
    subgraph "🌐 External Services"
        AssetPlan[🏢 AssetPlan.cl]
        GitHub[🐙 GitHub Registry]
    end
    
    API --> |HTTP| Host[🖥️ Host :8000]
    Dashboard --> |HTTP| Host2[🖥️ Host :8080]
    Scraper --> Chrome
    Chrome --> AssetPlan
    
    Data --> DataVol
    Logs --> LogsVol
    Models --> ModelsVol
    
    GitHub --> |Pull Image| Container[🐳 Container]
    
    style Container fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    style Host fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    style AssetPlan fill:#fff3e0,stroke:#f57c00,stroke-width:2px
```

## 🔧 Diagrama de Herramientas

```mermaid
mindmap
  root((🛠️ Scrapper LLM<br/>Tools))
    
    🎛️ Dashboard
      📊 Categorized Dashboard
      🧠 God Classes Tab
      📈 Metrics Viewer
      🤖 RAG Assistant
      
    🔍 Code Analysis
      📊 Smart Analyzer
      📏 Quality Scorer
      🔍 Duplicate Detector
      📋 Metrics Generator
      
    🧠 God Class Refactor
      🤖 AI Analysis
      📊 Semantic Clustering
      ⚠️ Risk Assessment
      📋 Refactor Planning
      
    📊 Data Processing
      🔗 RAG System
      📝 Chunked Analysis
      🧮 Embedding Engine
      🗂️ Vector Store
      
    ⚙️ Utilities
      🔧 Aggressive Refactor
      🧹 Cleanup Tools
      🔍 Orphan Detection
      🤖 Code Assistant
```

## 🚀 Diagrama de CI/CD

```mermaid
gitGraph
    commit id: "🚀 Initial"
    branch develop
    checkout develop
    
    commit id: "✨ Feature"
    commit id: "🧪 Tests"
    
    checkout main
    merge develop
    commit id: "🔄 PR Merge"
    
    commit id: "🏗️ Build" type: HIGHLIGHT
    commit id: "🧪 Test Suite"
    commit id: "🔒 Security"
    commit id: "🐳 Docker"
    
    branch staging
    checkout staging
    commit id: "🚀 Deploy Staging" type: HIGHLIGHT
    commit id: "🧪 Smoke Tests"
    
    checkout main
    merge staging
    commit id: "🏷️ Release Tag" type: HIGHLIGHT
    
    branch production
    checkout production
    commit id: "🚀 Deploy Prod" type: HIGHLIGHT
    commit id: "✅ Health Check"
    commit id: "📊 Monitoring"
```

## 📱 Diagrama de Interfaces

```mermaid
graph LR
    subgraph "👤 Usuario"
        WebUser[🌐 Usuario Web]
        DevUser[👨‍💻 Desarrollador]
        APIUser[🔌 Usuario API]
    end
    
    subgraph "🎛️ Interfaces"
        WebUI[🌐 Web Dashboard<br/>:8080]
        CLI[💻 Command Line<br/>Tools]
        RestAPI[🔌 REST API<br/>:8000]
    end
    
    subgraph "📊 Funcionalidades"
        Scraping[🕷️ Web Scraping]
        Analysis[📊 Code Analysis]
        GodClass[🧠 God Class<br/>Refactor]
        RAG[🤖 RAG System]
        Metrics[📈 Metrics &<br/>Reports]
    end
    
    WebUser --> WebUI
    DevUser --> CLI
    APIUser --> RestAPI
    
    WebUI --> Scraping
    WebUI --> Analysis
    WebUI --> GodClass
    WebUI --> RAG
    WebUI --> Metrics
    
    CLI --> Analysis
    CLI --> GodClass
    CLI --> Metrics
    
    RestAPI --> Scraping
    RestAPI --> RAG
    RestAPI --> Analysis
    
    style WebUI fill:#e1f5fe,stroke:#01579b
    style CLI fill:#f3e5f5,stroke:#4a148c
    style RestAPI fill:#e8f5e8,stroke:#1b5e20
    style Scraping fill:#fff3e0,stroke:#e65100
    style Analysis fill:#fce4ec,stroke:#880e4f
    style GodClass fill:#f1f8e9,stroke:#33691e
    style RAG fill:#e0f2f1,stroke:#00695c
    style Metrics fill:#fef7e0,stroke:#f57f17
```

---

## 📝 Notas

- **Arquitectura en Capas**: Separación clara entre presentación, servicios, dominio e infraestructura
- **Containerización**: Todo encapsulado en Docker para portabilidad
- **AI Local**: Modelos Qwen3 ejecutándose localmente sin dependencias externas
- **Escalabilidad**: Diseño modular que permite agregar nuevas funcionalidades
- **Monitoreo**: Dashboards y métricas integradas para observabilidad

Este diagrama muestra la estructura completa de la aplicación, desde las interfaces de usuario hasta la persistencia de datos, incluyendo el flujo de CI/CD y la containerización.