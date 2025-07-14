#!/bin/bash

# Script de construcción para Scrapper LLM Inmobiliario
# Uso: ./build.sh [opción]

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuración
PROJECT_NAME="scrapper-llm"
IMAGE_NAME="scrapper-llm"
VERSION=$(date +%Y%m%d_%H%M%S)
LATEST_TAG="latest"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
🐳 Script de Construcción - Scrapper LLM Inmobiliario

Uso: $0 [OPCIÓN]

OPCIONES:
    build           Construir imagen Docker
    run             Ejecutar contenedor
    dev             Iniciar entorno de desarrollo
    push            Subir imagen al registry
    clean           Limpiar imágenes y contenedores
    test            Ejecutar tests en contenedor
    logs            Ver logs del contenedor
    health          Verificar salud del contenedor
    help            Mostrar esta ayuda

EJEMPLOS:
    $0 build        # Construir imagen
    $0 run          # Ejecutar contenedor
    $0 dev          # Desarrollo con hot reload
    $0 clean        # Limpiar todo
EOF
}

build_image() {
    log_info "Construyendo imagen Docker..."
    log_info "Imagen: $IMAGE_NAME:$VERSION"
    
    # Verificar que Dockerfile existe
    if [ ! -f "Dockerfile" ]; then
        log_error "Dockerfile no encontrado"
        exit 1
    fi
    
    # Construir imagen
    docker build \
        -t "$IMAGE_NAME:$VERSION" \
        -t "$IMAGE_NAME:$LATEST_TAG" \
        --progress=plain \
        .
    
    log_info "✅ Imagen construida exitosamente"
    log_info "Tags: $IMAGE_NAME:$VERSION, $IMAGE_NAME:$LATEST_TAG"
}

run_container() {
    log_info "Ejecutando contenedor..."
    
    # Verificar que la imagen existe
    if ! docker image inspect "$IMAGE_NAME:$LATEST_TAG" >/dev/null 2>&1; then
        log_warn "Imagen no encontrada, construyendo..."
        build_image
    fi
    
    # Crear directorios si no existen
    mkdir -p data logs cache ml-models
    
    # Ejecutar contenedor
    docker run -d \
        --name "$PROJECT_NAME" \
        -p 8000:8000 \
        -p 8080:8080 \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd)/logs:/app/logs" \
        -v "$(pwd)/cache:/app/cache" \
        -v "$(pwd)/ml-models:/app/ml-models" \
        --restart unless-stopped \
        "$IMAGE_NAME:$LATEST_TAG"
    
    log_info "✅ Contenedor ejecutándose"
    log_info "API: http://localhost:8000"
    log_info "Dashboard: http://localhost:8080"
}

run_dev() {
    log_info "Iniciando entorno de desarrollo..."
    
    if [ ! -f "docker-compose.dev.yml" ]; then
        log_error "docker-compose.dev.yml no encontrado"
        exit 1
    fi
    
    docker-compose -f docker-compose.dev.yml up -d
    
    log_info "✅ Entorno de desarrollo iniciado"
    log_info "API: http://localhost:8000"
    log_info "Dashboard: http://localhost:8080"
    log_info "Jupyter: http://localhost:8889"
}

push_image() {
    log_info "Subiendo imagen al registry..."
    
    # Verificar que la imagen existe
    if ! docker image inspect "$IMAGE_NAME:$LATEST_TAG" >/dev/null 2>&1; then
        log_error "Imagen no encontrada. Ejecuta 'build' primero"
        exit 1
    fi
    
    # Aquí deberías configurar tu registry
    # REGISTRY="your-registry.com"
    # docker tag "$IMAGE_NAME:$LATEST_TAG" "$REGISTRY/$IMAGE_NAME:$VERSION"
    # docker push "$REGISTRY/$IMAGE_NAME:$VERSION"
    
    log_warn "Configurar registry en build.sh para push"
}

clean_docker() {
    log_info "Limpiando Docker..."
    
    # Detener contenedores
    docker-compose down 2>/dev/null || true
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    
    # Remover contenedor si existe
    if docker container inspect "$PROJECT_NAME" >/dev/null 2>&1; then
        docker rm -f "$PROJECT_NAME"
    fi
    
    # Remover imágenes
    docker image rm "$IMAGE_NAME:$LATEST_TAG" 2>/dev/null || true
    docker image rm "$IMAGE_NAME:$VERSION" 2>/dev/null || true
    
    # Limpiar sistema
    docker system prune -f
    
    log_info "✅ Limpieza completada"
}

run_tests() {
    log_info "Ejecutando tests en contenedor..."
    
    # Verificar que la imagen existe
    if ! docker image inspect "$IMAGE_NAME:$LATEST_TAG" >/dev/null 2>&1; then
        log_warn "Imagen no encontrada, construyendo..."
        build_image
    fi
    
    # Ejecutar tests
    docker run --rm \
        -v "$(pwd)/tests:/app/tests" \
        "$IMAGE_NAME:$LATEST_TAG" \
        test
    
    log_info "✅ Tests completados"
}

show_logs() {
    log_info "Mostrando logs del contenedor..."
    
    if docker container inspect "$PROJECT_NAME" >/dev/null 2>&1; then
        docker logs -f "$PROJECT_NAME"
    else
        log_error "Contenedor '$PROJECT_NAME' no encontrado"
        exit 1
    fi
}

check_health() {
    log_info "Verificando salud del contenedor..."
    
    if docker container inspect "$PROJECT_NAME" >/dev/null 2>&1; then
        docker exec "$PROJECT_NAME" /app/docker-entrypoint.sh health
    else
        log_error "Contenedor '$PROJECT_NAME' no encontrado"
        exit 1
    fi
}

# Procesamiento de argumentos
case "${1:-help}" in
    build)
        build_image
        ;;
    run)
        run_container
        ;;
    dev)
        run_dev
        ;;
    push)
        push_image
        ;;
    clean)
        clean_docker
        ;;
    test)
        run_tests
        ;;
    logs)
        show_logs
        ;;
    health)
        check_health
        ;;
    help|*)
        show_help
        ;;
esac