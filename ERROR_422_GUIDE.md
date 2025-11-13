# 🚨 Error 422 - Troubleshooting Guide

## Apa itu Error 422?

**Status Code 422: Unprocessable Entity** - Berarti data yang dikirim tidak sesuai dengan schema yang diharapkan oleh backend.

---

## 🎯 Penyebab Umum Error 422

### 1️⃣ **Tipe Data Salah (STRING vs INTEGER)**

**Masalah:**
- Field `usia`, `lama_bekerja`, `jumlah_anak` dikirim sebagai **string** padahal harus **number**

**Contoh Error:**
```json
{
  "usia": "28",  // ❌ String
  "lama_bekerja": "5",  // ❌ String
  "jumlah_anak": "2"  // ❌ String
}
```

**Response 422:**
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

**✅ SOLUSI:**
```json
{
  "usia": 28,  // ✅ Number (tanpa quotes)
  "lama_bekerja": 5,  // ✅ Number (tanpa quotes)
  "jumlah_anak": 2  // ✅ Number (tanpa quotes)
}
```

**JavaScript:**
```javascript
const payload = {
  usia: parseInt(formData.usia, 10),  // Konversi string ke number
  lama_bekerja: parseInt(formData.lama_bekerja, 10),
  jumlah_anak: parseInt(formData.jumlah_anak, 10)
};
```

---

### 2️⃣ **Field Wajib Kosong atau Null**

**Masalah:**
- Field yang wajib diisi dikirim sebagai `null`, `undefined`, atau string kosong

**Contoh Error:**
```json
{
  "inisial": "",  // ❌ Kosong
  "no_wa": null,  // ❌ Null
  "unit_ruangan": undefined  // ❌ Undefined
}
```

**Response 422:**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "inisial"],
      "msg": "Field required"
    }
  ]
}
```

**✅ SOLUSI:**
- Pastikan semua field wajib terisi sebelum submit
- Gunakan validasi client-side untuk mencegah submission kosong

```javascript
function validateForm(data) {
  const requiredFields = [
    'inisial', 'no_wa', 'usia', 'jenis_kelamin',
    'pendidikan', 'lama_bekerja', 'status_pegawai',
    'jabatan', 'unit_ruangan', 'status_perkawinan',
    'status_kehamilan', 'jumlah_anak'
  ];

  for (const field of requiredFields) {
    if (!data[field] || data[field] === '') {
      throw new Error(`${field} harus diisi!`);
    }
  }
}
```

---

### 3️⃣ **Email Format Salah**

**Masalah:**
- Field `email` dikirim dengan format yang tidak valid

**Contoh Error:**
```json
{
  "email": "invalid-email"  // ❌ Tidak ada @
}
```

**Response 422:**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "value is not a valid email address"
    }
  ]
}
```

**✅ SOLUSI:**
```json
{
  "email": "user@example.com"  // ✅ Format email valid
}
```

**JavaScript:**
```javascript
function isValidEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}
```

---

### 4️⃣ **Field Extra / Unknown**

**Masalah:**
- Mengirim field yang tidak didefinisikan di schema

**Contoh Error:**
```json
{
  "inisial": "SB",
  "no_wa": "081234567890",
  "age_group": "25-35",  // ❌ Field tidak didefinisikan!
  // ... field lainnya ...
}
```

**Response 422:**
```json
{
  "detail": [
    {
      "type": "extra_forbidden",
      "loc": ["body", "age_group"],
      "msg": "Extra inputs are not permitted"
    }
  ]
}
```

**✅ SOLUSI:**
- Hanya kirim field yang didefinisikan di schema
- Hapus field yang tidak perlu

---

## 📋 Tipe Data & Format yang Benar

| Field | Tipe | Format | Contoh |
|-------|------|--------|--------|
| `inisial` | string | Text | `"SB"` |
| `no_wa` | string | 08/+628/628 + 8-15 digit | `"081234567890"` |
| `usia` | **integer** | 18-65 | `28` |
| `jenis_kelamin` | string | Pilihan | `"Perempuan"` |
| `pendidikan` | string | Pilihan | `"Ners"` |
| `lama_bekerja` | **integer** | Tahun | `5` |
| `status_pegawai` | string | Pilihan | `"ASN"` |
| `jabatan` | string | Pilihan | `"Perawat Pelaksana"` |
| `jabatan_lain` | string / null | Text atau null | `"Supervisor"` atau `null` |
| `unit_ruangan` | string | Text | `"Ruang ICU"` |
| `status_perkawinan` | string | Pilihan | `"Menikah"` |
| `status_kehamilan` | string | Ya / Tidak | `"Tidak"` |
| `jumlah_anak` | **integer** | 0+ | `2` |
| `email` | string / null | Email valid | `"user@email.com"` atau `null` |

---

## 🔧 Testing dengan cURL

### ✅ Request Valid

```bash
curl -X POST "http://localhost:8000/api/v1/users/profile" \
  -H "Authorization: Bearer YOUR_TOKEN" \
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

**Response 201:**
```json
{
  "message": "Profile saved successfully"
}
```

### ❌ Request Invalid (Error 422)

```bash
curl -X POST "http://localhost:8000/api/v1/users/profile" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "inisial": "SB",
    "no_wa": "081234567890",
    "usia": "28",
    "jenis_kelamin": "Perempuan",
    "pendidikan": "Ners",
    "lama_bekerja": "5",
    "status_pegawai": "ASN",
    "jabatan": "Perawat Pelaksana",
    "jabatan_lain": null,
    "unit_ruangan": "Ruang ICU",
    "status_perkawinan": "Menikah",
    "status_kehamilan": "Ya",
    "jumlah_anak": "1"
  }'
```

**Response 422:**
```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["body", "usia"],
      "msg": "Input should be a valid integer",
      "input": "28"
    }
  ]
}
```

---

## 📊 Error Response Structure

```json
{
  "detail": [
    {
      "type": "error_type",           // int_parsing, value_error, extra_forbidden, etc
      "loc": ["body", "field_name"],  // Lokasi error
      "msg": "Error message",          // Pesan error
      "input": "value"                 // Nilai yang error
    }
  ]
}
```

### Common Error Types:

| Type | Artinya |
|------|---------|
| `int_parsing` | Field seharusnya integer, tapi dikirim string/non-integer |
| `string_type` | Field seharusnya string, tapi dikirim tipe lain |
| `value_error` | Nilai tidak sesuai dengan constraint (misal: email format) |
| `extra_forbidden` | Ada field yang tidak didefinisikan di schema |
| `missing` | Field wajib tidak ada di request |

---

## ✅ Checklist Sebelum Debug

- [ ] Pastikan semua field bernama **sama persis** dengan dokumentasi
- [ ] Pastikan `usia`, `lama_bekerja`, `jumlah_anak` adalah **number** bukan string
- [ ] Pastikan tidak ada field **extra** yang tidak didefinisikan
- [ ] Pastikan `email` (jika diisi) format valid: `user@example.com`
- [ ] Pastikan semua field wajib **tidak kosong**
- [ ] Periksa JSON syntax (gunakan JSON validator online)
- [ ] Pastikan **Authorization header** ada dan valid
- [ ] Pastikan **Content-Type** = `application/json`

---

## 🆘 Masih Error?

1. **Copy-paste response error 422** dan lihat `loc` field untuk tahu field mana yang error
2. **Lihat tabel di atas** untuk memastikan tipe data benar
3. **Validasi JSON** di https://jsonlint.com/
4. **Test dengan cURL** untuk isolir masalah (frontend vs backend)
5. **Lihat file `JSON_REQUEST_EXAMPLES.md`** untuk contoh yang sudah terbukti valid

---

## 📞 Debugging Steps

### Step 1: Log Request Payload
```javascript
console.log("Request payload:", JSON.stringify(payload, null, 2));
```

### Step 2: Validate Data Types
```javascript
console.log("usia type:", typeof payload.usia); // should be "number"
console.log("lama_bekerja type:", typeof payload.lama_bekerja); // should be "number"
console.log("jumlah_anak type:", typeof payload.jumlah_anak); // should be "number"
```

### Step 3: Check Response Details
```javascript
.catch(error => {
  if (error.response?.status === 422) {
    console.error("Validation errors:", error.response.data.detail);
    error.response.data.detail.forEach(err => {
      console.log(`Field: ${err.loc[1]}, Error: ${err.msg}, Got: ${err.input}`);
    });
  }
});
```

---

## 💡 Pro Tips

1. **Gunakan TypeScript** untuk type safety
   ```typescript
   interface UserProfile {
     inisial: string;
     no_wa: string;
     usia: number;  // Type-safe: number, bukan string
     // ...
   }
   ```

2. **Validasi Client-Side** sebelum submit
   ```javascript
   if (typeof payload.usia !== 'number') {
     throw new Error('Usia harus number!');
   }
   ```

3. **Gunakan Form Library** seperti React Hook Form
   ```javascript
   const { register, handleSubmit } = useForm();
   // Otomatis handle conversion & validation
   ```

