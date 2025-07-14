# 🧹 Análisis de Refactorización del Proyecto

## 📁 Archivos Identificados para Limpieza

### ✅ **ELIMINADOS**
- `src/scraper/domain/assetplan_extractor.py` - ✅ Reemplazado por `assetplan_extractor_v2.py`

### 🗑️ **CANDIDATOS PARA ELIMINACIÓN**

#### Scripts de Testing Redundantes
- `test_scraper_simple.py` - Usa `AssetplanScraper` obsoleto
- `simple_scraper_test.py` - Implementación con BeautifulSoup, no Selenium
- `test_end_to_end.py` - Probablemente redundante con tests organizados
- `demo_system.py` - Script de demo, no parte del core

#### Scripts de Diagnóstico/Desarrollo  
- `diagnose_scraping.py` - Script de diagnóstico, útil pero no esencial
- `fix_scraping.py` - Script de reparación, probablemente obsoleto

#### Documentación Redundante
- `GUIA.md` - Puede estar duplicada con `/docs`
- `WORKFLOW_EXAMPLE.md` - Puede estar obsoleta
- Múltiples archivos MD en `/docs` que pueden ser consolidados

#### Archivos de Datos/Logs Temporales
- `li_completo.html` - Archivo temporal de desarrollo
- `logs/application.log` - Log temporal

### 🔍 **ÁREAS DIFUSAS/DIFÍCILES**

#### 1. **`src/scraper/assetplan_scraper.py`**
```python
# ⚠️ ÁREA DIFUSA: Este archivo parece ser una implementación alternativa
# Usa una API diferente a scraper_manager.py y AssetPlanExtractorV2
# DECISIÓN NECESARIA: ¿Mantener como alternativa o eliminar?
```

#### 2. **`src/scraper/professional_scraper.py`**
```python
# ⚠️ ÁREA DIFUSA: No está claro si se usa actualmente
# Puede ser otra implementación alternativa
# NECESITA INVESTIGACIÓN
```

#### 3. **Tests en `/tests` vs archivos de test raíz**
```python
# ⚠️ CONFLICTO: tests organizados en /tests/ vs scripts sueltos
# Los tests organizados son mejores, pero algunos scripts pueden tener valor
```

#### 4. **Múltiples puntos de entrada**
```python
# ⚠️ CONFUSIÓN: Múltiples formas de ejecutar scraping:
# - test_multi_typology.py (NUEVO - recomendado)
# - run_api.py 
# - run_chat.py
# - demo_system.py
# - test_scraper_simple.py
# DECISIÓN: ¿Cuál es el punto de entrada oficial?
```

## 📊 **IMPACTO DEL ANÁLISIS**

### Archivos Core (MANTENER)
- ✅ `src/scraper/domain/assetplan_extractor_v2.py` - Core principal
- ✅ `src/scraper/services/scraper_manager.py` - Manager principal  
- ✅ `test_multi_typology.py` - Script CLI principal
- ✅ `tests/test_*_regression.py` - Tests de regresión críticos

### Archivos de Infraestructura (MANTENER)
- ✅ `src/scraper/infrastructure/` - Toda la infraestructura
- ✅ `src/scraper/models.py` - Modelos de datos
- ✅ `src/api/`, `src/rag/`, `src/vectorstore/` - Componentes adicionales

### Archivos de Configuración (MANTENER)
- ✅ `pytest.ini`, `requirements.txt`, `Makefile`
- ✅ `CLAUDE.md` - Instrucciones para Claude
- ✅ `docs/CLI_GUIDE.md`, `docs/multi_typology_feature.md` - Docs nuevas

## 🎯 **RECOMENDACIONES**

### Acción Inmediata
1. **Eliminar archivos claramente obsoletos**
2. **Consolidar scripts de testing**  
3. **Aclarar punto de entrada principal**

### Investigación Necesaria
1. **Revisar uso real de `assetplan_scraper.py`**
2. **Verificar dependencias de `professional_scraper.py`**
3. **Consolidar documentación redundante**

### Mejoras Estructurales
1. **Un solo punto de entrada CLI claro**
2. **Tests solo en `/tests/`** 
3. **Documentación consolidada en `/docs/`**