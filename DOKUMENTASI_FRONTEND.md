# 📚 Dokumentasi untuk Frontend Developer

## 📂 File-File Dokumentasi yang Telah Dibuat

Saya telah membuat 3 file dokumentasi lengkap untuk membantu frontend developer mengatasi error 422 dan memahami format request yang benar:

### 1️⃣ **API_EXAMPLES.md** 
   - 📍 Lokasi: `/API_EXAMPLES.md`
   - 📝 Isi:
     - Contoh request/response lengkap dengan berbagai skenario
     - Penjelasan detail setiap field (tipe data, constraints)
     - Error handling dengan JavaScript/Fetch
     - Validasi client-side untuk nomor WhatsApp
     - Tips untuk frontend developer (TypeScript, validation, form library)
     - Testing dengan cURL

### 2️⃣ **JSON_REQUEST_EXAMPLES.md** 
   - 📍 Lokasi: `/JSON_REQUEST_EXAMPLES.md`
   - 📝 Isi:
     - **4 Contoh Request VALID** yang sudah terbukti berhasil:
       1. Perempuan hamil
       2. Laki-laki (auto status_kehamilan = "Tidak")
       3. Perempuan tidak hamil
       4. Dengan jabatan "Yang lain"
     - **5 Contoh Request INVALID** dengan penjelasan error:
       1. Usia sebagai string (SALAH)
       2. lama_bekerja sebagai string (SALAH)
       3. jumlah_anak sebagai string (SALAH)
       4. No WhatsApp format salah (SALAH)
       5. Status kehamilan untuk laki-laki (SALAH)
     - Tabel pilihan nilai valid untuk setiap dropdown
     - Contoh code JavaScript untuk handle conversion & error
     - Checklist sebelum submit

### 3️⃣ **ERROR_422_GUIDE.md** 
   - 📍 Lokasi: `/ERROR_422_GUIDE.md`
   - 📝 Isi:
     - Penjelasan apa itu error 422
     - **4 Penyebab Umum Error 422** dengan contoh & solusi:
       1. Tipe data salah (string vs integer)
       2. Field wajib kosong
       3. Email format salah
       4. Field extra / unknown
     - Response structure dari Pydantic error
     - Testing dengan cURL
     - Debugging steps lengkap
     - Pro tips (TypeScript, validation, form library)

---

## 🎯 Ringkasan Masalah & Solusi

### ❌ **Masalah 1: Error 422 [object Object]**

**Root Cause:**
- Frontend mengirim `usia`, `lama_bekerja`, `jumlah_anak` sebagai **STRING** padahal backend expect **INTEGER**
- Error [object Object] adalah bentuk error object yang tidak ter-stringify dengan baik

**✅ Solusi:**
- Konversi ke integer: `parseInt(value, 10)`
- Lihat contoh di `JSON_REQUEST_EXAMPLES.md`

---

### ❌ **Masalah 2: Edit Profile Laki-laki Masih Bisa Ubah Status Kehamilan**

**Root Cause:**
- Endpoint `POST /api/v1/users/profile` tidak melakukan validasi

**✅ Solusi yang Sudah Diterapkan:**
1. **Pydantic Validator** di schema `UserProfile`:
   - Auto-correct: jika laki-laki & user kirim "Ya" → set ke "Tidak"
   
2. **Backend Validation** di endpoint:
   - Panggil `profiling_service.validate_biodata()`
   - Set status_kehamilan = "Tidak" untuk laki-laki
   
3. **Serialization Fix**:
   - Convert `DictRow` → `dict` untuk mencegah `[object Object]`

---

## 📊 Data Type Mapping

| Field | Type | Contoh | ✅ Benar | ❌ Salah |
|-------|------|--------|---------|---------|
| usia | integer | 28 | `28` | `"28"` |
| lama_bekerja | integer | 5 | `5` | `"5"` |
| jumlah_anak | integer | 2 | `2` | `"2"` |
| inisial | string | SB | `"SB"` | `SB` (tanpa quotes) |
| no_wa | string | 081234567890 | `"081234567890"` | `081234567890` |

---

## 🚀 Quick Start untuk Frontend

### Step 1: Baca Dokumentasi
```
1. JSON_REQUEST_EXAMPLES.md ← Lihat contoh request yang valid
2. ERROR_422_GUIDE.md ← Pahami error 422 & cara fix
3. API_EXAMPLES.md ← Implementasi lengkap di JavaScript
```

### Step 2: Copy Contoh Valid
```javascript
const payload = {
  inisial: "SB",
  no_wa: "081234567890",
  usia: 28,  // ← NUMBER, bukan string!
  jenis_kelamin: "Perempuan",
  pendidikan: "Ners",
  lama_bekerja: 5,  // ← NUMBER, bukan string!
  status_pegawai: "ASN",
  jabatan: "Perawat Pelaksana",
  jabatan_lain: null,
  unit_ruangan: "Ruang ICU",
  status_perkawinan: "Menikah",
  status_kehamilan: "Ya",
  jumlah_anak: 1  // ← NUMBER, bukan string!
};
```

### Step 3: Convert String Input
```javascript
// Form input selalu string, convert ke number
const formData = {
  usia: parseInt(event.target.usia.value, 10),
  lama_bekerja: parseInt(event.target.lama_bekerja.value, 10),
  jumlah_anak: parseInt(event.target.jumlah_anak.value, 10)
};
```

### Step 4: Auto-Fix untuk Laki-laki
```javascript
// Jika laki-laki, auto set status_kehamilan = "Tidak"
if (formData.jenis_kelamin === "Laki-laki") {
  formData.status_kehamilan = "Tidak";
}
```

### Step 5: Handle Error 422
```javascript
if (response.status === 422) {
  const error = await response.json();
  const field = error.detail[0].loc[1];
  const message = error.detail[0].msg;
  console.error(`Error di field ${field}: ${message}`);
}
```

---

## 📋 Checklist Sebelum Request

- [ ] Semua field string sudah **tidak punya quotes** di JSON
- [ ] Field `usia`, `lama_bekerja`, `jumlah_anak` adalah **number** (bukan string)
- [ ] Field `no_wa` format: `08...`, `+628...`, atau `628...`
- [ ] Jika `jenis_kelamin` = "Laki-laki" → `status_kehamilan` = "Tidak"
- [ ] Jika `jabatan` ≠ "Yang lain" → `jabatan_lain` = `null`
- [ ] JSON syntax valid (test di https://jsonlint.com/)
- [ ] Authorization header ada
- [ ] Content-Type = `application/json`

✅ **Jika semua checklist done, request akan 201 Created!**

---

## 🔗 File Reference

| File | Purpose | Untuk Siapa |
|------|---------|------------|
| `JSON_REQUEST_EXAMPLES.md` | Contoh request/response valid & invalid | Frontend Dev (copy-paste ready) |
| `ERROR_422_GUIDE.md` | Troubleshooting error 422 | Frontend Dev (debugging) |
| `API_EXAMPLES.md` | Dokumentasi lengkap API | Frontend Dev (comprehensive) |
| `backend/api/v1/routes/users.py` | Backend endpoint implementasi | Backend Dev |
| `backend/api/v1/schemas/user.py` | Pydantic schema dengan validator | Backend Dev |
| `core/services/profiling_service.py` | Business logic validation | Backend Dev |

---

## 💬 TL;DR

**Error 422?** 
→ Lihat `JSON_REQUEST_EXAMPLES.md`, cari "❌ ERROR", ikuti "🔧 FIX" bagian

**Mau contoh request yang valid?**
→ Copy dari "✅ Contoh X: ..." di `JSON_REQUEST_EXAMPLES.md`

**Mau implementasi JavaScript lengkap?**
→ Lihat `API_EXAMPLES.md`, bagian "JavaScript/TypeScript Example"

**Bingung field apa aja?**
→ Lihat tabel di `JSON_REQUEST_EXAMPLES.md`, bagian "📊 Pilihan Nilai Valid"

---

**✨ Semua file sudah siap dipelajari dan di-implement oleh frontend team!**
