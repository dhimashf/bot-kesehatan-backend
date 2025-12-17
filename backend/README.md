# Dokumentasi API - Asisten Kesejahteraan Diri

Selamat datang di dokumentasi API untuk backend Asisten Kesejahteraan Diri. API ini dirancang untuk melayani antarmuka web dan bot Telegram.

**Base URL:** `http://your-host:8010`

---

## Daftar Endpoint

Berikut adalah daftar lengkap endpoint yang tersedia di API ini, dikelompokkan berdasarkan fungsionalitasnya.

### 1. Umum
-   **`GET /api`**
    -   **Kegunaan:** Endpoint selamat datang untuk memastikan API berjalan.
    -   **Contoh Output (JSON):**
        ```json
        {
          "message": "Welcome to the Psiko API"
        }
        ```
-   **`GET /health`**
    -   **Kegunaan:** Endpoint *health check* untuk memonitor status API.
    -   **Contoh Output (JSON):**
        ```json
        {
          "status": "ok"
        }
        ```

### 2. Autentikasi Web (`/api/v1/web-auth`)
Endpoint ini menangani semua alur yang terkait dengan autentikasi pengguna dari antarmuka web.

-   **`POST /api/v1/web-auth/register`**
    -   **Kegunaan:** Mendaftarkan akun pengguna baru melalui antarmuka web.
    -   **Body (Form Data):** `username` (email) dan `password`.
    -   **Contoh Output (JSON):**
        ```json
        {
          "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "token_type": "bearer"
        }
        ```
-   **`POST /api/v1/web-auth/login`**
    -   **Kegunaan:** Mengautentikasi pengguna web dan mengembalikan token akses JWT.
    -   **Body (Form Data):** `username` (email) dan `password`.
    -   **Contoh Output (JSON):**
        ```json
        {
          "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "token_type": "bearer"
        }
        ```
-   **`POST /api/v1/web-auth/set-password`**
    -   **Kegunaan:** Endpoint khusus bagi pengguna yang mendaftar via Telegram untuk mengatur password mereka pertama kali.
    -   **Body (JSON):** `{"email": "user@example.com", "password": "new_secure_password"}`
    -   **Contoh Output (JSON):** `{"message": "Password has been set successfully. You can now log in."}`

### 3. Autentikasi Google (`/api/v1/auth/google`)
Endpoint ini menangani alur otentikasi menggunakan akun Google.

-   **`GET /api/v1/auth/google/login`**
    -   **Kegunaan:** Memulai alur login Google. Endpoint ini akan me-redirect pengguna ke halaman otentikasi Google.
    -   **Aksi:** Frontend harus mengarahkan pengguna ke URL ini.

-   **`GET /api/v1/auth/google/callback`**
    -   **Kegunaan:** Endpoint internal yang dipanggil oleh Google setelah pengguna berhasil login. Endpoint ini akan memproses login, membuat token JWT, dan me-redirect pengguna kembali ke frontend dengan token tersebut.
    -   **Aksi:** Tidak untuk dipanggil langsung oleh frontend.

-   **`GET /api/v1/auth/google/me`**
    -   **Kegunaan:** Sama seperti `/api/v1/users/me`, mendapatkan informasi pengguna yang sedang login. Endpoint ini berguna untuk memverifikasi token yang didapat dari alur Google Auth.
    -   **Otentikasi:** Membutuhkan Header `Authorization: Bearer <token>`.
    -   **Contoh Output (JSON):**
        ```json
        { "id": 1, "email": "user.google@example.com", "role": "user" }
        ```

-   **`POST /api/v1/auth/google/token-signin`**
    -   **Kegunaan:** Mengautentikasi pengguna dari klien mobile (seperti React Native) yang sudah mendapatkan `idToken` dari Google Sign-In.
    -   **Body (JSON):** `{"idToken": "id_token_yang_didapat_dari_google_signin"}`
    -   **Contoh Output (JSON):**
        ```json
        {
          "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "token_type": "bearer",
          "user": {
            "id": 1,
            "name": "Nama Pengguna",
            "email": "user@example.com",
            "photo": "https://url.to/photo.jpg",
            "role": "user"
          }
        }
        ```

### 4. Pengguna & Profil (`/api/v1/users`)
Mengelola data pengguna, profil (biodata), dan hasil kuesioner. Semua endpoint di sini **membutuhkan otentikasi** (Header `Authorization: Bearer <token>`).

-   **`GET /api/v1/users/me`**
    -   **Kegunaan:** Sama seperti `/api/v1/users/me`, mendapatkan informasi pengguna yang sedang login. Endpoint ini berguna untuk memverifikasi token yang didapat dari alur Google Auth.
    -   **Otentikasi:** Membutuhkan Header `Authorization: Bearer <token>`.
    -   **Contoh Output (JSON):**
        ```json
        { "id": 1, "email": "user.google@example.com", "role": "user" }
        ```

-   **`GET /api/v1/users/profile/status`**
    -   **Kegunaan:** Memeriksa apakah pengguna sudah melengkapi biodata dan kuesioner.
    -   **Contoh Output (JSON):**
        ```json
        {
          "biodata_completed": true,
          "health_results_completed": false
        }
        ```
-   **`GET /api/v1/users/profile/full`**
    -   **Kegunaan:** Mendapatkan profil lengkap pengguna, termasuk biodata dan semua riwayat hasil kuesioner.
    -   **Contoh Output (JSON):**
        ```json
        {
          "biodata": {
            "email": "user@example.com",
            "inisial": "DH",
            "no_wa": "081234567890",
            "usia": 30,
            "jenis_kelamin": "Laki-laki",
            "pendidikan": "Ners",
            "lama_bekerja": 5,
            "status_pegawai": "ASN",
            "jabatan": "Perawat Pelaksana",
            "jabatan_lain": null,
            "unit_ruangan": "IGD",
            "status_perkawinan": "Menikah",
            "status_kehamilan": "Tidak",
            "jumlah_anak": 1
          },
          "health_results": [
            {
              "id": 1,
              "user_id": 1,
              "who5_total": 20,
              "gad7_total": 5,
              "mbi_emosional_total": 15,
              "mbi_sinis_total": 8,
              "mbi_pencapaian_total": 12,
              "naqr_pribadi_total": 10,
              "naqr_pekerjaan_total": 12,
              "naqr_intimidasi_total": 5,
              "k10_total": 18,
              "naqr_bullying_experience": 2,
              "naqr_bullying_actors": "Rekan kerja",
              "naqr_bullying_perpetrators_detail": "1 laki-laki",
              "created_at": "2023-10-28T12:00:00",
              "who5_category": "Tidak ada gejala Depresi",
              "gad7_category": "Kecemasan Minimal",
              "k10_category": "Distres rendah",
              "mbi_emosional_category": "Sedang",
              "mbi_sinis_category": "Sedang",
              "mbi_pencapaian_category": "Tinggi",
              "mbi_total": 35,
              "naqr_total": 27
            }
          ],
          "biodata_completed": true,
          "health_results_completed": true
        }
        ```
-   **`POST /api/v1/users/profile`**
    -   **Kegunaan:** Membuat atau memperbarui profil identitas (biodata) pengguna.
    -   **Body (JSON):** Menggunakan struktur yang sama dengan objek `biodata` pada output `GET /api/v1/users/profile/full`.
    ```json
        {
          "email": "user@example.com",
          "inisial": "DH",
          "no_wa": "081234567890",
          "usia": 30,
          "jenis_kelamin": "Laki-laki",
          "pendidikan": "Ners",
          "lama_bekerja": 5,
          "status_pegawai": "ASN",
          "jabatan": "Perawat Pelaksana",
          "jabatan_lain": null,
          "unit_ruangan": "IGD",
          "status_perkawinan": "Menikah",
          "status_kehamilan": "Tidak",
          "jumlah_anak": 1
        }

    -   **Contoh Output (JSON):** `{"message": "Profile saved successfully"}`

-   **`GET /api/v1/users/questionnaire/{q_type}`**
    -   **Kegunaan:** Mendapatkan daftar pertanyaan dan opsi jawaban untuk tipe kuesioner tertentu (`who5`, `gad7`, `mbi`, `naqr`, `k10`).
    -   **Catatan:** Endpoint ini juga mendukung `q_type=naqr_perundungan` dengan format output yang berbeda (lihat contoh kedua).
    -   **Contoh Output (JSON) untuk `q_type=who5`:**
        ```json
        {
          "type": "who5",
          "questions": [
            { "text": "14. Saya merasa ceria dan bersemangat" },
            { "text": "15. Saya merasa tenang dan rileks" }
          ],
          "options": [
            { "text": "Setiap Saat", "score": 5 },
            { "text": "Sering Sekali", "score": 4 }
          ]
        }
        ```
    -   **Contoh Output (JSON) untuk `q_type=naqr_perundungan`:**
        ```json
        {
          "type": "naqr_perundungan",
          "questions": [
            { "id": "q80", "type": "multiple_choice", "text": "Apakah Anda pernah mengalami perundungan di tempat kerja?", "options": [...] },
            { "id": "q81", "type": "text_input", "text": "Siapa saja yang melakukan perundungan tersebut?" },
            { "id": "q82", "type": "text_input", "text": "Jelaskan lebih detail mengenai pelaku perundungan." }
          ]
        }
        ```
-   **`POST /api/v1/users/profile/results`**
    -   **Kegunaan:** Mengirimkan hasil kuesioner yang telah diisi dari antarmuka web, menyimpannya ke database, dan mengembalikan ringkasan.
    -   **Body (JSON):**
        ```json
        {
          "who5_total": 15,
          "gad7_total": 8,
          "k10_total": 25,
          "mbi_scores": [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2],
          "naqr_scores": [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2],
          "naqr_bullying_experience": 2,
          "naqr_bullying_actors": "Rekan kerja",
          "naqr_bullying_perpetrators_detail": "1 laki-laki"
        }
        ```
    -   **Contoh Output (JSON):**
        ```json
        {
          "message": "Results saved successfully",
          "summary": {
            "WHO-5": { "score": 15, "interpretation": "Tidak ada gejala Depresi" },
            "GAD-7": { "score": 8, "interpretation": "Kecemasan Ringan" },
            "MBI-EE": { "score": 25, "interpretation": "Tinggi" },
            "MBI-CYN": { "score": 10, "interpretation": "Tinggi" },
            "MBI-PA": { "score": 10, "interpretation": "Rendah" },
            "NAQ-R Total": { "score": 44, "interpretation": "Perundungan Sedang" },
            "K-10": { "score": 25, "interpretation": "Distres tinggi" },
            "Detail Pengalaman Perundungan": {
              "Pengalaman": "Ya, tapi jarang",
              "Pelaku": "Rekan kerja",
              "Detail Pelaku": "1 laki-laki"
            }
          }
        }
        ```
-   **`DELETE /api/v1/users/profile/results/{result_id}`**
    -   **Kegunaan:** Menghapus riwayat hasil kuesioner tertentu milik pengguna.
    -   **Contoh Output:** Status `204 No Content` jika berhasil.

### 4. Admin (`/api/v1/users/admin`)
Endpoint ini hanya dapat diakses oleh pengguna dengan peran `admin`.
-   **`GET /api/v1/users/admin/all-users`**
    -   **Kegunaan:** Mendapatkan daftar semua pengguna yang terdaftar di sistem.
    -   **Otentikasi:** Membutuhkan token admin.
    -   **Contoh Output (JSON):**
        ```json
        [
          {
            "id": 1,
            "email": "user1@example.com",
            "role": "user"
          },
          {
            "id": 2,
            "email": "admin@example.com",
            "role": "admin"
          }
        ]
        ```

-   **`GET /api/v1/users/admin/all-profiles`**
    -   **Kegunaan:** Mendapatkan semua data profil (biodata) dari seluruh pengguna.
    -   **Otentikasi:** Membutuhkan token admin.
    -   **Contoh Output (JSON):**
        ```json
        [
          {
            "user_id": 1,
            "email": "user1@example.com",
            "inisial": "U1",
            "usia": 28,
            "jenis_kelamin": "Perempuan",
            "pendidikan": "S1 Keperawatan"
          },
          {
            "user_id": 2,
            "email": "user2@example.com",
            "inisial": "U2",
            "usia": 35,
            "jenis_kelamin": "Laki-laki",
            "pendidikan": "Ners"
          }
        ]
        ```

-   **`GET /api/v1/users/admin/all-health-results`**
    -   **Kegunaan:** Mengambil seluruh riwayat hasil kuesioner dari semua pengguna.
    -   **Otentikasi:** Membutuhkan token admin.
    -   **Contoh Output (JSON):**
        ```json
        [
          {
            "id": 1,
            "user_id": 1,
            "who5_total": 18,
            "gad7_total": 7,
            "k10_total": 22,
            "created_at": "2023-10-01T10:00:00"
          },
          {
            "id": 2,
            "user_id": 2,
            "who5_total": 22,
            "gad7_total": 3,
            "k10_total": 15,
            "created_at": "2023-10-02T11:00:00"
          }
        ]
        ```

-   **`GET /api/v1/users/admin/all-results-with-biodata`**
    -   **Kegunaan:** Mengambil data gabungan dari semua pengguna, termasuk status kelengkapan profil, biodata, dan riwayat kuesioner. Sangat berguna untuk dashboard admin.
    -   **Otentikasi:** Membutuhkan token admin.
    -   **Contoh Output (JSON):**
        ```json
        [
          {
            "biodata_completed": true,
            "health_results_completed": true,
            "biodata": {
              "user_id": 1,
              "email": "user1@example.com",
              "role": "user",
              "inisial": "U1",
              "usia": 28,
              "jenis_kelamin": "Perempuan",
              "pendidikan": "S1 Keperawatan"
            },
            "health_results": [
              {
                "id": 101,
                "who5_total": 20,
                "gad7_total": 5,
                "k10_total": 18,
                "created_at": "2023-10-20T10:00:00"
              }
            ]
          },
          {
            "biodata_completed": true,
            "health_results_completed": false,
            "biodata": {
              "user_id": 2,
              "email": "user2@example.com",
              "role": "user",
              "inisial": "U2",
              "usia": 35,
              "jenis_kelamin": "Laki-laki",
              "pendidikan": "Ners"
            },
            "health_results": []
          }
        ]
        ```

-   **`GET /api/v1/users/admin/profile/{user_id}`**
    -   **Kegunaan:** Mendapatkan profil lengkap (biodata dan riwayat kuesioner) dari satu pengguna spesifik berdasarkan ID.
    -   **Otentikasi:** Membutuhkan token admin.
    -   **Contoh Output (JSON):**
        ```json
        {
          "biodata": {
            "email": "user1@example.com",
            "inisial": "U1",
            "usia": 28,
            "jenis_kelamin": "Perempuan"
          },
          "health_results": [
            { "id": 101, "who5_total": 20, "created_at": "2023-10-20T10:00:00" },
            { "id": 105, "who5_total": 22, "created_at": "2023-11-15T14:30:00" }
          ],
          "biodata_completed": true,
          "health_results_completed": true
        }
        ```

-   **`GET /api/v1/users/admin/health-results/{user_id}`**
    -   **Kegunaan:** Mendapatkan semua riwayat hasil kuesioner dari satu pengguna spesifik berdasarkan ID.
    -   **Otentikasi:** Membutuhkan token admin.
    -   **Contoh Output (JSON):**
        ```json
        [
          {
            "id": 1,
            "user_id": 1,
            "who5_total": 18,
            "gad7_total": 7,
            "k10_total": 22,
            "created_at": "2023-10-01T10:00:00"
          }
        ]
        ```
### 4. Chat
Endpoint untuk interaksi dengan chatbot.

-   **`POST /api/v1/web-chat`**
    -   **Kegunaan:** Mengirim pesan dari **antarmuka web** ke chatbot. Endpoint ini aman dan memerlukan token otentikasi JWT.
    -   **Body (JSON):** `{"message": "Halo, saya merasa cemas akhir-akhir ini."}`
    -   **Contoh Output (JSON):** `{"response": "Tentu, saya mengerti. Berdasarkan profil Anda..."}`
-   **`POST /api/v1/internal/chat`**
    -   **Kegunaan:** Mengirim pesan dari **bot Telegram** ke chatbot. Endpoint ini adalah untuk komunikasi internal dan dilindungi oleh *secret header* (`X-Internal-Token`).
    -   **Body (JSON):** `{"user_id": 1, "message": "Halo, saya merasa cemas akhir-akhir ini."}`
    -   **Contoh Output (JSON):** `{"response": "Tentu, saya mengerti. Berdasarkan profil Anda..."}`