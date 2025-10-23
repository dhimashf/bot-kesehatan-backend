from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any
from enum import Enum

class JenisKelamin(str, Enum):
    LAKI_LAKI = "Laki-laki"
    PEREMPUAN = "Perempuan"

class Pendidikan(str, Enum):
    D3 = "D3 Keperawatan"
    NERS = "Ners"
    MAGISTER = "Magister Keperawatan"
    SPESIALIS = "Ners Spesialis"

class StatusPegawai(str, Enum):
    ASN = "ASN"
    NON_ASN = "Non ASN"
    LAINNYA = "Yang lain"

class Jabatan(str, Enum):
    KEPALA_RUANGAN = "Kepala Ruangan"
    PENANGGUNG_JAWAB_MUTU = "Penanggung Jawab Mutu"
    PPJA = "PPJA"
    KETUA_TIM = "Ketua tim/PJ shift"
    PERAWAT_PELAKSANA = "Perawat Pelaksana"
    LAINNYA = "Yang lain"

class StatusPerkawinan(str, Enum):
    BELUM_MENIKAH = "Belum Menikah"
    MENIKAH = "Menikah"
    CERAI_MATI = "Cerai Mati"
    CERAI_HIDUP = "Cerai Hidup"

class StatusKehamilan(str, Enum):
    YA = "Ya"
    TIDAK = "Tidak"

class BiodataSchema(BaseModel):
    email: EmailStr
    inisial: str
    no_wa: str
    usia: int
    jenis_kelamin: JenisKelamin
    pendidikan: Pendidikan
    lama_bekerja: int
    status_pegawai: StatusPegawai
    jabatan: Jabatan
    jabatan_lain: str | None = None
    unit_ruangan: str
    status_perkawinan: StatusPerkawinan
    status_kehamilan: StatusKehamilan
    jumlah_anak: str

class ProfilingAnswers(BaseModel):
    user_id: int # The ID from the database
    answers: Dict[str, List[int]] # e.g., {"who5": [3, 4, 5, 2, 4], "gad7": [1,2,3,1,2,3,1]}

class UserProfileResponse(BaseModel):
    biodata: BiodataSchema
    profiling_results: Dict[str, Any]