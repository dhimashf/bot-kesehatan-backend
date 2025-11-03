
from fastapi import HTTPException

# Database imports
from core.services.database import Database
from common.config.db_config import DBConfig

# Service imports
from core.services.profiling_service import get_password_hash
from backend.api.v1.schemas.web_auth import WebAccountCreate

def create_user(db: Database, user: WebAccountCreate):
    """
    Handles the business logic for creating a new user.
    """
    db_user = db.get_user(email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    
    # Create user account with only email and password
    user_id = db.create_user_account(email=user.email, hashed_password=hashed_password)
    
    # Return the basic user info
    return {"id": user_id, "email": user.email}

def create_user_from_telegram(db: Database, email: str):
    """
    Handles the business logic for creating a new user from Telegram.
    The initial password will be set to the user's email.
    """
    db_user = db.get_user(email=email)
    if db_user:
        # If user exists, just return their data. This handles re-registration attempts.
        return {"id": db_user['id'], "email": db_user['email']}
    
    # Hash the email to use it as the initial password.
    hashed_password = get_password_hash(email)
    
    user_id = db.create_user_account(email=email, hashed_password=hashed_password)
    
    return {"id": user_id, "email": email}

def check_user_profile_status(db: Database, user_id: int) -> dict:
    """
    Checks if a user has completed their identity profile.
    A profile is considered complete if all required biodata fields are filled.
    """
    profile = db.get_profile_by_user_id(user_id)
    
    biodata_completed = False
    if profile:
        # Daftar field biodata yang wajib diisi (tidak termasuk 'jabatan_lain' yang opsional)
        required_fields = [
            'inisial', 'no_wa', 'usia', 'jenis_kelamin', 'pendidikan', 
            'lama_bekerja', 'status_pegawai', 'jabatan', 
            'unit_ruangan', 'status_perkawinan', 'status_kehamilan', 'jumlah_anak'
        ]
        # Cek apakah semua field yang wajib ada di dalam data profil dan tidak kosong
        biodata_completed = all(profile.get(field) is not None for field in required_fields)

    # Cek apakah ada setidaknya satu hasil kuesioner
    latest_result = db.get_latest_health_result(user_id)

    return {
        "biodata_completed": biodata_completed,
        "health_results_completed": latest_result is not None
    }

def create_user_from_google(db: Database, user_data: dict):
    """
    Membuat akun pengguna baru dari data login Google (tanpa password).
    Juga membuat entri profil dasar.
    """
    email = user_data.get('email')
    
    # Cek lagi untuk memastikan email belum ada, jika sudah ada, kembalikan user yang ada.
    existing_user = db.get_user(email=email)
    if existing_user:
        return existing_user

    # Buat akun di tabel 'users' dengan password NULL
    new_user_id = db.create_user_account(email, None) # Hashed password is None

    # Buat entri di tabel 'profiles' dengan data dari Google
    db.insert_or_update_profile(new_user_id, user_data)

    return db.get_user_by_id(new_user_id)
