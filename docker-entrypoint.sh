#!/bin/bash
set -e

# Configuración de colores para logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Banner de inicio
cat << 'EOF'
 ____                                             _     _     __  __
/ ___|  ___ _ __ __ _ _ __  _ __   ___ _ __   | |   | |   |  \/  |
\___ \ / __| '__/ _` | '_ \| '_ \ / _ \ '__|  | |   | |   | |\/| |
 ___) | (__| | | (_| | |_) | |_) |  __/ |     | |___| |___| |  | |
|____/ \___|_|  \__,_| .__/| .__/ \___|_|     |_____|_____|_|  |_|
                     |_|   |_|
        🏠 Scrapper Inmobiliario con IA Local 🤖
EOF

log_info "Iniciando Scrapper LLM Inmobiliario..."

# Verificar directorio de trabajo
if [ ! -d "/app" ]; then
    log_error "Directorio de aplicación no encontrado"
    exit 1
fi

cd /app

# Crear directorios necesarios
log_info "Creando directorios necesarios..."
mkdir -p data logs cache ml-models data/faiss_index

# Verificar permisos
if [ ! -w "/app/data" ]; then
    log_warn "Sin permisos de escritura en /app/data"
fi

# Verificar dependencias críticas
log_info "Verificando dependencias críticas..."

# Verificar Python
if ! command -v python &> /dev/null; then
    log_error "Python no está instalado"
    exit 1
fi

# Verificar Chrome
if ! command -v google-chrome &> /dev/null; then
    log_error "Google Chrome no está instalado"
    exit 1
fi

# Verificar ChromeDriver
if ! command -v chromedriver &> /dev/null; then
    log_error "ChromeDriver no está instalado"
    exit 1
fi

# Verificar que el puerto no esté en uso
if [ "$1" = "api" ] || [ "$1" = "uvicorn" ]; then
    PORT=${PORT:-8000}
    if ss -tuln | grep -q ":$PORT "; then
        log_warn "Puerto $PORT ya está en uso"
    fi
fi

# Configurar variables de entorno para Chrome
export CHROME_BIN=/usr/bin/google-chrome
export CHROME_DRIVER=/usr/local/bin/chromedriver
export DISPLAY=:99

# Verificar modelos ML si existen
if [ -d "/app/ml-models" ] && [ "$(ls -A /app/ml-models)" ]; then
    log_info "Modelos ML encontrados en /app/ml-models"
    ls -la /app/ml-models/
else
    log_warn "No se encontraron modelos ML en /app/ml-models"
    log_info "Los modelos se pueden montar como volumen: -v ./ml-models:/app/ml-models"
fi

# Verificar configuración de base de datos/índices
if [ -f "/app/data/faiss_index/index.faiss" ]; then
    log_info "Índice FAISS encontrado"
else
    log_warn "Índice FAISS no encontrado, se creará en primera ejecución"
fi

# Configurar PYTHONPATH
export PYTHONPATH=/app:$PYTHONPATH

# Ejecutar comando según parámetros
log_info "Ejecutando comando: $@"

case "$1" in
    "api"|"uvicorn")
        log_info "Iniciando API en puerto ${PORT:-8000}"
        exec python -m uvicorn src.api.property_api:app --host 0.0.0.0 --port ${PORT:-8000} --reload
        ;;
    "dashboard")
        log_info "Iniciando Dashboard en puerto ${DASHBOARD_PORT:-8080}"
        exec python tools/dashboard/categorized_dashboard_server.py
        ;;
    "scraper")
        log_info "Iniciando Scraper profesional"
        exec python -m src.scraper.professional_scraper --quick --max-properties 10
        ;;
    "test")
        log_info "Ejecutando tests"
        exec python -m pytest tests/ -v
        ;;
    "analysis")
        log_info "Ejecutando análisis de código"
        exec python tools/code_analysis/smart_code_analyzer.py
        ;;
    "bash"|"shell")
        log_info "Iniciando shell interactivo"
        exec /bin/bash
        ;;
    "health")
        log_info "Verificando salud del sistema"
        python -c "
import requests
import sys
try:
    response = requests.get('http://localhost:8000/health', timeout=5)
    if response.status_code == 200:
        print('✅ Sistema saludable')
        sys.exit(0)
    else:
        print('❌ Sistema no disponible')
        sys.exit(1)
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"
        ;;
    *)
        log_info "Ejecutando comando personalizado: $@"
        exec "$@"
        ;;
esac