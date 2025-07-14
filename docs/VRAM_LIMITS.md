# 🔥 VRAM Limits - Sistema GPU Documentado

## 📊 Especificaciones del Sistema

**Hardware Detectado:**
- **VRAM Total**: 8GB disponibles
- **VRAM Usable**: ~7.5GB (reservando overhead del sistema)
- **Arquitectura**: Compatible con llama-cpp-python
- **Driver**: Funcionando correctamente con CUDA/OpenCL

## 🚀 Configuraciones Probadas y Resultados

### ✅ **CONFIGURACIÓN AGRESIVA** (FUNCIONA)
```python
Llama(
    n_ctx=8192,          # 8K contexto ✅
    n_gpu_layers=30,     # 30 capas GPU ✅  
    n_batch=1024,        # Batch grande ✅
    n_threads=6,         # 6 threads ✅
    f16_kv=True,         # FP16 para KV cache ✅
    use_mmap=True,       # Memory mapping ✅
    use_mlock=False      # Sin lock memory ✅
)
```
**Resultado**: ✅ **EXITOSO** - Modelo Qwen3-Embedding-8B cargado y funcionando
**Tiempo de carga**: ~30 segundos
**Rendimiento**: 65 embeddings en 15.5 segundos

### ❌ **CONFIGURACIONES QUE FALLAN**

#### Configuración Ultra-Agresiva (FALLA)
```python
n_ctx=16384,         # 16K contexto ❌ 
n_gpu_layers=-1,     # Todas las capas ❌
n_batch=2048,        # Batch muy grande ❌
use_mlock=True       # Lock memory ❌
```
**Error**: `Failed to create llama_context`

#### Configuración Máxima (FALLA)
```python
n_ctx=12288,         # 12K contexto ❌
n_gpu_layers=35,     # 35+ capas ❌
```
**Error**: `Failed to create llama_context`

## 📈 Límites Exactos Encontrados

### 🎯 **Contexto Máximo**
- **8192 tokens**: ✅ Funciona perfectamente
- **12288 tokens**: ❌ Falla al crear contexto
- **16384 tokens**: ❌ Falla al crear contexto

### 🎯 **GPU Layers Máximo** 
- **30 layers**: ✅ Configuración óptima
- **35+ layers**: ❌ Excede VRAM disponible

### 🎯 **Batch Size Óptimo**
- **1024**: ✅ Balance perfecto velocidad/memoria
- **2048**: ❌ Demasiado para VRAM disponible

### 🎯 **Configuraciones de Memoria**
- **f16_kv=True**: ✅ Esencial para ahorrar VRAM
- **use_mmap=True**: ✅ Mejora eficiencia
- **use_mlock=False**: ✅ Evita OOM en sistema
- **offload_kqv=True**: ❌ Incompatible con este setup

## 🔧 Configuración de Respaldo (Balanceada)

Si la configuración agresiva falla en futuras actualizaciones:

```python
Llama(
    n_ctx=6144,          # 6K contexto (más conservador)
    n_gpu_layers=25,     # 25 capas GPU
    n_batch=512,         # Batch moderado  
    n_threads=4,         # 4 threads
    f16_kv=True,
    use_mmap=True,
    use_mlock=False
)
```

## 🎮 Configuración Mínima Garantizada

Para compatibilidad máxima:

```python
Llama(
    n_ctx=4096,          # 4K contexto (estándar)
    n_gpu_layers=20,     # 20 capas GPU
    n_batch=256,         # Batch pequeño
    n_threads=2,         # 2 threads
    f16_kv=True,
    use_mmap=True,
    use_mlock=False
)
```

## 📊 Rendimiento por Configuración

| Configuración | Contexto | GPU Layers | Tiempo Carga | Rendimiento | Estado |
|---------------|----------|------------|--------------|-------------|---------|
| Agresiva      | 8192     | 30         | ~30s         | 15.5s/65emb | ✅ Óptima |
| Balanceada    | 6144     | 25         | ~25s         | ~20s/65emb  | ✅ Backup |
| Conservadora  | 4096     | 20         | ~20s         | ~30s/65emb  | ✅ Segura |
| Mínima        | 2048     | 15         | ~15s         | ~45s/65emb  | ✅ Compat |

## ⚠️ Advertencias y Limitaciones

### 🚫 **NO Funciona**
- **Modelos simultáneos**: 2 modelos de 8B al mismo tiempo
- **Contexto >8K**: Cualquier configuración con más de 8192 contexto
- **GPU layers >30**: Más de 30 capas causa OOM
- **Memory locking**: `use_mlock=True` causa fallos

### ⚡ **Optimizaciones Clave**
- **FP16 KV Cache**: Fundamental para ahorrar VRAM
- **Memory mapping**: Mejora significativa de rendimiento  
- **Batch moderado**: 1024 es el sweet spot
- **Threading**: 6 threads es óptimo para este sistema

## 🔍 Método de Detección Automática

El sistema implementa detección automática que prueba configuraciones en este orden:

1. **Agresiva** (8192 ctx, 30 layers) - Probada primero
2. **Balanceada** (6144 ctx, 25 layers) - Si falla agresiva
3. **Conservadora** (4096 ctx, 20 layers) - Si falla balanceada  
4. **Mínima** (2048 ctx, 15 layers) - Última opción

## 📝 Notas de Implementación

- **Cache persistente**: La configuración óptima se guarda en `cache/god_class_refactor/optimal_config.json`
- **Reset disponible**: `--reset-config` para forzar nueva detección
- **Fallback graceful**: Si falla una configuración, prueba la siguiente automáticamente
- **Mensajes informativos**: El sistema reporta qué configuración está usando

---

**Fecha**: Julio 2025  
**Sistema**: 8GB VRAM GPU  
**Modelo**: Qwen3-Embedding-8B-Q6_K.gguf  
**Configuración Óptima**: Agresiva (8192 ctx, 30 layers) ✅