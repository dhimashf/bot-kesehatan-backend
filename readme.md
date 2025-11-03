# Chatbot Psiko - Asisten Kesejahteraan Diri Berbasis AI

Proyek ini adalah sebuah platform asisten kesehatan mental komprehensif yang dapat diakses melalui **Bot Telegram** dan **Antarmuka Web**. Sistem ini dirancang untuk memberikan dukungan psikologis awal yang dipersonalisasi, menggunakan Large Language Model (LLM) yang diperkaya dengan profil psikometrik pengguna dan basis pengetahuan yang relevan.

## ✨ Fitur Utama

- **Interaksi Multi-Platform**: Pengguna dapat berinteraksi dengan sistem melalui Bot Telegram untuk kemudahan akses atau melalui Antarmuka Web untuk pengalaman yang lebih visual.
- **Profil Psikometrik Komprehensif**: Sistem mengumpulkan data melalui lima kuesioner standar industri (WHO-5, GAD-7, MBI, NAQ-R, K10) untuk membangun profil kesehatan mental pengguna yang mendalam.
- **Personalisasi Respons AI**: Inovasi inti dari proyek ini adalah kemampuan untuk menyuntikkan ringkasan profil psikometrik pengguna sebagai konteks ke dalam *system prompt* LLM. Hal ini membuat respons AI menjadi **adaptif** dan disesuaikan dengan kondisi spesifik pengguna.
- **Retrieval-Augmented Generation (RAG)**: Jawaban dari chatbot didasarkan pada basis pengetahuan yang terkontrol (file `kitab.pdf`), memastikan relevansi, akurasi, dan keamanan informasi yang diberikan.
- **Autentikasi Terpadu**: Satu akun pengguna dapat digunakan untuk login di kedua platform (Telegram dan Web), memberikan pengalaman yang mulus.
- **Manajemen Riwayat**: Pengguna dapat melihat riwayat hasil kuesioner mereka dari waktu ke waktu melalui antarmuka web, memungkinkan pemantauan perkembangan kondisi.
- **Arsitektur Siap Produksi**: Proyek ini dikemas dengan Docker, Docker Compose, dan Nginx, siap untuk di-deploy di lingkungan produksi seperti VPS.

## 🏗️ Arsitektur Sistem

Sistem ini terdiri dari beberapa komponen utama yang bekerja sama:

```
      Pengguna           Pengguna
         |                  |
     (Telegram)           (Web Browser)
         |                  |
         |             (Vercel/Netlify)
         |                  |
         +-------+----------+
                 |
              (Internet)
                 |
      +--------- v ---------+
      |   NGINX (Reverse Proxy)  |  <-- Port 80/443
      +--------------------------+
                 |
      +--------- v ---------+
      | Docker Container: app    |
      |--------------------------|
      |  - FastAPI Backend (API) |  <-- Port 8010 (internal)
      |  - Telegram Bot Polling  |
      |--------------------------|
      |      Core Services       |
      |  - OpenRouter (LLM)      |
      |  - RAG (ChromaDB)        |
      |  - Profiling             |
      |  - Database              |
      +--------------------------+
                 |
       +---------+----------+
       |                    |
       v                    v
  (MySQL DB)         (OpenRouter API)
```

## 🛠️ Tumpukan Teknologi

- **Backend**: FastAPI
- **Bot**: `python-telegram-bot`
- **Database**: MySQL
- **LLM Service**: OpenRouter
- **Vector Store (RAG)**: ChromaDB
- **Deployment**: Docker, Docker Compose, Nginx
- **Frontend**:  HTML, Tailwind CSS (dideploy terpisah)

## 📂 Struktur Proyek

```
.
├── backend/         # Aplikasi FastAPI (API endpoints)
├── bot_tele/        # Logika Bot Telegram (ConversationHandler, dll.)
├── common/          # Modul bersama (konfigurasi, skema data)
├── core/            # Layanan inti (database, RAG, profiling, LLM)
├── static/          # Kode Frontend (HTML, JS, CSS) - untuk deployment terpisah
├── main.py          # Titik masuk untuk development lokal
├── Dockerfile       # Instruksi build image Docker
├── docker-compose.yml # Orkestrasi container untuk produksi
├── nginx/           # Konfigurasi Nginx sebagai reverse proxy
└── requirements.txt # Dependensi Python
```

## 🚀 Instalasi dan Konfigurasi

### 1. Prasyarat
- Python 3.10+
- Docker & Docker Compose
- Database MySQL yang sedang berjalan

### 2. Langkah Instalasi
1.  **Kloning Repositori**
    ```bash
    git clone https://github.com/your-username/your-repository.git
    cd your-repository
    ```
2.  **Buat dan Aktifkan Lingkungan Virtual**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```
3.  **Instal Dependensi**
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```
4.  **Konfigurasi Variabel Lingkungan**
    Buat file `.env` di direktori root proyek dan isi dengan konfigurasi Anda.
    ```env
    # Konfigurasi Database
    DB_HOST=127.0.0.1
    DB_USER=root
    DB_PASSWORD=
    DB_NAME=kesehatan

    # Kunci API
    TELEGRAM_BOT_TOKEN=your-telegram-bot-token
    OPENROUTER_API_KEY=your-openrouter-api-key

    # Google OAuth2 Credentials (Opsional, untuk login via Google)
    GOOGLE_CLIENT_ID=your-google-client-id
    GOOGLE_CLIENT_SECRET=your-google-client-secret
    GOOGLE_REDIRECT_URI=http://localhost:8010/api/v1/auth/google/callback
    FRONTEND_IDENTITY_FORM_URL=http://localhost:3000/identity_form
    FRONTEND_LOGIN_SUCCESS_URL=http://localhost:3000
    SECRET_KEY=your_super_secret_random_string_for_jwt
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=1440 # 1 hari

    # Token internal untuk komunikasi aman antara bot dan backend
    INTERNAL_BOT_TOKEN=another_super_secret_string

    # Nonaktifkan telemetri ChromaDB
    ANONYMIZED_TELEMETRY=false
    ```

## 💻 Menjalankan Aplikasi

### Mode Development (Lokal)
1.  **Jalankan Backend & Bot**: Buka terminal, aktifkan *virtual environment*, dan jalankan `main.py`.
    ```bash
    python main.py
    ```
    Perintah ini akan menjalankan server API FastAPI di `http://localhost:8010` dan bot Telegram secara bersamaan.

2.  **Jalankan Frontend**: Buka terminal **kedua**, masuk ke direktori `static/`, dan jalankan server web sederhana.
    ```bash
    cd static
    python -m http.server 3000
    ```
3.  **Akses Aplikasi**:
    - **Web**: Buka browser dan kunjungi `http://localhost:3000`.
    - **Telegram**: Cari bot Anda di aplikasi Telegram dan mulai percakapan.

### Mode Produksi (Docker)
1.  **Deploy Frontend**: Deploy konten dari folder `static/` ke layanan hosting statis seperti Vercel, Netlify, atau GitHub Pages.

2.  **Deploy Backend**:
    - Salin seluruh kode proyek (kecuali folder `static/`) ke server/VPS Anda.
    - Pastikan Docker dan Docker Compose terinstal di server.
    - Buat file `.env` di server dengan kredensial produksi.
    - (Opsional) Ubah `nginx/nginx.conf` untuk menyesuaikan dengan nama domain Anda.
    - Jalankan Docker Compose dari direktori root proyek:
      ```bash
      docker-compose up --build -d # Opsi --build untuk membangun image baru, -d untuk detached mode
      ```
    Perintah ini akan membangun image, lalu menjalankan container untuk aplikasi utama (backend + bot) dan Nginx sebagai *reverse proxy*.

## 📚 Dokumentasi API

Dokumentasi lengkap untuk setiap endpoint API tersedia di file `backend/README.md`.

Secara ringkas, API dikelompokkan menjadi:
- **`/api/v1/web-auth`**: Registrasi, login, dan manajemen autentikasi untuk antarmuka web.
- **`/api/v1/users`**: Pengelolaan profil pengguna, biodata, dan riwayat kuesioner.
- **`/api/v1/web-chat`**: Endpoint untuk interaksi chat dari antarmuka web.
- **`/api/v1/internal/chat`**: Endpoint internal yang aman untuk interaksi chat dari bot Telegram.
