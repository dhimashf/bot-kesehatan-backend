from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# Basic User schema (for /me endpoint)
class User(BaseModel):
    id: int
    email: str

# Schema for the biodata (profiles table)
class UserProfile(BaseModel):
    email: Optional[str] = None # Added to hold email for display purposes
    inisial: Optional[str] = None
    no_wa: Optional[str] = None
    usia: Optional[int] = None
    jenis_kelamin: Optional[str] = None
    pendidikan: Optional[str] = None
    lama_bekerja: Optional[int] = None
    status_pegawai: Optional[str] = None
    jabatan: Optional[str] = None
    jabatan_lain: Optional[str] = None
    unit_ruangan: Optional[str] = None
    status_perkawinan: Optional[str] = None
    status_kehamilan: Optional[str] = None
    jumlah_anak: Optional[int] = None

    class Config:
        # Allow population by field name or alias (if aliases were defined)
        # For now, field names directly match DB columns (snake_case)
        from_attributes = True

# Schema for the latest health results (health_results table)
class LatestHealthResult(BaseModel):
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
    # New fields for categories and total scores
    who5_category: Optional[str] = None
    gad7_category: Optional[str] = None
    k10_category: Optional[str] = None
    mbi_emosional_category: Optional[str] = None
    mbi_sinis_category: Optional[str] = None
    mbi_pencapaian_category: Optional[str] = None
    mbi_total: Optional[int] = None
    naqr_total: Optional[int] = None

    class Config:
        from_attributes = True

# Schema for the full user profile response (combining biodata and health results)
class FullUserProfileResponse(BaseModel):
    biodata: Optional[UserProfile] = None
    health_results: Optional[List[LatestHealthResult]] = None # Diubah menjadi List
    biodata_completed: bool = False
    health_results_completed: bool = False

# Schema for submitting health results (from frontend)
class HealthResultPayload(BaseModel):
    who5_total: int
    gad7_total: int
    mbi_scores: List[int] # Raw MBI scores for processing
    naqr_pribadi_total: int
    naqr_pekerjaan_total: int
    naqr_intimidasi_total: int
    k10_total: int

# Schema for the summary returned after submitting health results
class HealthResultSummary(BaseModel):
    message: str
    summary: Dict[str, Dict[str, Any]]