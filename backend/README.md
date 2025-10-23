# Dokumentasi API - Asisten Kesejahteraan Diri

Selamat datang di dokumentasi API untuk backend Asisten Kesejahteraan Diri. API ini dirancang untuk melayani antarmuka web dan bot Telegram.

**Base URL:** `http://your-host:8000`

---

## Daftar Endpoint

Berikut adalah daftar lengkap endpoint yang tersedia di API ini, dikelompokkan berdasarkan fungsionalitasnya.

### 1. Umum
-   **`GET /api`**
    -   **Kegunaan:** Endpoint selamat datang untuk memastikan API berjalan.
-   **`GET /health`**
    -   **Kegunaan:** Endpoint *health check* untuk memonitor status API.

### 2. Autentikasi (`/api/v1/auth`)
Endpoint ini menangani semua alur yang terkait dengan autentikasi pengguna.

-   **`POST /api/v1/auth/register`**
    -   **Kegunaan:** Mendaftarkan akun pengguna baru melalui antarmuka web.
-   **`POST /api/v1/auth/login`**
    -   **Kegunaan:** Mengautentikasi pengguna web dan mengembalikan token akses JWT.
-   **`POST /api/v1/auth/set-password`**
    -   **Kegunaan:** Endpoint khusus bagi pengguna yang mendaftar via Telegram untuk mengatur password mereka pertama kali.

### 3. Pengguna & Profil (`/api/v1/users`)
Mengelola data pengguna, profil (biodata), dan hasil kuesioner. Semua endpoint di sini **membutuhkan otentikasi** (Header `Authorization: Bearer <token>`).

-   **`GET /api/v1/users/me`**
    -   **Kegunaan:** Mendapatkan informasi dasar (ID dan email) dari pengguna yang sedang login.
-   **`GET /api/v1/users/profile/status`**
    -   **Kegunaan:** Memeriksa apakah pengguna sudah melengkapi data identitasnya.
-   **`GET /api/v1/users/profile/full`**
    -   **Kegunaan:** Mendapatkan profil lengkap pengguna, termasuk biodata dan semua riwayat hasil kuesioner.
-   **`POST /api/v1/users/profile`**
    -   **Kegunaan:** Membuat atau memperbarui profil identitas (biodata) pengguna.
-   **`GET /api/v1/users/questionnaire/{q_type}`**
    -   **Kegunaan:** Mendapatkan daftar pertanyaan dan opsi jawaban untuk tipe kuesioner tertentu (`who5`, `gad7`, `mbi`, `naqr`, `k10`).
-   **`POST /api/v1/users/profile/results`**
    -   **Kegunaan:** Mengirimkan hasil kuesioner yang telah diisi, menyimpannya ke database, dan mengembalikan ringkasan.
-   **`DELETE /api/v1/users/profile/results/{result_id}`**
    -   **Kegunaan:** Menghapus riwayat hasil kuesioner tertentu milik pengguna.

### 4. Chat
Endpoint untuk interaksi dengan chatbot.

-   **`POST /api/v1/chat`**
    -   **Kegunaan:** Mengirim pesan dari **antarmuka web** ke chatbot. Endpoint ini aman dan memerlukan token otentikasi JWT.
-   **`POST /api/v1/internal/chat`**
    -   **Kegunaan:** Mengirim pesan dari **bot Telegram** ke chatbot. Endpoint ini adalah untuk komunikasi internal dan dilindungi oleh *secret header* (`X-Internal-Token`).