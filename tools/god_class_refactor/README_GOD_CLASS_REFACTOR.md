# 🧠 God Class Refactor Guide

Herramienta inteligente para guiar la refactorización **manual y segura** de God classes usando IA local.

## ✨ Características

- 🤖 **IA Local**: Usa modelo Qwen3-Embedding-8B para análisis semántico
- 🚀 **Configuración Adaptativa**: Encuentra automáticamente la configuración óptima de VRAM
- 🛡️ **Refactorización Segura**: Genera guía paso a paso para refactorización MANUAL
- ⚡ **Cache Inteligente**: Análisis futuros son instantáneos
- 🎯 **Análisis de Riesgos**: Evalúa riesgo de cada método antes de sugerir separación
- 📊 **Insights Semánticos**: Agrupa métodos por similitud semántica

## 🚀 Uso Rápido

```bash
# Activar entorno virtual
source env/bin/activate

# Analizar God class
python3 tools/god_class_refactor_guide.py src/path/to/god_class.py --output analysis.json

# Ver solo análisis en consola (sin guardar)
python3 tools/god_class_refactor_guide.py src/path/to/god_class.py
```

## 📊 Ejemplo de Resultado

```
🧠 ANÁLISIS INTELIGENTE GOD CLASS - IA LOCAL
==================================================
📊 Cargando modelo de IA local...
🎯 Modelo cargado exitosamente!
📈 Usando: Agresiva (8192 ctx, 30 GPU layers)
📋 Clase: AssetPlanExtractorV2
🔧 Métodos encontrados: 65
🧠 Análisis semántico con configuración óptima...
⏱️ Análisis completado en 15.5s

🎯 ANÁLISIS INTELIGENTE COMPLETADO
==================================================
🏗️ Clase: AssetPlanExtractorV2
🔧 Métodos: 65
📊 Configuración: Agresiva (8192 ctx)

💡 INSIGHTS CLAVE:
   • God class con 65 métodos identificada
   • Separable en 7 componentes especializados
   • Reducción de complejidad: 89%
   • Riesgo predominante: low

🛣️ PLAN EJECUTIVO:
   1. Preparar refactorización (2-3 horas)
   2. Extraer CoordinationManager (120 minutos)
   3. Extraer DebugManager (180 minutos)
   4. Extraer NavigationManager (420 minutos)
```

## 🔧 Configuración

### Requisitos
- Python 3.8+
- llama-cpp-python
- numpy
- Modelo Qwen3-Embedding-8B en `ml-models/`

### GPU/VRAM
La herramienta se adapta automáticamente a tu VRAM disponible:
- **8GB+**: Configuración Agresiva (8192 ctx, 30 GPU layers)
- **6GB**: Configuración Balanceada (6144 ctx, 25 GPU layers)
- **4GB**: Configuración Conservadora (4096 ctx, 20 GPU layers)
- **2GB**: Configuración Mínima (2048 ctx, 15 GPU layers)

## 📁 Estructura de Salida

El archivo JSON contiene:

```json
{
  "class_name": "NombreClase",
  "total_methods": 65,
  "methods_analysis": [
    {
      "name": "metodo_ejemplo",
      "semantic_concern": "navigation",
      "risk_level": "low", 
      "suggested_component": "NavigationManager",
      "complexity": 3,
      "dependencies": ["método1", "método2"]
    }
  ],
  "refactor_plan": [
    {
      "step": 1,
      "action": "Extraer DebugManager",
      "risk": "Low",
      "time_estimate": "180 minutos"
    }
  ],
  "summary": {
    "key_insights": [...],
    "refactorability": "Alta"
  }
}
```

## 🛠️ Opciones Avanzadas

```bash
# Resetear configuración óptima (volver a buscar configuración)
python3 tools/god_class_refactor_guide.py --reset-config

# Limpiar cache completo
rm -rf cache/god_class_refactor/
```

## 🧠 Cómo Funciona

1. **Detección**: Identifica clases con 10+ métodos
2. **Embeddings**: Genera embeddings semánticos para cada método
3. **Clustering**: Agrupa métodos por similitud semántica
4. **Análisis**: Categoriza por concerns (debug, navigation, parsing, etc.)
5. **Riesgo**: Evalúa complejidad y dependencias de cada método
6. **Plan**: Genera plan paso a paso priorizando métodos de bajo riesgo

## ⚠️ Filosofía: Refactorización Manual

Esta herramienta **NO refactoriza automáticamente** el código. En su lugar:

✅ **Genera guía inteligente** para refactorización manual  
✅ **Analiza riesgos** antes de sugerir separaciones  
✅ **Prioriza seguridad** sobre velocidad  
✅ **Requiere validación humana** en cada paso  

## 🎯 Casos de Uso

- **God Classes**: Clases con 20+ métodos
- **Servicios Monolíticos**: Clases que hacen "demasiado"
- **Controladores Grandes**: Controladores web con muchas responsabilidades
- **Managers Complejos**: Gestores que manejan múltiples concerns

## 🔍 Tipos de Concerns Detectados

- **Debug**: Métodos de debugging y monitoreo
- **Navigation**: Navegación y interacción (WebDriver, UI)
- **Parsing**: Parsing y validación de datos
- **Extraction**: Extracción de información
- **Validation**: Validación y verificación
- **Coordination**: Métodos coordinadores (alto riesgo)
- **Utility**: Métodos utilitarios

## 📈 Métricas de Calidad

- **Complejidad**: Número de estructuras de control (if/for/while/try)
- **Acoplamiento**: Número de dependencias con otros métodos
- **Riesgo**: Combinación de complejidad, acoplamiento y tipo
- **Refactorabilidad**: Porcentaje de métodos de bajo/medio riesgo

---

**Versión**: Final y Robusta  
**Autor**: Claude Code con herramientas de IA local  
**Licencia**: Proyecto interno  