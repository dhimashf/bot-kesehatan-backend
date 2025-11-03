from authlib.integrations.starlette_client import OAuth
from common.config.settings import settings
from core.services.database import Database
from backend.services import user_service, web_auth_service
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

# Inisialisasi OAuth
oauth = OAuth()

# --- DEBUGGING: Cek apakah kredensial Google dimuat dengan benar ---
logger.info(f"Memuat Google Client ID: {'ADA' if settings.GOOGLE_CLIENT_ID else 'KOSONG'}")
logger.info(f"Memuat Google Client Secret: {'ADA' if settings.GOOGLE_CLIENT_SECRET else 'KOSONG'}")
# --- AKHIR DEBUGGING ---

# Konfigurasi Google OAuth Client
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

def process_google_login(db: Database, user_info: dict):
    """
    Memproses login pengguna setelah mendapatkan data dari Google.
    Jika pengguna belum ada, buat akun baru.
    Kemudian, buat JWT token untuk sesi tersebut.
    """
    email = user_info.get('email')
    if not email:
        return None

    # Cek apakah pengguna sudah ada di database
    user = db.get_user(email=email)

    if not user:
        # Jika pengguna belum ada, buat akun baru (tanpa password)
        # Nama diambil dari profil Google, inisial dibuat dari nama
        name = user_info.get('name', 'User')
        initial = "".join([s[0] for s in name.split()]).upper()

        new_user_data = {
            'email': email,
            'inisial': initial,
            'nama_lengkap': name
        }
        user = user_service.create_user_from_google(db, user_data=new_user_data)

    # Buat JWT token untuk pengguna
    access_token_expires = timedelta(minutes=web_auth_service.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = web_auth_service.create_access_token(
        data={"sub": user['email'], "id": user['id'], "role": user['role']},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user # Kembalikan juga data user
    }