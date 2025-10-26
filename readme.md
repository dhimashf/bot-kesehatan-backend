# Chatbot Psiko - Asisten Kesejahteraan Diri

Proyek ini adalah aplikasi asisten kesehatan mental yang komprehensif, menyediakan interaksi melalui bot Telegram dan antarmuka web. Backend dibangun dengan FastAPI dan dirancang untuk di-deploy menggunakan Docker, sementara frontend (berbasis Vanilla JS) dipisahkan untuk deployment mandiri (misalnya di Vercel).

## Fitur

- **Bot Telegram:** Berinteraksi dengan chatbot melalui bot Telegram.
- **Antarmuka Web:** Menyediakan alur registrasi, pengisian biodata, serangkaian kuesioner kesehatan (WHO-5, GAD-7, MBI, NAQ-R, K10), dan halaman profil untuk melihat riwayat.
- **Autentikasi Terpadu:** Pengguna dapat mendaftar dan login melalui antarmuka web atau bot Telegram, menggunakan akun yang sama di kedua platform.
- **Penyimpanan Riwayat:** Semua hasil kuesioner dan profil pengguna disimpan dalam database MySQL.
- **Layanan RAG:** Chatbot menggunakan *Retrieval-Augmented Generation* (RAG) untuk memberikan jawaban yang relevan berdasarkan basis pengetahuan (file PDF).
- **Siap Produksi:** Dilengkapi dengan konfigurasi Docker, Docker Compose, dan Nginx untuk deployment yang tangguh di server (VPS).

## Arsitektur

Proyek ini dibagi menjadi beberapa komponen:

- **`backend/`:** Direktori ini berisi aplikasi FastAPI.
    - **`app.py`:** Definisi utama aplikasi FastAPI, termasuk konfigurasi CORS dan router.
    - **`api/`:** Berisi semua endpoint API yang dikelompokkan berdasarkan fungsionalitas (auth, users, chat).
- **`bot_tele/`:** Direktori ini berisi kode untuk bot Telegram.
    - **`bot.py`:** Logika utama bot, termasuk `ConversationHandler` untuk alur kuesioner dan registrasi.
- **`static/` (Frontend):** Antarmuka web berbasis Vanilla JS, HTML, dan Tailwind CSS. Folder ini dirancang untuk di-deploy secara terpisah ke platform seperti Vercel.
- **`main.py`:** Skrip untuk **development lokal**. Menjalankan server API FastAPI dan bot Telegram secara bersamaan dalam thread terpisah untuk kemudahan pengembangan.
- **`common/`:** Direktori ini berisi modul umum yang digunakan oleh backend dan bot.
    - **`config/`:** Pengaturan aplikasi yang dimuat dari file `.env`.
    - **`data/`:** Data yang digunakan oleh layanan RAG (file PDF dan database ChromaDB).
    - **`schemas/`:** Skema Pydantic untuk validasi data API.
- **`core/`:** Direktori ini berisi layanan inti aplikasi.
    - **`services/`:** Layanan inti untuk interaksi database, OpenRouter, profiling, dan RAG.
- **Docker & Nginx:**
    - **`Dockerfile`:** Instruksi untuk membangun image container tunggal yang berisi backend dan bot.
    - **`docker-compose.yml`:** Mengorkestrasi layanan aplikasi (`app`) dan `nginx` untuk berjalan bersama di produksi.
    - **`nginx/nginx.conf`:** Konfigurasi Nginx sebagai *reverse proxy* untuk backend API.

## Persiapan

### Prasyarat

- Python 3.10 atau lebih tinggi
- Docker & Docker Compose (untuk deployment produksi)
- Database MySQL

### Instalasi

1. **Kloning repositori:**
   ```bash
   git clone https://github.com/your-username/your-repository.git
   ```
2. **Buat lingkungan virtual:**
   ```bash
   python -m venv venv
   ```
3. **Aktifkan lingkungan virtual:**
   - Di Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Di macOS dan Linux:
     ```bash
     source venv/bin/activate
     ```
4. **Instal dependensi:**
   ```bash
   pip install -r requirements.txt
   ```
   > **Catatan:** Jika Anda mendapatkan error `No matching distribution found` saat menginstal, kemungkinan besar `pip` Anda sudah usang. Perbarui `pip` dengan menjalankan:
   > ```bash
   > python -m pip install --upgrade pip
   > ```
   > Kemudian, jalankan kembali perintah `pip install -r requirements.txt`.

5. **Konfigurasi Variabel Lingkungan:**
   Buat file `.env` di direktori root dan tambahkan variabel berikut:
   ```env
   DB_HOST=your-db-host
   DB_USER=your-db-user
   DB_PASSWORD=your-db-password
   DB_NAME=your-db-name

   TELEGRAM_BOT_TOKEN=your-telegram-bot-token
   OPENROUTER_API_KEY=your-openrouter-api-key

   SECRET_KEY=your_super_secret_random_string_for_jwt
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # Nonaktifkan telemetri ChromaDB untuk menghindari potensi error
   ANONYMIZED_TELEMETRY=false
   ```

## Menjalankan Aplikasi

### 1. Development Lokal (Direkomendasikan)

1.  **Jalankan Backend & Bot:**
    Buka terminal, aktifkan virtual environment, dan jalankan `main.py`.
    ```bash
    python main.py
    ```
    Ini akan memulai server API di `http://localhost:8000` dan menjalankan bot Telegram.

2.  **Jalankan Frontend:**
    Buka terminal **kedua**, masuk ke direktori `static/`, dan jalankan server web sederhana.
    ```bash
    cd static
    python -m http.server 3000
    ```

3.  **Akses Aplikasi:**
    - Buka browser dan kunjungi `http://localhost:3000` untuk mengakses antarmuka web.
    - Cari bot Anda di Telegram dan mulai percakapan.

### 2. Deployment Produksi (Docker di VPS)

1.  **Deploy Frontend:**
    Deploy konten dari folder `static/` ke layanan hosting statis seperti Vercel atau Netlify.

2.  **Deploy Backend & Bot:**
    - Salin seluruh proyek (kecuali folder `static`) ke VPS Anda.
    - Pastikan Docker dan Docker Compose sudah terinstal di VPS.
    - Buat file `.env` di VPS dan isi dengan kredensial produksi.
    - Perbarui `nginx/nginx.conf` dengan nama domain atau IP VPS Anda.
    - Jalankan Docker Compose:
      ```bash
      docker-compose up --build -d
      ```
    Ini akan membangun dan menjalankan container untuk aplikasi utama (backend + bot) dan Nginx.

## Dokumentasi API

Dokumentasi detail untuk setiap endpoint API tersedia di file backend/README.md.
