# Contoh Request/Response API

## 📝 Endpoint: POST /api/v1/users/profile

### ✅ Request Body - Format JSON Valid

**Endpoint**: `POST /api/v1/users/profile`

**Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "Content-Type": "application/json"
}
```

### Contoh 1: Perempuan yang Hamil

```json
{
  "inisial": "SB",
  "no_wa": "081234567890",
  "usia": 28,
  "jenis_kelamin": "Perempuan",
  "pendidikan": "Ners",
  "lama_bekerja": 5,
  "status_pegawai": "ASN",
  "jabatan": "Perawat Pelaksana",
  "jabatan_lain": null,
  "unit_ruangan": "Ruang ICU",
  "status_perkawinan": "Menikah",
  "status_kehamilan": "Ya",
  "jumlah_anak": 1
}
```

**Response 201 Created**:
```json
{
  "message": "Profile saved successfully"
}
```

---

### Contoh 2: Laki-laki (status_kehamilan otomatis "Tidak")

```json
{
  "inisial": "AW",
  "no_wa": "082345678901",
  "usia": 35,
  "jenis_kelamin": "Laki-laki",
  "pendidikan": "D3 Keperawatan",
  "lama_bekerja": 8,
  "status_pegawai": "Non ASN",
  "jabatan": "Kepala Ruangan",
  "jabatan_lain": null,
  "unit_ruangan": "Ruang Bedah",
  "status_perkawinan": "Menikah",
  "status_kehamilan": "Tidak",
  "jumlah_anak": 2
}
```

**Response 201 Created**:
```json
{
  "message": "Profile saved successfully"
}
```

---

### Contoh 3: Dengan Jabatan "Yang lain"

```json
{
  "inisial": "RJ",
  "no_wa": "+628123456789",
  "usia": 42,
  "jenis_kelamin": "Perempuan",
  "pendidikan": "Magister Keperawatan",
  "lama_bekerja": 12,
  "status_pegawai": "Yang lain",
  "jabatan": "Yang lain",
  "jabatan_lain": "Supervisor Khusus",
  "unit_ruangan": "Unit Manajemen",
  "status_perkawinan": "Cerai Hidup",
  "status_kehamilan": "Tidak",
  "jumlah_anak": 3
}
```

---

## ⚠️ Error 422: Validation Error

### Penyebab Error 422

Error 422 terjadi ketika data tidak sesuai dengan schema Pydantic. Berikut adalah **hal-hal yang TIDAK boleh dilakukan**:

#### ❌ Contoh Error: Usia bukan integer

```json
{
  "inisial": "AB",
  "no_wa": "081234567890",
  "usia": "30",  // ❌ SALAH: String, harus number
  "jenis_kelamin": "Laki-laki",
  "pendidikan": "Ners",
  "lama_bekerja": 5,
  "status_pegawai": "ASN",
  "jabatan": "Perawat Pelaksana",
  "jabatan_lain": null,
  "unit_ruangan": "Ruang ICU",
  "status_perkawinan": "Belum Menikah",
  "status_kehamilan": "Tidak",
  "jumlah_anak": 0
}
```

**Response 422**:
```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["body", "usia"],
      "msg": "Input should be a valid integer",
      "input": "30"
    }
  ]
}
```

---

#### ❌ Contoh Error: Nomor WhatsApp format salah

```json
{
  "no_wa": "123456789",  // ❌ SALAH: Harus dimulai 08 atau +628
  // ... field lainnya ...
}
```

**Response 400** (dari backend validation):
```json
{
  "detail": "Format nomor WhatsApp tidak valid. Contoh: 081234567890 atau +6281234567890."
}
```

---

#### ❌ Contoh Error: lama_bekerja bukan integer

```json
{
  "lama_bekerja": "5 tahun",  // ❌ SALAH: Harus number
  // ... field lainnya ...
}
```

**Response 422**:
```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["body", "lama_bekerja"],
      "msg": "Input should be a valid integer",
      "input": "5 tahun"
    }
  ]
}
```

---

#### ❌ Contoh Error: jumlah_anak bukan integer

```json
{
  "jumlah_anak": "2",  // ❌ SALAH: Harus number
  // ... field lainnya ...
}
```

---

## ✅ Validasi Yang Benar

### Tipe Data untuk Setiap Field

| Field | Tipe | Contoh | Catatan |
|-------|------|--------|---------|
| `inisial` | string | `"SB"` | Singkatan nama (2-3 karakter) |
| `no_wa` | string | `"081234567890"` | Format: 08, 628, atau +628 + 8-15 digit |
| `usia` | **integer** | `28` | Bukan string! Range: 18-65 |
| `jenis_kelamin` | string | `"Perempuan"` atau `"Laki-laki"` | Pilihan: Perempuan, Laki-laki |
| `pendidikan` | string | `"Ners"` | Pilihan: D3 Keperawatan, Ners, Magister Keperawatan, Ners Spesialis |
| `lama_bekerja` | **integer** | `5` | Bukan string! (dalam tahun) |
| `status_pegawai` | string | `"ASN"` | Pilihan: ASN, Non ASN, Yang lain |
| `jabatan` | string | `"Perawat Pelaksana"` | Lihat BIODATA_OPTIONS |
| `jabatan_lain` | string atau null | `"Supervisor"` atau `null` | Hanya isi jika jabatan="Yang lain" |
| `unit_ruangan` | string | `"Ruang ICU"` | Text bebas |
| `status_perkawinan` | string | `"Menikah"` | Pilihan: Belum Menikah, Menikah, Cerai Mati, Cerai Hidup |
| `status_kehamilan` | string | `"Ya"` atau `"Tidak"` | Pilihan: Ya, Tidak (auto-set "Tidak" untuk laki-laki) |
| `jumlah_anak` | **integer** | `2` | Bukan string! Range: 0+ |
| `email` | string atau null | `"user@email.com"` | Optional, auto-filled by backend |

---

## 🔄 Response Endpoint GET /api/v1/users/profile/full

**Response 200 OK**:
```json
{
  "biodata": {
    "inisial": "SB",
    "no_wa": "081234567890",
    "usia": 28,
    "jenis_kelamin": "Perempuan",
    "pendidikan": "Ners",
    "lama_bekerja": 5,
    "status_pegawai": "ASN",
    "jabatan": "Perawat Pelaksana",
    "jabatan_lain": null,
    "unit_ruangan": "Ruang ICU",
    "status_perkawinan": "Menikah",
    "status_kehamilan": "Ya",
    "jumlah_anak": 1,
    "email": "siti.budi@email.com"
  },
  "health_results": [
    {
      "id": 1,
      "user_id": 5,
      "who5_total": 20,
      "gad7_total": 8,
      "mbi_emosional_total": 18,
      "mbi_sinis_total": 6,
      "mbi_pencapaian_total": 35,
      "naqr_pribadi_total": 15,
      "naqr_pekerjaan_total": 10,
      "naqr_intimidasi_total": 5,
      "k10_total": 25,
      "created_at": "2025-11-13T10:30:00",
      "who5_category": "Tidak ada gejala Depresi",
      "gad7_category": "Kecemasan Ringan",
      "k10_category": "Distres sedang",
      "mbi_emosional_category": "Kelelahan Emosional Sedang",
      "mbi_sinis_category": "Sikap Sinis Rendah",
      "mbi_pencapaian_category": "Pencapaian Pribadi Tinggi",
      "mbi_total": 59,
      "naqr_total": 30,
      "naqr_category": "Perundungan Rendah / Tidak ada"
    }
  ],
  "biodata_completed": true,
  "health_results_completed": true
}
```

---

## 💡 Tips untuk Frontend Developer

### 1. Konversi Tipe Data Dengan Benar
```javascript
// ✅ BENAR
const payload = {
  inisial: "SB",
  no_wa: "081234567890",
  usia: parseInt(formData.usia),  // Convert string → integer
  jenis_kelamin: "Perempuan",
  pendidikan: "Ners",
  lama_bekerja: parseInt(formData.lama_bekerja),  // Convert string → integer
  status_pegawai: "ASN",
  jabatan: "Perawat Pelaksana",
  jabatan_lain: null,
  unit_ruangan: "Ruang ICU",
  status_perkawinan: "Menikah",
  status_kehamilan: "Ya",
  jumlah_anak: parseInt(formData.jumlah_anak)  // Convert string → integer
};

// ❌ SALAH - akan error 422
const wrong = {
  usia: "28",  // String, bukan number!
  lama_bekerja: "5",  // String, bukan number!
  jumlah_anak: "0"  // String, bukan number!
};
```

### 2. Handle Error 422 dengan Menampilkan Detail Error
```javascript
fetch('/api/v1/users/profile', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify(payload)
})
.then(res => {
  if (res.status === 422) {
    return res.json().then(err => {
      console.error("Validation Error:", err.detail);
      // Tampilkan ke user: "Field XYZ tidak valid: ..."
      throw new Error(err.detail[0].msg);
    });
  }
  if (res.status === 400) {
    return res.json().then(err => {
      console.error("Bad Request:", err.detail);
      // Tampilkan ke user: err.detail
      throw new Error(err.detail);
    });
  }
  return res.json();
})
.then(data => console.log("Success:", data))
.catch(err => console.error("Error:", err.message));
```

### 3. Validasi Nomor WhatsApp Sebelum Send
```javascript
function validatePhoneNumber(phoneNumber) {
  // Pattern: 08/628/+628 + 8-15 digits
  const pattern = /^(08|\+628|628)\d{8,15}$/;
  return pattern.test(phoneNumber.replace(/[-\s]/g, ''));
}

// Test
console.log(validatePhoneNumber("081234567890"));  // true
console.log(validatePhoneNumber("082345678901"));  // true
console.log(validatePhoneNumber("+6281234567890"));  // true
console.log(validatePhoneNumber("6281234567890"));  // true (628 prefix)
console.log(validatePhoneNumber("123456789"));  // false
```

### 4. Auto-Correct untuk Laki-laki
```javascript
// Jika user memilih laki-laki, auto-set status_kehamilan = "Tidak"
if (formData.jenis_kelamin === "Laki-laki") {
  formData.status_kehamilan = "Tidak";
  // Sembunyikan field status_kehamilan dari UI (optional)
}
```

---

## 🧪 Testing dengan cURL

```bash
# Test dengan data valid
curl -X POST "http://localhost:8000/api/v1/users/profile" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "inisial": "SB",
    "no_wa": "081234567890",
    "usia": 28,
    "jenis_kelamin": "Perempuan",
    "pendidikan": "Ners",
    "lama_bekerja": 5,
    "status_pegawai": "ASN",
    "jabatan": "Perawat Pelaksana",
    "jabatan_lain": null,
    "unit_ruangan": "Ruang ICU",
    "status_perkawinan": "Menikah",
    "status_kehamilan": "Ya",
    "jumlah_anak": 1
  }'
```

---

## 📋 Checklist Sebelum Submit

- [ ] `usia` adalah **integer** (bukan string)
- [ ] `lama_bekerja` adalah **integer** (bukan string)
- [ ] `jumlah_anak` adalah **integer** (bukan string)
- [ ] `no_wa` memiliki format: `08xxxxxxxxxx` atau `+628xxxxxxxxxx` atau `628xxxxxxxxxx`
- [ ] `usia` antara 18-65
- [ ] `jenis_kelamin` adalah `"Perempuan"` atau `"Laki-laki"`
- [ ] `status_kehamilan` adalah `"Ya"` atau `"Tidak"`
- [ ] Jika `jenis_kelamin` = "Laki-laki", maka `status_kehamilan` = "Tidak"
- [ ] Jika `jabatan` ≠ "Yang lain", maka `jabatan_lain` = `null` atau tidak dikirim

✅ Jika semua checklist tercapai, request seharusnya berhasil 201 Created!
