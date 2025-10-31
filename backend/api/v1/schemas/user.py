from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# --- Skema Dasar ---

class User(BaseModel):
    """Skema dasar untuk data pengguna, digunakan untuk respons."""
    id: int
    email: EmailStr
    role: str  # <-- TAMBAHKAN FIELD INI

    class Config:
        from_attributes = True # Dulu orm_mode

class UserProfile(BaseModel):
    """Skema untuk data profil/biodata pengguna."""
    inisial: str
    no_wa: str
    usia: int
    jenis_kelamin: str
    pendidikan: str
    lama_bekerja: int
    status_pegawai: str
    jabatan: str
    jabatan_lain: Optional[str] = None
    unit_ruangan: str
    status_perkawinan: str
    status_kehamilan: str
    jumlah_anak: int
    email: Optional[EmailStr] = None # Opsional, diisi oleh backend

class HealthResultBase(BaseModel):
    """Skema dasar untuk hasil kuesioner."""
    id: int
    user_id: int
    who5_total: int
    gad7_total: int
    mbi_emosional_total: int
    mbi_sinis_total: int
    mbi_pencapaian_total: int
    naqr_pribadi_total: int
    naqr_pekerjaan_total: int
    naqr_intimidasi_total: int
    k10_total: int
    created_at: datetime

class FullUserProfileResponse(BaseModel):
    """Skema untuk respons profil lengkap pengguna."""
    biodata: Optional[UserProfile] = None
    health_results: Optional[List[HealthResultBase]] = []
    biodata_completed: bool
    health_results_completed: bool

class HealthResultPayload(BaseModel):
    """Skema untuk payload yang dikirim dari frontend saat submit kuesioner."""
    who5_total: int
    gad7_total: int
    k10_total: int
    mbi_scores: List[int]
    naqr_pribadi_total: int
    naqr_pekerjaan_total: int
    naqr_intimidasi_total: int

class SummaryItem(BaseModel):
    score: int
    interpretation: str

class HealthResultSummary(BaseModel):
    """Skema untuk ringkasan hasil yang dikembalikan ke frontend."""
    message: str
    summary: dict[str, SummaryItem]