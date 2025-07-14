# API Documentation - AssetPlan Property Assistant

## 🌐 FastAPI REST Interface

La API REST proporciona acceso programático a todas las funcionalidades del sistema de propiedades inmobiliarias con IA conversacional.

**Base URL**: `http://localhost:8000`  
**Documentación Interactiva**: `http://localhost:8000/docs`  
**ReDoc**: `http://localhost:8000/redoc`

## 📋 Endpoints Overview

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| GET | `/` | Información general de la API | No |
| GET | `/health` | Estado del sistema | No |
| GET | `/stats` | Estadísticas del sistema | No |
| POST | `/ask` | Preguntas en lenguaje natural | No |
| POST | `/search` | Búsqueda semántica | No |
| POST | `/recommend` | Recomendaciones personalizadas | No |

## 🔍 Endpoints Detallados

### **GET /** - Información de la API

Retorna información básica sobre la API y endpoints disponibles.

**Response:**
```json
{
  "service": "AssetPlan Property Assistant API",
  "version": "1.0.0",
  "description": "AI-powered real estate property search and recommendations",
  "endpoints": {
    "ask": "/ask - Ask questions about properties",
    "search": "/search - Search properties by query", 
    "recommend": "/recommend - Get property recommendations",
    "health": "/health - Health check",
    "docs": "/docs - API documentation"
  }
}
```

---

### **GET /health** - Health Check

Verifica el estado del sistema y sus componentes.

**Response Model: `HealthResponse`**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "system_stats": {
    "llm_model": "gpt-3.5-turbo",
    "retrieval_k": 5,
    "vector_store_stats": {
      "status": "ready",
      "document_count": 55,
      "embedding_dimension": 1536,
      "property_types": {
        "departamento": 32,
        "casa": 18,
        "oficina": 5
      }
    }
  }
}
```

**Status Values:**
- `healthy`: Sistema funcionando correctamente
- `degraded`: Sistema funcional con algunos problemas
- `unhealthy`: Sistema con errores críticos

---

### **GET /stats** - Estadísticas del Sistema

Retorna estadísticas detalladas del sistema.

**Response:**
```json
{
  "llm_model": "gpt-3.5-turbo",
  "retrieval_k": 5,
  "vector_store_stats": {
    "status": "loaded",
    "document_count": 55,
    "embedding_dimension": 1536,
    "property_types": {
      "departamento": 32,
      "casa": 18,
      "oficina": 5
    },
    "top_locations": {
      "Providencia, Santiago": 15,
      "Las Condes, Santiago": 12,
      "Ñuñoa, Santiago": 8,
      "Santiago Centro": 7,
      "Vitacura, Santiago": 5
    },
    "price_coverage": {
      "with_price": 45,
      "without_price": 10
    },
    "index_path": "data/faiss_index"
  },
  "status": "ready"
}
```

---

### **POST /ask** - Preguntas en Lenguaje Natural

El endpoint principal para hacer preguntas conversacionales sobre propiedades.

**Request Model: `QuestionRequest`**
```json
{
  "question": "¿Qué departamentos de 2 dormitorios hay en Providencia bajo 3000 UF?",
  "max_sources": 5
}
```

**Request Fields:**
- `question` (string, required): Pregunta en lenguaje natural (mín. 3 caracteres)
- `max_sources` (integer, optional): Máximo número de fuentes (1-20, default: 5)

**Response Model: `QuestionResponse`**
```json
{
  "answer": "Encontré 3 departamentos de 2 dormitorios en Providencia bajo 3000 UF:\n\n1. **Departamento Providencia Centro** - 2.850 UF, 65 m², 2 dorm, 2 baños\n   Fuente: [Ver propiedad](https://www.assetplan.cl/propiedad/123)\n\n2. **Moderno Departamento Providencia** - 2.950 UF, 70 m², 2 dorm, 1 baño\n   Fuente: [Ver propiedad](https://www.assetplan.cl/propiedad/456)\n\nTodas estas propiedades están ubicadas en Providencia y cumplen con tus criterios.",
  "sources": [
    {
      "property_id": "123",
      "title": "Departamento Providencia Centro",
      "property_type": "departamento",
      "location": "Providencia, Santiago",
      "price": "$570.000",
      "price_uf": "2.850 UF",
      "area_m2": 65.0,
      "bedrooms": 2,
      "bathrooms": 2,
      "url": "https://www.assetplan.cl/propiedad/123",
      "images": ["image1.jpg"],
      "source": "assetplan.cl"
    }
  ],
  "confidence": 0.85,
  "query_type": "search",
  "property_count": 3,
  "timestamp": "2024-01-01T12:00:00Z",
  "processing_time_ms": 1250.5
}
```

**Response Fields:**
- `answer` (string): Respuesta generada en lenguaje natural
- `sources` (array): Propiedades fuente con metadata completa
- `confidence` (float): Puntuación de confianza (0.0-1.0)
- `query_type` (string): Tipo de consulta clasificada
- `property_count` (integer): Número de propiedades encontradas
- `timestamp` (string): Timestamp de la respuesta
- `processing_time_ms` (float): Tiempo de procesamiento en milisegundos

**Query Types:**
- `search`: Búsqueda específica por características
- `comparison`: Comparación entre propiedades
- `recommendation`: Recomendación personalizada
- `information`: Información sobre propiedades específicas
- `price_analysis`: Análisis de precios
- `location_info`: Información sobre ubicaciones

**Ejemplos de Preguntas:**
```bash
# Búsqueda específica
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué departamentos de 2 dormitorios hay en Providencia bajo 3000 UF?",
    "max_sources": 5
  }'

# Comparación
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Compara las propiedades más baratas en Las Condes vs Providencia",
    "max_sources": 10
  }'

# Recomendación
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Recomiéndame una casa familiar con jardín en la zona oriente",
    "max_sources": 3
  }'
```

---

### **POST /search** - Búsqueda Semántica

Realiza búsqueda semántica directa en las propiedades usando embeddings.

**Request Model: `SearchRequest`**
```json
{
  "query": "departamento moderno con vista panorámica",
  "max_results": 10,
  "score_threshold": 0.7
}
```

**Request Fields:**
- `query` (string, required): Consulta de búsqueda (mín. 3 caracteres)
- `max_results` (integer, optional): Máximo resultados (1-50, default: 10)
- `score_threshold` (float, optional): Umbral de similitud (0.0-1.0, default: 0.7)

**Response Model: `SearchResponse`**
```json
{
  "query": "departamento moderno con vista panorámica",
  "total_results": 3,
  "properties": [
    {
      "property_id": "123",
      "title": "Departamento Moderno Torre Central",
      "property_type": "departamento",
      "location": "Providencia, Santiago",
      "price": "$650.000",
      "price_uf": "3.250 UF",
      "area_m2": 85.0,
      "bedrooms": 2,
      "bathrooms": 2,
      "url": "https://www.assetplan.cl/propiedad/123",
      "similarity_score": 0.92
    },
    {
      "property_id": "456",
      "title": "Exclusivo Departamento Vista Ciudad",
      "property_type": "departamento",
      "location": "Las Condes, Santiago",
      "price": "$890.000",
      "price_uf": "4.450 UF",
      "area_m2": 120.0,
      "bedrooms": 3,
      "bathrooms": 2,
      "url": "https://www.assetplan.cl/propiedad/456",
      "similarity_score": 0.87
    }
  ],
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Ejemplo:**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "casa con jardín y piscina",
    "max_results": 5,
    "score_threshold": 0.8
  }'
```

---

### **POST /recommend** - Recomendaciones Personalizadas

Genera recomendaciones basadas en criterios específicos.

**Request Model: `RecommendationRequest`**
```json
{
  "property_type": "departamento",
  "location": "Providencia",
  "bedrooms": 2,
  "bathrooms": 1,
  "max_price_uf": 3000,
  "min_area_m2": 60,
  "max_recommendations": 5
}
```

**Request Fields (todos opcionales):**
- `property_type` (string): Tipo de propiedad
- `location` (string): Ubicación preferida
- `bedrooms` (integer): Número de dormitorios (0-10)
- `bathrooms` (integer): Número de baños (0-10)
- `max_price_uf` (float): Precio máximo en UF
- `min_area_m2` (float): Superficie mínima en m²
- `max_recommendations` (integer): Máximo recomendaciones (1-20, default: 5)

**Response Model: `QuestionResponse`**
(Mismo formato que `/ask`)

**Ejemplo:**
```bash
curl -X POST "http://localhost:8000/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "property_type": "casa",
    "location": "Las Condes", 
    "bedrooms": 3,
    "max_price_uf": 5000,
    "min_area_m2": 150,
    "max_recommendations": 3
  }'
```

## 🚨 Códigos de Error

### **Error Response Format**
```json
{
  "error": "Error description",
  "status_code": 400,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### **HTTP Status Codes**

| Código | Descripción | Cuándo Ocurre |
|--------|-------------|---------------|
| 200 | OK | Solicitud exitosa |
| 400 | Bad Request | Datos de entrada inválidos |
| 422 | Validation Error | Error de validación Pydantic |
| 500 | Internal Server Error | Error interno del servidor |
| 503 | Service Unavailable | RAG chain no inicializado |

### **Validation Errors**
```json
{
  "detail": [
    {
      "loc": ["body", "question"],
      "msg": "ensure this value has at least 3 characters",
      "type": "value_error.any_str.min_length",
      "ctx": {"limit_value": 3}
    }
  ]
}
```

## 🔧 SDKs y Clientes

### **Python Client**
```python
import requests

class PropertyAssistantClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def ask_question(self, question, max_sources=5):
        response = requests.post(f"{self.base_url}/ask", json={
            "question": question,
            "max_sources": max_sources
        })
        return response.json()
    
    def search_properties(self, query, max_results=10, score_threshold=0.7):
        response = requests.post(f"{self.base_url}/search", json={
            "query": query,
            "max_results": max_results,
            "score_threshold": score_threshold
        })
        return response.json()
    
    def get_recommendations(self, **criteria):
        response = requests.post(f"{self.base_url}/recommend", json=criteria)
        return response.json()

# Uso
client = PropertyAssistantClient()
answer = client.ask_question("¿Hay departamentos en Ñuñoa bajo 2500 UF?")
print(answer['answer'])
```

### **JavaScript/TypeScript Client**
```typescript
interface PropertyAssistantClient {
  askQuestion(question: string, maxSources?: number): Promise<QuestionResponse>;
  searchProperties(query: string, maxResults?: number, scoreThreshold?: number): Promise<SearchResponse>;
  getRecommendations(criteria: RecommendationCriteria): Promise<QuestionResponse>;
}

class PropertyAssistantAPI implements PropertyAssistantClient {
  constructor(private baseUrl: string = 'http://localhost:8000') {}
  
  async askQuestion(question: string, maxSources = 5): Promise<QuestionResponse> {
    const response = await fetch(`${this.baseUrl}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, max_sources: maxSources })
    });
    return response.json();
  }
  
  // ... más métodos
}

// Uso
const client = new PropertyAssistantAPI();
const answer = await client.askQuestion('¿Qué casas hay en Vitacura?');
console.log(answer.answer);
```

## 📊 Rate Limiting y Performance

### **Límites de Rate (Recomendados)**
- Desarrollo: Sin límites
- Producción: 100 requests/minuto por IP
- Burst: Hasta 20 requests/segundo por períodos cortos

### **Timeouts**
- Request timeout: 30 segundos
- Processing timeout: 60 segundos para primera respuesta
- Respuestas típicas: 1-3 segundos después de inicialización

### **Caching**
- Embeddings: Cache automático en disco
- Índice FAISS: Persistente entre reinicios
- Responses: No cacheadas (datos dinámicos)

## 🔒 Autenticación y Seguridad

### **Autenticación Actual**
- Sin autenticación (desarrollo)
- API Key ready (producción)

### **CORS Configuration**
```python
# Configuración actual (desarrollo)
allow_origins=["*"]
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]

# Configuración recomendada (producción)
allow_origins=["https://yourdomain.com"]
allow_credentials=False
allow_methods=["GET", "POST"]
allow_headers=["Content-Type", "Authorization"]
```

### **Input Validation**
- Sanitización automática con Pydantic
- Validación de longitud de strings
- Validación de rangos numéricos
- Prevención de injection attacks

## 🚀 Deployment

### **Docker Deployment**
```dockerfile
FROM python:3.13-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "run_api.py"]
```

### **Environment Variables**
```bash
OPENAI_API_KEY=your-api-key
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

### **Health Check Endpoint**
```bash
# Monitoreo de salud
curl http://localhost:8000/health

# Usar en Docker health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

---

**📚 Esta documentación está siempre actualizada en**: `http://localhost:8000/docs`