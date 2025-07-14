# 🐳 Docker Setup - Scrapper LLM Inmobiliario

Este documento explica cómo usar Docker para ejecutar el Scrapper LLM Inmobiliario.

## 🚀 Inicio Rápido

### 1. Construcción básica

```bash
# Construir la imagen
docker build -t scrapper-llm .

# Ejecutar contenedor básico
docker run -p 8000:8000 scrapper-llm
```

### 2. Usando Docker Compose (Recomendado)

```bash
# Producción
docker-compose up -d

# Desarrollo
docker-compose -f docker-compose.dev.yml up -d
```

## 📁 Estructura de Volúmenes

```
./data          -> /app/data          # Datos persistentes
./logs          -> /app/logs          # Logs de aplicación
./cache         -> /app/cache         # Cache de análisis
./ml-models     -> /app/ml-models     # Modelos de IA local
```

## 🔧 Configuración

### Variables de Entorno

```bash
# Ambiente
ENVIRONMENT=production|development
LOG_LEVEL=INFO|DEBUG|WARNING|ERROR

# Chrome/Selenium
CHROME_NO_SANDBOX=true
CHROME_HEADLESS=true
WEBDRIVER_CHROME_DRIVER=/usr/local/bin/chromedriver

# Puertos
PORT=8000                    # API principal
DASHBOARD_PORT=8080          # Dashboard
```

### Archivo .env

```env
# API Configuration
PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=production

# Chrome Configuration
CHROME_HEADLESS=true
CHROME_NO_SANDBOX=true

# IA Configuration
ML_MODELS_PATH=/app/ml-models
VRAM_LIMIT=8GB
```

## 🎛️ Comandos Disponibles

### Servicios Principales

```bash
# API principal
docker-compose exec scrapper-llm python docker-entrypoint.sh api

# Dashboard
docker-compose exec scrapper-llm python docker-entrypoint.sh dashboard

# Scraper
docker-compose exec scrapper-llm python docker-entrypoint.sh scraper

# Tests
docker-compose exec scrapper-llm python docker-entrypoint.sh test

# Análisis de código
docker-compose exec scrapper-llm python docker-entrypoint.sh analysis

# Shell interactivo
docker-compose exec scrapper-llm python docker-entrypoint.sh bash
```

### Servicios Individuales

```bash
# Solo API
docker run -p 8000:8000 -v ./data:/app/data scrapper-llm api

# Solo Dashboard
docker run -p 8080:8080 -v ./data:/app/data scrapper-llm dashboard

# Solo Scraper
docker run -v ./data:/app/data scrapper-llm scraper
```

## 🔄 Desarrollo

### Setup de Desarrollo

```bash
# Usar docker-compose para desarrollo
docker-compose -f docker-compose.dev.yml up -d

# Acceder al contenedor
docker-compose -f docker-compose.dev.yml exec scrapper-llm-dev bash

# Jupyter Lab (opcional)
docker-compose -f docker-compose.dev.yml exec jupyter bash
```

### Hot Reload

El archivo `docker-compose.dev.yml` incluye:
- Montaje de código fuente para hot reload
- Debugging habilitado
- Jupyter Lab para desarrollo
- Bases de datos opcionales

## 📊 Monitoreo

### Health Check

```bash
# Verificar salud del contenedor
docker-compose exec scrapper-llm python docker-entrypoint.sh health

# Logs en tiempo real
docker-compose logs -f scrapper-llm

# Métricas del sistema
docker stats scrapper-llm
```

### Logs

```bash
# Logs de aplicación
docker-compose logs scrapper-llm

# Logs específicos
docker-compose exec scrapper-llm tail -f /app/logs/application.log
```

## 🚨 Troubleshooting

### Problemas Comunes

#### 1. Chrome/ChromeDriver
```bash
# Verificar Chrome
docker-compose exec scrapper-llm google-chrome --version

# Verificar ChromeDriver
docker-compose exec scrapper-llm chromedriver --version
```

#### 2. Permisos
```bash
# Verificar permisos
docker-compose exec scrapper-llm ls -la /app/data

# Corregir permisos
sudo chown -R 1000:1000 ./data ./logs ./cache
```

#### 3. Modelos ML
```bash
# Verificar modelos
docker-compose exec scrapper-llm ls -la /app/ml-models

# Descargar modelos (ejemplo)
wget -P ./ml-models https://huggingface.co/...
```

#### 4. Memoria/VRAM
```bash
# Verificar recursos
docker-compose exec scrapper-llm free -h
docker-compose exec scrapper-llm nvidia-smi  # Si tiene GPU
```

## 🔧 Configuración Avanzada

### GPU Support (NVIDIA)

```yaml
# En docker-compose.yml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

### Múltiples Instancias

```bash
# Escalar servicios
docker-compose up -d --scale scrapper-llm=3

# Load balancer (nginx)
docker-compose -f docker-compose.yml -f docker-compose.nginx.yml up -d
```

### Backup y Restore

```bash
# Backup de datos
docker run --rm -v $(pwd)/data:/backup alpine tar czf /backup/backup.tar.gz /app/data

# Restore
docker run --rm -v $(pwd)/data:/restore alpine tar xzf /restore/backup.tar.gz
```

## 🛡️ Seguridad

### Usuario No-Root

El contenedor ejecuta como usuario `scrapper` (UID: 1000) por seguridad.

### Secrets

```bash
# Usar Docker secrets
echo "mi_api_key" | docker secret create api_key -

# En docker-compose.yml
secrets:
  - api_key
```

### Network Security

```yaml
# Red personalizada
networks:
  scrapper-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## 📚 Recursos Adicionales

- [Docker Hub Repository](https://hub.docker.com/r/scrapper-llm)
- [Documentación API](./docs/API_DOCUMENTATION.md)
- [Guía de Desarrollo](./docs/DEVELOPMENT.md)
- [Troubleshooting](./docs/TROUBLESHOOTING.md)

## 🤝 Contribución

Para contribuir con mejoras a Docker:

1. Probar cambios en `docker-compose.dev.yml`
2. Actualizar `Dockerfile` y `docker-entrypoint.sh`
3. Documentar cambios en este README
4. Enviar PR con tests incluidos

---

**Nota**: Este setup de Docker está optimizado para desarrollo y producción. Para despliegues específicos, consultar con el equipo de DevOps.