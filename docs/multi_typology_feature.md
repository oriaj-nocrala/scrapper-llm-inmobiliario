# Funcionalidad Multi-Tipología 🏢

## Descripción

La funcionalidad **Multi-Tipología** permite extraer propiedades de múltiples edificios/tipologías en una sola ejecución del scraper, usando navegación inteligente back para saltar entre edificios.

## Uso

### Comando de línea

```bash
# Extraer 10 propiedades de hasta 3 edificios diferentes
python test_multi_typology.py --max-properties 10 --max-typologies 3

# Modo debug para ver el navegador
python test_multi_typology.py --max-properties 6 --max-typologies 2 --debug

# Modo más lento para depuración
python test_multi_typology.py --max-properties 8 --max-typologies 2 --behavior normal
```

### Programático

```python
from src.scraper.services.scraper_manager import ScrapingConfig, scrape_properties_quick

# Usando función de conveniencia
collection = scrape_properties_quick(max_properties=15, max_typologies=3)

# Usando configuración completa
config = ScrapingConfig(
    max_properties=20,
    max_typologies=4,
    behavior_mode="extreme"
)

with ScraperManager(config) as manager:
    collection = manager.scrape_properties()
```

## Cómo Funciona

### Flujo de Navegación

1. **Inicio**: Lista de edificios (`/arriendo/departamento`)
2. **Edificio 1**: Procesar tipologías → extraer N propiedades
3. **Back x2**: `page departamento` → `page edificio` → `lista edificios`
4. **Edificio 2**: Procesar tipologías → extraer M propiedades  
5. **Repetir** hasta `max_typologies` edificios o `max_properties` total

### Distribución de Propiedades

El scraper distribuye inteligentemente las propiedades entre edificios:

```python
properties_per_building = max(1, max_properties // max_typologies)
```

**Ejemplos:**
- `--max-properties 15 --max-typologies 3` → ~5 props por edificio
- `--max-properties 10 --max-typologies 4` → ~2-3 props por edificio  
- `--max-properties 2 --max-typologies 5` → mínimo 1 prop por edificio

### URLs Esperadas

La navegación back debe seguir este patrón:

```
# Página de departamento
https://www.assetplan.cl/arriendo/departamento/independencia/home-inclusive/3063?selectedUnit=495857

# Back #1 → Página de edificio  
https://www.assetplan.cl/arriendo/departamento/independencia/home-inclusive/3063

# Back #2 → Lista de edificios
https://www.assetplan.cl/arriendo/departamento?page=1
```

## Configuración

### Parámetros

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `max_properties` | int | 50 | Máximo total de propiedades |
| `max_typologies` | int | None | Máximo número de edificios (None = ilimitado) |

### Modos de Operación

- **max_typologies = None**: Modo estándar (un edificio secuencial)
- **max_typologies = 1**: Modo estándar (un edificio)  
- **max_typologies > 1**: **Modo Multi-Tipología** (múltiples edificios)

## Prevención de Regresiones

### Tests Automáticos

```bash
# Tests específicos de multi-tipología
pytest tests/test_multi_typology_regression.py -v

# Tests de regresión general  
pytest tests/test_regression_core.py -v
```

### Tests Cubiertos

- ✅ Configuración de parámetros
- ✅ Navegación back exitosa/fallida
- ✅ Distribución de propiedades entre edificios
- ✅ Respeto de límites máximos
- ✅ Recuperación de errores
- ✅ Selección automática de modo
- ✅ Performance de navegación

## Beneficios

### 🎯 **Diversidad de Datos**
Extrae de múltiples edificios para obtener mayor variedad de tipologías y precios.

### ⚡ **Eficiencia**
Evita procesar todo un edificio cuando solo necesitas pocas propiedades.

### 🛡️ **Robustez** 
Navegación inteligente con recuperación de errores y validación de URLs.

### 📊 **Optimización de Imágenes**
Mantiene la estructura optimizada donde imágenes se almacenan en tipologías.

## Limitaciones

- **Dependiente de navegación back**: Si la estructura de URLs cambia, puede fallar
- **Performance**: Navegación adicional añade tiempo entre edificios
- **Complejidad**: Mayor superficie de fallo comparado con modo estándar

## Troubleshooting

### Error: "No se pudo navegar back a lista de edificios"

**Causa**: URLs inesperadas o estructura de navegación cambiada

**Solución**: 
1. Verificar URLs en modo debug
2. Actualizar patrones de URL en `_navigate_back_to_buildings_list()`

### Propiedades menos de lo esperado

**Causa**: Edificios con pocas propiedades disponibles

**Solución**: 
1. Aumentar `max_typologies` para compensar
2. Verificar que edificios tengan suficientes propiedades

### Performance lenta

**Causa**: Delays entre navegación de edificios

**Solución**:
1. Usar `behavior_mode="extreme"` para mínimos delays
2. Reducir `max_typologies` si no necesitas tantos edificios