# 🔧 Guía Completa de CLI - Scraper AssetPlan

## 📋 Comandos Disponibles

### 🚀 Script Principal Multi-Tipología

```bash
python test_multi_typology.py [OPTIONS]
```

#### Opciones Disponibles

| Flag | Tipo | Default | Descripción |
|------|------|---------|-------------|
| `--max-properties` | int | 10 | Máximo número de propiedades a extraer |
| `--max-typologies` | int | None | Máximo número de edificios/tipologías a procesar |
| `--debug` | flag | False | Activar modo debug (browser visible) |
| `--behavior` | choice | extreme | Modo de comportamiento del scraper |
| `--help` | flag | - | Mostrar ayuda y salir |

#### Valores de `--behavior`

- `extreme`: **Modo más rápido** - Mínimos delays, sin logs detallados
- `fast`: Modo rápido con algunos logs
- `normal`: Modo estándar con delays normales

---

## 📖 Ejemplos de Uso

### 🏠 Modo Estándar (Un edificio)

```bash
# Extraer 5 propiedades del primer edificio encontrado
python test_multi_typology.py --max-properties 5

# Con modo debug para ver el browser
python test_multi_typology.py --max-properties 3 --debug

# Modo más lento para depuración
python test_multi_typology.py --max-properties 8 --behavior normal
```

### 🏢 Modo Multi-Tipología (Múltiples edificios)

```bash
# Extraer 12 propiedades de hasta 3 edificios diferentes
python test_multi_typology.py --max-properties 12 --max-typologies 3

# Extraer 20 propiedades de hasta 5 edificios (modo extremo)
python test_multi_typology.py --max-properties 20 --max-typologies 5

# Debug multi-tipología para ver navegación
python test_multi_typology.py --max-properties 6 --max-typologies 2 --debug --behavior normal
```

### ⚡ Comandos de Prueba Rápida

```bash
# Test rápido: 3 props, 2 edificios
python test_multi_typology.py --max-properties 3 --max-typologies 2

# Test completo: 15 props, 4 edificios  
python test_multi_typology.py --max-properties 15 --max-typologies 4

# Test debug visual
python test_multi_typology.py --max-properties 4 --max-typologies 2 --debug
```

---

## 🧪 Comandos de Testing

### 🔍 Tests de Regresión

```bash
# Tests específicos de multi-tipología
python -m pytest tests/test_multi_typology_regression.py -v

# Tests de regresión core (modal, piso, tipologías)
python -m pytest tests/test_regression_core.py -v

# Tests del extractor V2
python -m pytest tests/test_assetplan_extractor_v2.py -v

# Todos los tests (excluyendo integración)
python -m pytest tests/ -k "not integration" --tb=short
```

### 📊 Tests Específicos

```bash
# Solo tests de navegación back
python -m pytest tests/test_multi_typology_regression.py::TestMultiTypologyNavigation -v

# Solo tests de distribución de propiedades
python -m pytest tests/test_multi_typology_regression.py::TestMultiTypologyLogic -v

# Solo tests de performance
python -m pytest tests/test_multi_typology_regression.py::TestMultiTypologyPerformance -v

# Tests de extracción de piso (prevención regresión 37s)
python -m pytest tests/test_regression_core.py::TestFloorExtractionRegression -v
```

---

## 🔧 Comandos de Desarrollo

### 🐍 Activar Entorno

```bash
# Activar virtual environment
source env/bin/activate

# Verificar instalación
python -c "from src.scraper.services.scraper_manager import scrape_properties_quick; print('✅ OK')"
```

### 📦 Instalación de Dependencias

```bash
# Instalar dependencias básicas
pip install selenium

# Verificar Chrome/Chromium (requerido para Selenium)
google-chrome --version
# o
chromium --version
```

### 📝 Logs y Debug

```bash
# Con logs detallados
python test_multi_typology.py --max-properties 5 --behavior normal

# Modo debug completo (browser visible + logs)
python test_multi_typology.py --max-properties 3 --debug --behavior normal

# Solo en modo extremo (mínimos logs)
python test_multi_typology.py --max-properties 10 --max-typologies 3
```

---

## 🎯 Casos de Uso Comunes

### 🔍 Exploración Inicial

```bash
# Conocer el scraper - pocas propiedades, modo debug
python test_multi_typology.py --max-properties 2 --debug --behavior normal
```

### 📊 Recolección de Datos

```bash
# Dataset pequeño pero diverso - multiple edificios
python test_multi_typology.py --max-properties 15 --max-typologies 4

# Dataset grande de un edificio específico
python test_multi_typology.py --max-properties 25
```

### 🐛 Debugging y Desarrollo

```bash
# Debug navegación multi-tipología
python test_multi_typology.py --max-properties 4 --max-typologies 2 --debug --behavior normal

# Verificar performance sin regresiones
python -m pytest tests/test_regression_core.py::TestFloorExtractionRegression::test_floor_extraction_performance_under_1_second -v
```

### ⚡ Testing Rápido

```bash
# Test básico funcionalidad
python test_multi_typology.py --max-properties 3

# Test multi-tipología básico
python test_multi_typology.py --max-properties 6 --max-typologies 2

# Verificar que todo funciona
python -m pytest tests/test_regression_core.py -v
```

---

## 📈 Interpretación de Resultados

### 📊 Output Esperado

```bash
🚀 Iniciando scraper con configuración:
   • Max propiedades: 10
   • Max tipologías: 3
   • Modo: extreme
   • Debug: False

🏢 MODO MULTI-TIPOLOGÍA activado: extraerá de 3 edificios diferentes

✅ Scraping completado:
   • Total propiedades: 10
   • Total tipologías: 3
   • Fuente: https://www.assetplan.cl/arriendo/departamento
   • Guardado en: data/properties.json

📊 Tipologías encontradas:
   • 1 dormitorio 1 baño: 4 propiedades, 7 imágenes
   • 2 dormitorios 2 baños: 3 propiedades, 5 imágenes
   • Estudio: 3 propiedades, 4 imágenes

🎉 ¡Proceso exitoso! 10 propiedades extraídas
```

### 📁 Archivos Generados

```bash
data/properties.json    # Datos extraídos en formato JSON optimizado
```

### 🔍 Estructura de Datos

```json
{
  "properties": [
    {
      "id": "495857", 
      "title": "Home Inclusive Independencia - Depto 1011-A",
      "price": "$154.414",
      "floor": 10,
      "typology_id": "bed1_bath1_area51_1dormitori",
      "images": []  // Vacío - imágenes están en tipología
    }
  ],
  "typologies": {
    "bed1_bath1_area51_1dormitori": {
      "name": "1 dormitorio 1 baño",
      "images": ["img1.jpg", "img2.jpg", ...]  // Todas las imágenes aquí
    }
  },
  "total_count": 10,
  "scraped_at": "2025-07-13T...",
  "source_url": "https://www.assetplan.cl/arriendo/departamento"
}
```

---

## ⚠️ Troubleshooting

### 🚫 Errores Comunes

```bash
# Error: "No module named 'src'"
# Solución: Ejecutar desde directorio raíz del proyecto
cd /ruta/al/proyecto/scrapper-llm-inmobiliario
python test_multi_typology.py --max-properties 5

# Error: "selenium.common.exceptions.WebDriverException"
# Solución: Verificar Chrome/Chromium instalado
google-chrome --version

# Error: "No se pudo navegar back"
# Solución: Usar modo debug para investigar
python test_multi_typology.py --max-properties 3 --max-typologies 2 --debug
```

### 🔧 Verificación del Sistema

```bash
# Verificar que todo está funcionando
python -c "
from src.scraper.services.scraper_manager import ScrapingConfig
config = ScrapingConfig(max_properties=1, max_typologies=1)
print(f'✅ Config OK: {config.max_properties} props, {config.max_typologies} tipologías')
"

# Test rápido de extractor
python -m pytest tests/test_regression_core.py::TestFloorExtractionRegression::test_floor_extraction_performance_under_1_second -v
```

---

## 📚 Referencias Rápidas

### 🎛️ Modos de Configuración

| Comando | Modo | Edificios | Performance | Uso |
|---------|------|-----------|-------------|-----|
| `--max-properties 5` | Estándar | 1 | ⚡⚡⚡ | Testing rápido |
| `--max-properties 10 --max-typologies 3` | Multi | 3 | ⚡⚡ | Dataset diverso |
| `--debug --behavior normal` | Debug | Variable | ⚡ | Desarrollo |

### 🔍 Tests por Categoría

```bash
# Funcionalidad básica
pytest tests/test_regression_core.py -v

# Multi-tipología  
pytest tests/test_multi_typology_regression.py -v

# Performance (regresión 37s)
pytest tests/test_regression_core.py::TestFloorExtractionRegression -v

# Navegación back
pytest tests/test_multi_typology_regression.py::TestMultiTypologyNavigation -v
```

### 🏃‍♂️ Comandos de Un Solo Uso

```bash
# Testing rápido
python test_multi_typology.py --max-properties 3 --max-typologies 2

# Producción diversa
python test_multi_typology.py --max-properties 20 --max-typologies 5

# Debug completo
python test_multi_typology.py --max-properties 2 --debug --behavior normal
```