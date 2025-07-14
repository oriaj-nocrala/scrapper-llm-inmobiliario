# Guía de Deployment - AssetPlan Property Assistant

## 🚀 Opciones de Deployment

Esta guía cubre múltiples opciones de deployment desde desarrollo local hasta producción en la nube.

## 📋 Requisitos Previos

### **Sistema Operativo**
- ✅ Ubuntu 20.04+ (recomendado)
- ✅ macOS 11+ 
- ✅ Windows 10+ con WSL2
- ✅ Docker compatible

### **Hardware Mínimo**
- **CPU**: 2 cores, 2.4GHz
- **RAM**: 4GB (8GB recomendado)
- **Disco**: 10GB espacio libre
- **Red**: Conexión estable a internet

### **Software**
- Python 3.13+
- Chrome/Chromium browser
- OpenAI API Key válida

## 🔧 Deployment Local

### **1. Setup Básico**

```bash
# Clonar repositorio
git clone <repository-url>
cd scrapper-llm-inmobiliario

# Crear entorno virtual
python -m venv env
source env/bin/activate  # Linux/Mac
# env\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tu OpenAI API Key
```

### **2. Configuración de Entorno**

Crear archivo `.env`:
```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=text-embedding-ada-002

# Application Configuration
MAX_PROPERTIES=50
HEADLESS_BROWSER=true
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Paths
PROPERTIES_JSON_PATH=data/properties.json
FAISS_INDEX_PATH=data/faiss_index
LOGS_DIR=logs
```

### **3. Ejecutar Scraping Inicial**

```bash
# Ejecutar scraping (requerido antes del primer uso)
python -m src.scraper.professional_scraper --max-properties 50

# Verificar datos scrapeados
ls -la data/
cat data/properties.json | jq '.total_count'
```

### **4. Iniciar Servicios**

```bash
# Terminal 1: API REST
python run_api.py

# Terminal 2: CLI Interactivo (opcional)
python run_chat.py

# Verificar funcionamiento
curl http://localhost:8000/health
```

### **5. Verificar Installation**

```bash
# Ejecutar tests
python run_tests.py --type fast

# Verificar endpoints
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Hay propiedades disponibles?"}'
```

## 🐳 Deployment con Docker

### **1. Dockerfile**

```dockerfile
FROM python:3.13-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Configurar directorio de trabajo
WORKDIR /app

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear directorios necesarios
RUN mkdir -p data logs

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando por defecto
CMD ["python", "run_api.py"]
```

### **2. Docker Compose**

```yaml
version: '3.8'

services:
  property-assistant:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_MODEL=gpt-3.5-turbo
      - MAX_PROPERTIES=50
      - HEADLESS_BROWSER=true
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # Opcional: Nginx proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - property-assistant
    restart: unless-stopped
```

### **3. Comandos Docker**

```bash
# Build y ejecutar
docker-compose up --build -d

# Ver logs
docker-compose logs -f property-assistant

# Ejecutar scraping en container
docker-compose exec property-assistant python -m src.scraper.professional_scraper

# Ejecutar tests
docker-compose exec property-assistant python run_tests.py

# Parar servicios
docker-compose down
```

## ☁️ Deployment en AWS

### **1. EC2 Deployment**

#### **Launch EC2 Instance**
```bash
# Crear security group
aws ec2 create-security-group \
    --group-name property-assistant-sg \
    --description "Security group for Property Assistant"

# Permitir HTTP, HTTPS y SSH
aws ec2 authorize-security-group-ingress \
    --group-name property-assistant-sg \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-name property-assistant-sg \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-name property-assistant-sg \
    --protocol tcp \
    --port 8000 \
    --cidr 0.0.0.0/0

# Launch instance
aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --count 1 \
    --instance-type t3.medium \
    --key-name your-key-pair \
    --security-groups property-assistant-sg \
    --user-data file://user-data.sh
```

#### **User Data Script (user-data.sh)**
```bash
#!/bin/bash
yum update -y
yum install -y python3 python3-pip git docker

# Instalar Chrome
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
yum install -y google-chrome-stable

# Configurar Docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Clonar y configurar aplicación
cd /home/ec2-user
git clone <your-repo-url> scrapper-llm-inmobiliario
cd scrapper-llm-inmobiliario

# Configurar variables de entorno
echo "OPENAI_API_KEY=your-key-here" > .env
echo "API_HOST=0.0.0.0" >> .env
echo "API_PORT=8000" >> .env

# Instalar dependencias
pip3 install -r requirements.txt

# Ejecutar scraping inicial
python3 -m src.scraper.professional_scraper --max-properties 50

# Iniciar servicio
nohup python3 run_api.py > /var/log/property-assistant.log 2>&1 &
```

### **2. ECS Deployment**

#### **Task Definition**
```json
{
  "family": "property-assistant",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "property-assistant",
      "image": "your-account.dkr.ecr.region.amazonaws.com/property-assistant:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "API_HOST",
          "value": "0.0.0.0"
        },
        {
          "name": "API_PORT", 
          "value": "8000"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:openai-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/property-assistant",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### **3. Lambda Deployment**

#### **Serverless Framework**
```yaml
# serverless.yml
service: property-assistant

provider:
  name: aws
  runtime: python3.9
  region: us-east-1
  environment:
    OPENAI_API_KEY: ${env:OPENAI_API_KEY}
  timeout: 60
  memorySize: 3008

functions:
  api:
    handler: lambda_handler.handler
    events:
      - http:
          path: /{proxy+}
          method: ANY
          cors: true
    layers:
      - arn:aws:lambda:us-east-1:account:layer:chromium:1

plugins:
  - serverless-python-requirements
  - serverless-wsgi

custom:
  wsgi:
    app: src.api.property_api.app
  pythonRequirements:
    dockerizePip: true
```

#### **Lambda Handler**
```python
# lambda_handler.py
import json
from mangum import Mangum
from src.api.property_api import app

handler = Mangum(app, lifespan="off")
```

## 🌐 Deployment en Servicios Cloud

### **1. Google Cloud Run**

```bash
# Build y push imagen
gcloud builds submit --tag gcr.io/PROJECT_ID/property-assistant

# Deploy a Cloud Run
gcloud run deploy property-assistant \
  --image gcr.io/PROJECT_ID/property-assistant \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=your-key \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600
```

### **2. Azure Container Instances**

```bash
# Crear resource group
az group create --name property-assistant-rg --location eastus

# Deploy container
az container create \
  --resource-group property-assistant-rg \
  --name property-assistant \
  --image your-registry/property-assistant:latest \
  --ports 8000 \
  --environment-variables OPENAI_API_KEY=your-key API_PORT=8000 \
  --memory 4 \
  --cpu 2
```

### **3. Heroku**

```bash
# Configurar Heroku
heroku create property-assistant-app
heroku config:set OPENAI_API_KEY=your-key
heroku config:set BUILDPACK_URL=https://github.com/heroku/heroku-buildpack-google-chrome

# Deploy
git push heroku main

# Escalar dynos
heroku ps:scale web=1:standard-2x
```

## 🔒 Configuración de Producción

### **1. Variables de Entorno de Producción**

```env
# Production Environment
NODE_ENV=production
LOG_LEVEL=WARNING
API_DEBUG=false

# Security
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Performance
WORKER_PROCESSES=4
MAX_CONNECTIONS=1000
TIMEOUT=60

# Monitoring
SENTRY_DSN=your-sentry-dsn
DATADOG_API_KEY=your-datadog-key
```

### **2. Reverse Proxy (Nginx)**

```nginx
# nginx.conf
upstream property_assistant {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    location / {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://property_assistant;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /health {
        access_log off;
        proxy_pass http://property_assistant;
    }
}
```

### **3. Process Manager (Systemd)**

```ini
# /etc/systemd/system/property-assistant.service
[Unit]
Description=AssetPlan Property Assistant API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/property-assistant
Environment=PATH=/opt/property-assistant/env/bin
ExecStart=/opt/property-assistant/env/bin/python run_api.py
Restart=always
RestartSec=10

# Security
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/property-assistant/data /opt/property-assistant/logs

[Install]
WantedBy=multi-user.target
```

```bash
# Habilitar y iniciar servicio
sudo systemctl enable property-assistant
sudo systemctl start property-assistant
sudo systemctl status property-assistant
```

## 📊 Monitoreo y Logs

### **1. Logging Centralizado**

```python
# Configuración de logs para producción
import logging
from pythonjsonlogger import jsonlogger

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)
```

### **2. Health Checks**

```bash
# Script de monitoreo
#!/bin/bash
# health_check.sh

ENDPOINT="http://localhost:8000/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $ENDPOINT)

if [ $RESPONSE -eq 200 ]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy (HTTP $RESPONSE)"
    exit 1
fi
```

### **3. Alertas**

```yaml
# Prometheus alerting rules
groups:
  - name: property-assistant
    rules:
      - alert: ServiceDown
        expr: up{job="property-assistant"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Property Assistant service is down"
          
      - alert: HighResponseTime
        expr: http_request_duration_seconds{job="property-assistant"} > 5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
```

## 🛠️ Troubleshooting Deployment

### **Problemas Comunes**

#### **1. OpenAI API Key Issues**
```bash
# Verificar configuración
echo $OPENAI_API_KEY
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

#### **2. Memory Issues**
```bash
# Monitorear memoria
docker stats
htop

# Optimizar configuración
export MAX_PROPERTIES=25  # Reducir carga inicial
export RETRIEVAL_K=3      # Reducir documentos por query
```

#### **3. Port Conflicts**
```bash
# Verificar puertos ocupados
netstat -tlnp | grep :8000
lsof -i :8000

# Cambiar puerto
export API_PORT=8001
```

#### **4. Permission Issues**
```bash
# Permisos de archivos
chown -R www-data:www-data /opt/property-assistant
chmod +x run_api.py

# SELinux (si aplica)
setsebool -P httpd_can_network_connect 1
```

### **Scripts de Diagnóstico**

```bash
#!/bin/bash
# diagnostic.sh

echo "=== Property Assistant Diagnostics ==="

# Verificar Python
python3 --version

# Verificar dependencias
pip list | grep -E "(fastapi|langchain|openai|faiss)"

# Verificar Chrome
google-chrome --version

# Verificar datos
ls -la data/
echo "Properties count: $(cat data/properties.json | jq '.total_count' 2>/dev/null || echo 'N/A')"

# Verificar logs
tail -n 20 logs/application.log

# Test de endpoints
curl -s http://localhost:8000/health | jq .

echo "=== End Diagnostics ==="
```

## 📈 Escalabilidad

### **Horizontal Scaling**

```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  property-assistant:
    build: .
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data:ro  # Read-only para múltiples instancias
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx-lb.conf:/etc/nginx/nginx.conf
    depends_on:
      - property-assistant
```

```bash
# Escalar horizontalmente
docker-compose up --scale property-assistant=4
```

### **Load Balancing**

```nginx
# nginx-lb.conf
upstream backend {
    least_conn;
    server property-assistant_1:8000;
    server property-assistant_2:8000;
    server property-assistant_3:8000;
    server property-assistant_4:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://backend;
    }
}
```

---

**🚀 ¡Tu AssetPlan Property Assistant está listo para producción!**