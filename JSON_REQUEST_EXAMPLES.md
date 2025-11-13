# JSON Request Examples untuk Frontend

## 🎯 Request: POST /api/v1/users/profile

**Headers Wajib:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

## ✅ Contoh 1: Perempuan Hamil (VALID)

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

**✅ Response 201 Created:**
```json
{
  "message": "Profile saved successfully"
}
```

---

## ✅ Contoh 2: Laki-laki (Status Kehamilan AUTO = "Tidak") (VALID)

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

**✅ Response 201 Created:**
```json
{
  "message": "Profile saved successfully"
}
```

---

## ✅ Contoh 3: Perempuan Tidak Hamil (VALID)

```json
{
  "inisial": "RJ",
  "no_wa": "+628123456789",
  "usia": 42,
  "jenis_kelamin": "Perempuan",
  "pendidikan": "Magister Keperawatan",
  "lama_bekerja": 12,
  "status_pegawai": "ASN",
  "jabatan": "Penanggung Jawab Mutu",
  "jabatan_lain": null,
  "unit_ruangan": "Unit Manajemen",
  "status_perkawinan": "Cerai Hidup",
  "status_kehamilan": "Tidak",
  "jumlah_anak": 3
}
```

**✅ Response 201 Created:**
```json
{
  "message": "Profile saved successfully"
}
```

---

## ✅ Contoh 4: Dengan Jabatan "Yang lain" (VALID)

```json
{
  "inisial": "TD",
  "no_wa": "0812-3456-7890",
  "usia": 31,
  "jenis_kelamin": "Perempuan",
  "pendidikan": "Ners Spesialis",
  "lama_bekerja": 6,
  "status_pegawai": "Yang lain",
  "jabatan": "Yang lain",
  "jabatan_lain": "Supervisor Shift",
  "unit_ruangan": "Ruang Emergency",
  "status_perkawinan": "Belum Menikah",
  "status_kehamilan": "Tidak",
  "jumlah_anak": 0
}
```

**✅ Response 201 Created:**
```json
{
  "message": "Profile saved successfully"
}
```

---

## ❌ Contoh ERROR 422: Usia String (INVALID)

```json
{
  "inisial": "AB",
  "no_wa": "081234567890",
  "usia": "30",
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

**❌ Response 422 Unprocessable Entity:**
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

**🔧 FIX:** Ubah `"usia": "30"` → `"usia": 30` (tanpa quotes)

---

## ❌ Contoh ERROR 422: lama_bekerja String (INVALID)

```json
{
  "inisial": "CD",
  "no_wa": "081234567890",
  "usia": 28,
  "jenis_kelamin": "Perempuan",
  "pendidikan": "Ners",
  "lama_bekerja": "5",
  "status_pegawai": "ASN",
  "jabatan": "Perawat Pelaksana",
  "jabatan_lain": null,
  "unit_ruangan": "Ruang ICU",
  "status_perkawinan": "Menikah",
  "status_kehamilan": "Ya",
  "jumlah_anak": 1
}
```

**❌ Response 422 Unprocessable Entity:**
```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["body", "lama_bekerja"],
      "msg": "Input should be a valid integer",
      "input": "5"
    }
  ]
}
```

**🔧 FIX:** Ubah `"lama_bekerja": "5"` → `"lama_bekerja": 5` (tanpa quotes)

---

## ❌ Contoh ERROR 422: jumlah_anak String (INVALID)

```json
{
  "inisial": "EF",
  "no_wa": "081234567890",
  "usia": 30,
  "jenis_kelamin": "Perempuan",
  "pendidikan": "D3 Keperawatan",
  "lama_bekerja": 4,
  "status_pegawai": "Non ASN",
  "jabatan": "Perawat Pelaksana",
  "jabatan_lain": null,
  "unit_ruangan": "Ruang Rawat",
  "status_perkawinan": "Menikah",
  "status_kehamilan": "Tidak",
  "jumlah_anak": "2"
}
```

**❌ Response 422 Unprocessable Entity:**
```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["body", "jumlah_anak"],
      "msg": "Input should be a valid integer",
      "input": "2"
    }
  ]
}
```

**🔧 FIX:** Ubah `"jumlah_anak": "2"` → `"jumlah_anak": 2` (tanpa quotes)

---

## ❌ Contoh ERROR 400: Nomor WhatsApp Invalid (INVALID)

```json
{
  "inisial": "GH",
  "no_wa": "123456789",
  "usia": 26,
  "jenis_kelamin": "Perempuan",
  "pendidikan": "Ners",
  "lama_bekerja": 3,
  "status_pegawai": "ASN",
  "jabatan": "Perawat Pelaksana",
  "jabatan_lain": null,
  "unit_ruangan": "Ruang ICU",
  "status_perkawinan": "Belum Menikah",
  "status_kehamilan": "Tidak",
  "jumlah_anak": 0
}
```

**❌ Response 400 Bad Request:**
```json
{
  "detail": "Format nomor WhatsApp tidak valid. Contoh: 081234567890 atau +6281234567890."
}
```

**🔧 FIX:** Nomor harus dimulai dengan `08` atau `+628` atau `628`, diikuti 8-15 digit

**Format yang benar:**
- ✅ `"081234567890"` (08 + 10 digit)
- ✅ `"082345678901"` (08 + 10 digit)
- ✅ `"+6281234567890"` (+628 + 10 digit)
- ✅ `"6281234567890"` (628 + 10 digit)
- ✅ `"0812-3456-7890"` (08 + 10 digit dengan dash)
- ✅ `"08 1234 567890"` (08 + 10 digit dengan space)

---

## 📊 Pilihan Nilai Valid untuk Dropdown Fields

### jenis_kelamin
- `"Laki-laki"`
- `"Perempuan"`

### pendidikan
- `"D3 Keperawatan"`
- `"Ners"`
- `"Magister Keperawatan"`
- `"Ners Spesialis"`

### status_pegawai
- `"ASN"`
- `"Non ASN"`
- `"Yang lain"`

### jabatan
- `"Kepala Ruangan"`
- `"Penanggung Jawab Mutu"`
- `"PPJA"`
- `"Ketua tim/PJ shift"`
- `"Perawat Pelaksana"`
- `"Yang lain"` (jika dipilih, isi `jabatan_lain`)

### status_perkawinan
- `"Belum Menikah"`
- `"Menikah"`
- `"Cerai Mati"`
- `"Cerai Hidup"`

### status_kehamilan
- `"Ya"` (hanya untuk Perempuan)
- `"Tidak"` (untuk Perempuan atau AUTO untuk Laki-laki)

---

## 🚀 JavaScript/TypeScript Example

```javascript
async function submitProfile(formData) {
  // PENTING: Konversi string ke integer
  const payload = {
    inisial: formData.inisial.trim(),
    no_wa: formData.no_wa.trim(),
    usia: parseInt(formData.usia, 10),  // STRING → INTEGER
    jenis_kelamin: formData.jenis_kelamin,
    pendidikan: formData.pendidikan,
    lama_bekerja: parseInt(formData.lama_bekerja, 10),  // STRING → INTEGER
    status_pegawai: formData.status_pegawai,
    jabatan: formData.jabatan,
    jabatan_lain: formData.jabatan !== "Yang lain" ? null : formData.jabatan_lain?.trim() || null,
    unit_ruangan: formData.unit_ruangan.trim(),
    status_perkawinan: formData.status_perkawinan,
    status_kehamilan: formData.jenis_kelamin === "Laki-laki" ? "Tidak" : formData.status_kehamilan,
    jumlah_anak: parseInt(formData.jumlah_anak, 10)  // STRING → INTEGER
  };

  try {
    const response = await fetch('/api/v1/users/profile', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const error = await response.json();
      
      if (response.status === 422) {
        // Validation error from Pydantic
        const details = error.detail[0];
        throw new Error(`Field ${details.loc[1]}: ${details.msg}`);
      } else if (response.status === 400) {
        // Validation error from backend logic
        throw new Error(error.detail);
      } else {
        throw new Error(`Server error: ${response.status}`);
      }
    }

    const result = await response.json();
    console.log("✅ Success:", result.message);
    alert("Profil berhasil disimpan!");
    return result;

  } catch (error) {
    console.error("❌ Error:", error.message);
    alert(`Gagal menyimpan profil: ${error.message}`);
    throw error;
  }
}

// Usage
submitProfile({
  inisial: "SB",
  no_wa: "081234567890",
  usia: "28",  // Akan di-convert ke 28
  jenis_kelamin: "Perempuan",
  pendidikan: "Ners",
  lama_bekerja: "5",  // Akan di-convert ke 5
  status_pegawai: "ASN",
  jabatan: "Perawat Pelaksana",
  jabatan_lain: null,
  unit_ruangan: "Ruang ICU",
  status_perkawinan: "Menikah",
  status_kehamilan: "Ya",
  jumlah_anak: "1"  // Akan di-convert ke 1
});
```

---

## 📝 Checklist Validasi Frontend

Sebelum kirim request, pastikan:

- [ ] `usia` = **number** (bukan string)
- [ ] `lama_bekerja` = **number** (bukan string)
- [ ] `jumlah_anak` = **number** (bukan string)
- [ ] `no_wa` format: `08...`, `+628...`, atau `628...` (8-15 digit)
- [ ] `usia` range: 18-65
- [ ] `jenis_kelamin` = `"Perempuan"` atau `"Laki-laki"`
- [ ] `status_kehamilan` = `"Ya"` atau `"Tidak"`
- [ ] Jika `jenis_kelamin` = "Laki-laki" → set `status_kehamilan` = "Tidak"
- [ ] Jika `jabatan` ≠ "Yang lain" → set `jabatan_lain` = `null`
- [ ] Semua field wajib terisi (kecuali `email` dan `jabatan_lain` jika tidak diperlukan)

✅ **Jika semua valid, response akan 201 Created!**

