# ---- Builder Stage ----
# Tahap ini digunakan untuk menginstal dependensi, termasuk yang memerlukan kompilasi.
FROM python:3.10-slim AS builder

# Tetapkan direktori kerja di dalam container
WORKDIR /app

# Set variabel lingkungan
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependensi sistem yang mungkin dibutuhkan (misal untuk kompilasi beberapa library)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Buat virtual environment di dalam builder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Salin file requirements dan install dependensi ke dalam venv
COPY requirements.in requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir pip-tools && pip-sync requirements.txt

# Salin seluruh kode aplikasi ke dalam container
COPY . .

# ---- Runtime Stage ----
# Tahap ini adalah image akhir yang minimalis untuk produksi.
FROM python:3.10-slim AS runtime
WORKDIR /app

# Salin virtual environment yang sudah berisi dependensi dari tahap builder
COPY --from=builder /opt/venv /opt/venv

# Salin kode aplikasi dari tahap builder
COPY --from=builder /app /app

# Atur PATH untuk menggunakan Python dari venv dan tambahkan /app ke PYTHONPATH
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app

# Perintah untuk menjalankan aplikasi FastAPI dengan Uvicorn
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]