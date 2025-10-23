# Gunakan base image Python yang sama dengan backend untuk konsistensi
FROM python:3.10-slim

# Tetapkan direktori kerja di dalam container
WORKDIR /app

# Set variabel lingkungan
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Salin file requirements terlebih dahulu
COPY requirements.txt .

# Install dependensi Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode aplikasi
COPY . .

# Perintah untuk menjalankan skrip bot
CMD ["python", "-m", "bot_tele.bot"]