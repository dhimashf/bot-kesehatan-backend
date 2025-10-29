# Menggunakan base image Python 3.11-slim
FROM python:3.11-slim

# Tetapkan direktori kerja di dalam container
WORKDIR /app

# Set variabel lingkungan untuk Python (mencegah file .pyc dan buffering)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependensi sistem:
# - 'gcc' & 'build-essential': Untuk mengkompilasi beberapa paket Python
# - 'curl': Untuk healthcheck
# - 'libpq5': Runtime library yang dibutuhkan oleh psycopg2 (PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    curl \
    libpq5 \
  && rm -rf /var/lib/apt/lists/*

# Upgrade pip dan salin file requirements.txt
RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt .

# Install semua paket Python dari requirements.txt
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Salin semua kode aplikasi Anda ke dalam container
COPY . .

# ===================================================================
# PERBAIKAN: Buat direktori cache SEBELUM beralih ke user non-root
# ===================================================================
RUN mkdir -p /app/cache && chmod -R 777 /app/cache

# Set environment variables untuk Hugging Face cache
ENV HF_HOME=/app/cache
ENV SENTENCE_TRANSFORMERS_HOME=/app/cache
ENV TRANSFORMERS_CACHE=/app/cache
ENV HF_HUB_DISABLE_SYMLINKS_WARNING=1

# Buat group dan user non-root untuk keamanan
RUN groupadd --system app && useradd --system --gid app app
RUN chown -R app:app /app

# Atur PYTHONPATH agar Python bisa menemukan modul di /app
ENV PYTHONPATH=/app

# Ganti ke user non-root
USER app

# Expose port
EXPOSE 8010

# Perintah default untuk menjalankan aplikasi Anda
CMD ["python", "main.py"]