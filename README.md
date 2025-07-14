# 🏠 Scrapper LLM Inmobiliario

Sistema de scraping inteligente de propiedades inmobiliarias con RAG (Retrieval-Augmented Generation) y análisis de código automatizado.

## 🚀 Inicio Rápido

### 1. Configuración
```bash
# Activar entorno virtual
source env/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Correr el Scraper
```bash
# Scraping rápido (30 propiedades)
python scripts/run_scraper_rag.py --mode quick --max-properties 30

# Scraping completo (50 propiedades)
python scripts/run_scraper_rag.py --mode comprehensive --max-properties 50
```

### 3. Levantar el Agente RAG
```bash
# Chat interactivo con RAG
python scripts/run_chat.py

# API REST en puerto 8000
python scripts/run_api.py

# Pipeline completo: scraper + RAG + API
python scripts/run_scraper_rag.py --mode quick --start-api --wait-for-api
```

### 4. Ejecutar Tests
```bash
# Tests rápidos
python scripts/run_tests.py --type fast

# Tests completos
python scripts/run_tests.py --type all

# Tests funcionales del sistema
python tests/test_integration.py
```

## 🛠️ Herramientas Adicionales

### Dashboard de Análisis
```bash
# Levantar dashboard web
python tools/dashboard/categorized_dashboard_server.py
# Abrir: http://localhost:8080
```

### Análisis de Código
```bash
# Análisis completo de métricas
python tools/code_analysis/smart_code_analyzer.py

# Detectar God Classes
python tools/god_class_refactor/god_class_refactor_guide.py
```

## 🐳 Docker

```bash
# Construcción
docker build -t scrapper-llm .

# Ejecutar scraper
docker run --rm scrapper-llm scraper

# Ejecutar API
docker run -p 8000:8000 scrapper-llm api

# Docker Compose
docker-compose up
```

## 📊 Características

- **Scraping Inteligente**: Selenium con comportamiento humano
- **RAG System**: LangChain + FAISS + Modelos locales GGUF
- **API REST**: FastAPI con documentación automática
- **Análisis AI**: God Class detection y refactoring automático
- **Testing**: Suite completa con pytest
- **Dashboard**: Interface web para análisis y métricas

## 🔧 Configuración

Las variables de entorno principales:
- `USE_LOCAL_MODELS=true` - Usar modelos locales GGUF
- `OPENAI_API_KEY` - Para usar modelos OpenAI
- `API_PORT=8000` - Puerto de la API
- `LOG_LEVEL=INFO` - Nivel de logging

## 📁 Estructura

```
├── src/                    # Código fuente
├── tools/                  # Herramientas de análisis
├── tests/                  # Tests
├── scripts/                # Scripts de ejecución
├── data/                   # Datos scrapeados
├── ml-models/              # Modelos LLM locales
└── docs/                   # Documentación
```

---

Sistema optimizado con refactoring automatizado y análisis de código basado en IA.