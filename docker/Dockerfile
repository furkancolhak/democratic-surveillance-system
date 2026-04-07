FROM python:3.10-slim

# Sistem bağımlılıklarını yükle
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    g++ \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizini
WORKDIR /app

# Python bağımlılıklarını kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyalarını kopyala
COPY *.py ./
COPY violence_detection_model2.keras ./

# Gerekli dizinleri oluştur
RUN mkdir -p /app/encrypted_videos /app/decrypted_videos /app/violence_recordings /app/secrets

# Güvenlik: root olmayan kullanıcı oluştur
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:3333/health')" || exit 1

EXPOSE 3333

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:3333", "--timeout", "120", "secure_voting_web:app"]
