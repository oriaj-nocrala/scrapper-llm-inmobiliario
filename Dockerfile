# Dockerfile para Scrapper LLM Inmobiliario
# Imagen base con Python y herramientas necesarias
FROM python:3.13-slim

# Información del mantenedor
LABEL maintainer="Scrapper LLM Team"
LABEL description="Scrapper inmobiliario con IA local y dashboard de análisis"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    unzip \
    software-properties-common \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Instalar Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Instalar ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d'.' -f1-3) \
    && CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}") \
    && wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm /tmp/chromedriver.zip

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar llama-cpp-python para IA local
RUN pip install llama-cpp-python

# Copiar código fuente
COPY . .

# Crear directorios necesarios
RUN mkdir -p \
    /app/data \
    /app/logs \
    /app/cache \
    /app/ml-models \
    /app/data/faiss_index

# Permisos y configuración
RUN chmod +x /app/scripts/*.py
RUN chmod +x /app/tools/dashboard/categorized_dashboard_server.py
RUN chmod +x /app/docker-entrypoint.sh

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 scrapper && \
    chown -R scrapper:scrapper /app
USER scrapper

# Exponer puertos
EXPOSE 8000 8080 8888

# Volúmenes para persistencia
VOLUME ["/app/data", "/app/logs", "/app/cache", "/app/ml-models"]

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Punto de entrada
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Comando por defecto - iniciar la API
CMD ["api"]