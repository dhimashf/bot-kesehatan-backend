from fastapi import APIRouter

# Impor semua router dari direktori 'routes'
from .routes import chat, web_auth, users, web_chat as web_chat_router

# Buat instance APIRouter utama untuk versi 1 dari API
api_router = APIRouter()

# Gabungkan semua router parsial ke dalam router utama dengan prefix yang sesuai.
# Prefix ini akan ditambahkan setelah '/api/v1' yang didefinisikan di backend/app.py.

# Endpoint untuk komunikasi internal dari bot Telegram
api_router.include_router(chat.router, prefix="/internal/chat", tags=["Internal Bot Chat"])

# Endpoint untuk autentikasi dari antarmuka web
api_router.include_router(web_auth.router, prefix="/web-auth", tags=["Web Authentication"])

# Endpoint untuk manajemen data pengguna (profil, hasil, dll.)
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# Endpoint untuk fungsionalitas chat dari antarmuka web
api_router.include_router(web_chat_router.router, prefix="/web-chat", tags=["Web Chat"])