from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from backend.services import google_auth_service, web_auth_service, user_service
from core.services.database import Database
from common.config.settings import settings
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

router = APIRouter()

@router.get("/login")
async def login_via_google(request: Request):
    """
    Endpoint untuk me-redirect pengguna ke halaman login Google.
    """
    # Menggunakan URI redirect eksplisit dari settings untuk konsistensi
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    if not redirect_uri:
        raise HTTPException(status_code=500, detail="GOOGLE_REDIRECT_URI tidak diatur di file .env")
    return await google_auth_service.oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/callback")
async def auth_google_callback(request: Request, db: Database = Depends(web_auth_service.get_db)):
    """
    Endpoint callback yang dipanggil Google setelah user login.
    Memproses token, membuat/login user, dan me-redirect kembali ke frontend.
    """
    token = await google_auth_service.oauth.google.authorize_access_token(request)
    user_info = token.get('userinfo')

    if not user_info:
        return RedirectResponse(url="/?error=LoginFailed") # Redirect ke frontend dengan pesan error

    # Proses login/register dan dapatkan data user serta token JWT
    processed_data = google_auth_service.process_google_login(db, user_info)
    user = processed_data["user"]
    jwt_token = processed_data["access_token"]

    # --- LOGIKA BARU: Cek status kelengkapan profil ---
    profile_status = user_service.check_user_profile_status(db, user['id'])
    
    redirect_url_base = ""
    if profile_status.get("biodata_completed"):
        # Jika biodata lengkap, arahkan ke halaman utama/dashboard
        redirect_url_base = settings.FRONTEND_LOGIN_SUCCESS_URL
        if not redirect_url_base:
            raise HTTPException(status_code=500, detail="FRONTEND_LOGIN_SUCCESS_URL tidak diatur di file .env")
    else:
        # Jika biodata tidak lengkap, arahkan ke form identitas
        redirect_url_base = settings.FRONTEND_IDENTITY_FORM_URL
        if not redirect_url_base:
            raise HTTPException(status_code=500, detail="FRONTEND_IDENTITY_FORM_URL tidak diatur di file .env")

    frontend_redirect_url = f"{redirect_url_base}?token={jwt_token}"
    return RedirectResponse(url=frontend_redirect_url)

class TokenSignInRequest(BaseModel):
    idToken: str # Cukup terima idToken dari mobile

@router.post("/token-signin")
async def token_signin(
    request_body: TokenSignInRequest, 
    db: Database = Depends(web_auth_service.get_db)
):
    """
    Endpoint untuk login dari mobile (React Native) menggunakan idToken dari Google.
    """
    try:
        # Verifikasi idToken yang diterima dari aplikasi mobile
        id_info = id_token.verify_oauth2_token(
            request_body.idToken, # Gunakan idToken dari request body
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID # Gunakan Client ID khusus untuk mobile
        )

        # Pastikan token dikeluarkan oleh Google
        if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')

        # Ambil informasi pengguna dari token yang sudah diverifikasi
        user_info = {
            "email": id_info["email"],
            "name": id_info.get("name"),
            "given_name": id_info.get("given_name"),
            "family_name": id_info.get("family_name"),
            "picture": id_info.get("picture"),
        }

        # Gunakan kembali logika yang sudah ada untuk memproses login/register
        processed_data = google_auth_service.process_google_login(db, user_info)
        
        # Sesuai permintaan klien mobile, sertakan juga objek user
       
        user_data = dict(processed_data["user"]).copy()
        # Tambahkan kunci 'photo' ke dictionary yang sudah disalin.
        user_data['photo'] = user_info.get("picture")
        # SOLUSI: Tambahkan juga kunci 'name' dari info Google.
        user_data['name'] = user_info.get("name")
        
        # PENTING: Hapus hashed_password dari respons untuk keamanan.
        user_data.pop("hashed_password", None)

        return {"access_token": processed_data["access_token"], "token_type": "bearer", "user": user_data}

    except ValueError as e:
        # Jika token tidak valid
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {e}")

@router.get("/me")
async def get_google_user_me(current_user: dict = Depends(web_auth_service.get_current_active_user)):
    """
    Endpoint terproteksi untuk mendapatkan data user yang sedang login via Google.
    """
    return current_user