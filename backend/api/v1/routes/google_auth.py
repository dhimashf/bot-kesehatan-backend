from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from backend.services import google_auth_service, web_auth_service, user_service
from core.services.database import Database
from common.config.settings import settings

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

@router.get("/me")
async def get_google_user_me(current_user: dict = Depends(web_auth_service.get_current_active_user)):
    """
    Endpoint terproteksi untuk mendapatkan data user yang sedang login via Google.
    """
    return current_user