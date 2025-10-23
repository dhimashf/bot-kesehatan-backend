# Gunakan base image Python yang ringan
FROM python:3.10-slim

# Tetapkan direktori kerja di dalam container
WORKDIR /app

# Set variabel lingkungan agar Python tidak buffer output dan path module
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Install dependensi sistem yang mungkin dibutuhkan (misal untuk kompilasi beberapa library)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Salin file requirements terlebih dahulu untuk memanfaatkan cache Docker
COPY requirements.txt .

# Install dependensi Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode aplikasi ke dalam container
COPY . .

# Perintah untuk menjalankan aplikasi FastAPI dengan Uvicorn
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]