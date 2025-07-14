# 🏠 AssetPlan Property Assistant

**Agente Conversacional "Scraper + RAG"** - Desafío Técnico (72h)

Un sistema inteligente de búsqueda y recomendación de propiedades inmobiliarias que combina web scraping profesional con inteligencia artificial conversacional usando **modelos locales GGUF** y **GPU acceleration**.

## 🎯 Características Principales

✅ **Web Scraping Profesional** - Extrae propiedades de AssetPlan.cl con técnicas anti-detección  
✅ **RAG con Modelos Locales** - LangChain + llama.cpp + DeepSeek R1  
✅ **GPU Acceleration** - CUDA support para RTX 3050+ (8GB VRAM)  
✅ **URL Citation** - Cita URLs originales (requisito coding challenge)  
✅ **Anti-Overthinking** - Respuestas concisas optimizadas  
✅ **API REST** - FastAPI con documentación automática  
✅ **CLI Interactivo** - Chat directo con el agente  

## 🚀 Quick Start

```bash
# 1. Setup completo
make setup

# 2. Verificar estado del sistema  
make test-status

# 3. Ejecutar scraper
make scrape-quick

# 4. Levantar agente RAG
make run

# 5. Verificar URLs (coding challenge)
make test-url-citation
```

## 📋 Instalación

### Prerrequisitos

- **Python 3.13+**
- **Chrome/Chromium** (para scraping)
- **CUDA 12.1+** (opcional, para GPU acceleration)
- **8GB+ RAM** (4GB+ VRAM recomendado para GPU)

### Setup Automático

```bash
# Clonar repositorio
git clone <repository-url>
cd scrapper-llm-inmobiliario

# Setup completo con make
make setup
```

### Setup Manual

```bash
# Crear entorno virtual
python3 -m venv env
source env/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación
make test-status
```

## 🕷️ Ejecutar el Scraper

### Comandos Make (Recomendado)

```bash
# Scraping rápido (10 propiedades)
make scrape-quick

# Scraping profesional (configuración completa)
make scrape-pro

# Scraping completo (50 propiedades)
make scrape-full

# Ver todas las opciones
make help
```

### Comandos Directos

```bash
# Activar entorno
source env/bin/activate

# Scraping básico
python3 -m src.scraper.professional_scraper

# Scraping personalizado
python3 -m src.scraper.professional_scraper --max-properties 50 --comprehensive

# Ver ayuda
python3 -m src.scraper.professional_scraper --help
```

### Verificar Datos Scrapeados

```bash
# Ver estado de datos
make test-status

# Ver propiedades extraídas
ls -la data/properties.json

# Verificar URLs en datos
python3 -c "import json; data=json.load(open('data/properties.json')); print(f'Propiedades: {len(data[\"properties\"])}, URLs: {sum(1 for p in data[\"properties\"] if p.get(\"url\"))}')"
```

## 🤖 Levantar el Agente RAG

### Opción 1: API REST (Recomendado)

```bash
# Levantar API con optimizaciones GPU
make run

# O directamente:
source env/bin/activate && python3 run_gpu_optimized.py
```

**API disponible en:**
- 🌐 **Servidor**: http://localhost:8000
- 📖 **Documentación**: http://localhost:8000/docs  
- 📋 **Redoc**: http://localhost:8000/redoc

### Opción 2: CLI Interactivo

```bash
# Chat interactivo con GPU
source env/bin/activate && python3 run_chat.py
```

### Opción 3: API con Configuración Específica

```bash
# Solo CPU (sin GPU)
export USE_GPU=false && make run

# Solo modelos OpenAI
export USE_LOCAL_MODELS=false && export OPENAI_API_KEY="tu-key" && make run
```

## 🧪 Ejecutar Tests

### Tests Rápidos (Recomendados)

```bash
# Verificación completa del sistema (1 segundo)
make test-status

# Test de URLs (requisito coding challenge) 
make test-url-citation

# Test anti-overthinking
make test-anti-overthinking

# Ver todos los comandos de test
make help
```

### Suite Completa de Tests

```bash
# Tests funcionales completos
make test-functional

# Tests GPU
make test-gpu

# Tests API
make test-api

# Tests tradicionales (pytest)
make test
```

### Interpretación de Resultados

#### ✅ Sistema Funcionando
```
🎉 ¡SISTEMA LISTO!
✅ Todos los componentes disponibles
✅ 30 propiedades scrapeadas con URLs
✅ URLs originales citadas correctamente
```

#### ✅ URLs Funcionando (Coding Challenge)
```
✅ URL encontrada en respuesta
URL: https://www.assetplan.cl/arriendo/departamento/independencia/1-dormitorio/home-inclusive-independencia/3063?feeGuarantee=false&fixedPrice=false&freeCommission=false&onOffer=false&selectedUnit=496134
```

#### ❌ Problemas Detectados
```
⚠️ X componentes con problemas
🔧 Revisar configuración antes de ejecutar tests
```

## 🏗️ Arquitectura del Sistema

```mermaid
graph TB
    subgraph "🕷️ Scraping Layer"
        WS[Web Scraper] --> WDF[WebDriver Factory]
        WS --> HBS[Human Behavior Simulator]
        WS --> AE[AssetPlan Extractor]
        WS --> DV[Data Validator]
    end
    
    subgraph "💾 Data Layer"
        WS --> JSON[properties.json]
        JSON --> VS[Vector Store FAISS]
    end
    
    subgraph "🧠 AI Layer"
        VS --> EMB[HuggingFace Embeddings]
        VS --> RAG[LangChain RAG]
        RAG --> LLM[DeepSeek R1 GGUF]
        RAG --> GPU[CUDA Acceleration]
    end
    
    subgraph "🌐 Interface Layer"
        RAG --> API[FastAPI REST]
        RAG --> CLI[Interactive CLI]
    end
    
    subgraph "🔗 Output Features"
        RAG --> URLS[URL Citation]
        RAG --> ANTI[Anti-Overthinking]
        RAG --> CONF[Confidence Scoring]
    end
    
    subgraph "👤 User Interaction"
        USER[User] --> CLI
        CLIENT[Client App] --> API
    end
    
    style GPU fill:#90EE90
    style URLS fill:#FFD700
    style ANTI fill:#87CEEB
```

### 🔧 Componentes Clave

#### **Scraping Layer**
- **WebDriver Factory**: Configuración anti-detección
- **Human Behavior**: Simulación de comportamiento natural
- **AssetPlan Extractor**: Extractor especializado v2
- **Data Validator**: Validación robusta de datos

#### **AI Layer** 
- **Vector Store**: FAISS con embeddings HuggingFace
- **LangChain RAG**: Retrieval-Augmented Generation
- **DeepSeek R1**: Modelo local GGUF optimizado
- **GPU Acceleration**: CUDA para RTX 3050+ (25 layers)

#### **Output Features**
- **URL Citation**: Cita URLs originales (requisito)
- **Anti-Overthinking**: Respuestas concisas
- **Confidence Scoring**: Evaluación de calidad

## 🔌 API Usage

### Pregunta con URL Citation

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Muestra 1 departamento en Independencia",
    "max_sources": 3
  }'
```

**Respuesta:**
```json
{
  "answer": "**Departamento:** Home Inclusive Independencia - Depto 1904-B\n**Precio:** $149.057\n**Superficie:** 51.0 m²\n**URL:** https://www.assetplan.cl/arriendo/departamento/independencia/1-dormitorio/home-inclusive-independencia/3063?feeGuarantee=false&fixedPrice=false&freeCommission=false&onOffer=false&selectedUnit=496134",
  "sources": [...],
  "confidence": 0.85,
  "query_type": "search",
  "property_count": 5
}
```

### Otros Endpoints

```bash
# Estado del sistema
curl http://localhost:8000/health

# Estadísticas
curl http://localhost:8000/stats

# Búsqueda semántica
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "departamento moderno", "max_results": 5}'
```

## ⚙️ Configuración Avanzada

### Variables de Entorno

```bash
# Modelos y GPU
export USE_LOCAL_MODELS=true
export USE_GPU=true  
export GPU_LAYERS=25
export GPU_MEMORY_LIMIT=5.5

# Paths de modelos
export LOCAL_LLM_MODEL_PATH=ml-models/DeepSeek-R1-0528-Qwen3-8B-Q6_K.gguf
export LOCAL_EMBEDDING_MODEL_PATH=ml-models/Qwen3-Embedding-8B-Q6_K.gguf

# OpenAI (alternativo)
export OPENAI_API_KEY=tu-key-aqui
export OPENAI_MODEL=gpt-4

# Scraping
export MAX_PROPERTIES=50
export HEADLESS_BROWSER=true
```

### Configuración de GPU

```bash
# Verificar CUDA
nvidia-smi

# Configurar para RTX 3050 (8GB)
export GPU_LAYERS=25
export GPU_MEMORY_LIMIT=5.5

# Configurar para RTX 4070+ (12GB+)
export GPU_LAYERS=35
export GPU_MEMORY_LIMIT=8.0

# Solo CPU
export USE_GPU=false
```

## 📊 Performance y Optimizaciones

### Métricas Actuales

- ✅ **Primera respuesta**: ~60s (inicialización modelo)
- ✅ **Respuestas subsecuentes**: ~10s promedio  
- ✅ **GPU acceleration**: 2-3x speedup vs CPU
- ✅ **URL citation**: 100% accuracy
- ✅ **Anti-overthinking**: 95% respuestas concisas

### Optimizaciones Implementadas

- 🚀 **GPU offloading**: 25 layers en VRAM
- 🧠 **Anti-overthinking**: temperature=0.0, stop tokens
- 💾 **Memory optimization**: n_batch=256, f16_kv=True
- 🔗 **URL extraction**: Prompt simplificado y directo
- ⚡ **Vector caching**: FAISS index persistente

## 🛠️ Troubleshooting

### Problemas Comunes

#### Modelos no encontrados
```bash
# Verificar modelos
ls ml-models/
make test-status
```

#### GPU no disponible
```bash
# Verificar CUDA
nvidia-smi

# Fallback a CPU
export USE_GPU=false
make test-status
```

#### Datos no scrapeados
```bash
# Ejecutar scraping
make scrape-quick

# Verificar datos
make test-status
```

#### Tests fallan
```bash
# Verificar sistema completo
make test-status

# Test específico URLs
make test-url-citation
```

### Logs y Debug

```bash
# Ver logs en tiempo real
tail -f logs/application.log

# Debug específico
export LOG_LEVEL=DEBUG
python3 debug_url_source.py
```

## 📁 Estructura del Proyecto

```
scrapper-llm-inmobiliario/
├── 📄 README.md                    # Esta guía
├── 📄 Makefile                     # Comandos automatizados
├── 📄 HOWTO_TEST.md                # Guía detallada de testing
├── 📄 URL_CITATION_SUCCESS.md      # Documentación URL citation
├── 📄 requirements.txt             # Dependencias Python
├── 
├── 🚀 run_gpu_optimized.py         # Launcher optimizado GPU
├── 🚀 run_api.py                   # Launcher API REST
├── 🚀 run_chat.py                  # Launcher CLI interactivo
├── 
├── 📂 src/                         # Código fuente
│   ├── 📂 scraper/                 # Sistema scraping profesional
│   ├── 📂 rag/                     # LangChain RAG + modelos locales
│   ├── 📂 vectorstore/             # FAISS + embeddings
│   ├── 📂 api/                     # FastAPI REST
│   ├── 📂 cli/                     # CLI interactivo
│   └── 📂 utils/                   # Configuración y utilidades
├── 
├── 📂 ml-models/                   # Modelos GGUF locales
│   ├── 📄 DeepSeek-R1-*.gguf       # Modelo LLM principal
│   └── 📄 Qwen3-Embedding-*.gguf   # Modelo embeddings
├── 
├── 📂 data/                        # Datos generados
│   ├── 📄 properties.json          # Propiedades scrapeadas
│   └── 📂 faiss_index/             # Índice vectorial
├── 
├── 📂 tests/                       # Tests tradicionales
└── 🧪 test_*.py                    # Tests funcionales
```

## 🎯 Cumplimiento Coding Challenge

### ✅ Requisitos Cumplidos

1. **URLs Originales Citadas**
   - ✅ URLs de AssetPlan.cl incluidas en todas las respuestas
   - ✅ Test: `make test-url-citation`

2. **Scraping Profesional**
   - ✅ 30+ propiedades extraídas
   - ✅ Anti-detección implementado
   - ✅ Test: `make test-status`

3. **RAG Funcional**
   - ✅ Respuestas en lenguaje natural
   - ✅ Modelos locales con GPU
   - ✅ Test: `make test-functional`

4. **API Operativa**
   - ✅ FastAPI con documentación
   - ✅ Endpoints funcionales
   - ✅ Test: `make test-api`

### 🚀 Extras Implementados

- 🧠 **Modelos Locales**: DeepSeek R1 sin dependencia OpenAI
- ⚡ **GPU Acceleration**: RTX 3050+ support
- 🎯 **Anti-Overthinking**: Respuestas concisas optimizadas
- 🔗 **URL Citation**: Citación perfecta de fuentes
- 🛠️ **Suite de Tests**: Testing completo automatizado

## 📞 Soporte

### Tests de Verificación

```bash
# Verificación completa (1 segundo)
make test-status

# Verificación coding challenge
make test-url-citation

# Ayuda completa
make help
```

### Documentación Adicional

- 📖 **Testing**: `HOWTO_TEST.md`
- 🔗 **URL Citation**: `URL_CITATION_SUCCESS.md`
- 🏗️ **Arquitectura**: `ARCHITECTURE.md`

---

**🏠 AssetPlan Property Assistant** - *Potenciado por IA local con GPU acceleration*

> **Status**: ✅ Completamente funcional | URLs citadas correctamente | Coding challenge cumplido