FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema si fueran necesarias
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requerimientos e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m pip install --no-cache-dir --upgrade setuptools

# Copiar todo el código de la aplicación
COPY . .

# Puerto por defecto
ENV PORT=6767
ENV FORWARDED_ALLOW_IPS=127.0.0.1
EXPOSE 6767

# Comando de ejecución
CMD ["sh", "-c", "python -m uvicorn backend.main:app --host 0.0.0.0 --port 6767 --proxy-headers --forwarded-allow-ips=$FORWARDED_ALLOW_IPS"]
