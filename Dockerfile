# Dockerfile Tunggal untuk Aplikasi PsikoBot (Backend + Bot)

# ---- Builder Stage ----
# Tahap ini digunakan untuk menginstal dependensi, termasuk yang memerlukan kompilasi.
FROM python:3.11-slim AS builder

# Tetapkan direktori kerja di dalam container
WORKDIR /app

# Set variabel lingkungan untuk Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependensi sistem yang mungkin dibutuhkan (misal untuk kompilasi beberapa library)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Buat virtual environment di dalam builder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Salin file requirements dan install dependensi ke dalam venv
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode aplikasi ke dalam container
COPY . .

# ---- Runtime Stage ----
# Tahap ini adalah image akhir yang minimalis untuk produksi.
FROM python:3.11-slim AS runtime
WORKDIR /app

# Buat group dan user non-root untuk menjalankan aplikasi
RUN groupadd --system app && useradd --system --gid app app

# Install curl untuk healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Salin virtual environment yang sudah berisi dependensi dari tahap builder
COPY --from=builder /opt/venv /opt/venv
# Salin kode aplikasi dari tahap builder
COPY --from=builder /app /app

# Berikan kepemilikan direktori aplikasi kepada user non-root
RUN chown -R app:app /app

# Atur PATH untuk menggunakan Python dari venv dan tambahkan /app ke PYTHONPATH
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app

# Ganti ke user non-root
USER app

# Perintah untuk menjalankan aplikasi utama yang berisi backend dan bot
CMD ["python", "main.py"]