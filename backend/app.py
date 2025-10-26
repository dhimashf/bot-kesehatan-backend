import os
import sys
import asyncio
from fastapi import FastAPI
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from common.data.kitab_loader import kitab_loader
from core.services.rag_service import rag_service

from common.config.settings import settings
from bot_tele.bot import psikobot
# Impor semua router yang dibutuhkan
from backend.api.v1.routes import chat as internal_chat_router
from backend.api.v1.routes import web_chat as web_chat_router
from backend.api.v1.routes import users as users_router
from backend.api.v1.routes import web_auth as web_auth_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info("Application startup: Starting Telegram bot polling...")
    asyncio.create_task(psikobot.run_polling())
    yield
    # --- Shutdown ---
    logger.info("Application shutdown: Stopping Telegram bot polling...")
    await psikobot.stop_polling()


app = FastAPI(
    title="🤖 Chatbot Psiko API",
    description="API untuk Chatbot Psiko berbasis Telegram dengan OpenRouter",
    version="1.0.0",
    lifespan=lifespan
)

# --- CORS Middleware ---
# Ini sangat penting agar frontend bisa berkomunikasi dengan API ini.
origins = [
    "http://localhost:3000",  # Alamat server development frontend Anda
    "http://127.0.0.1:3000", # Alternatif untuk localhost
    "http://localhost:5500",  # Alamat dari `python -m http.server 5500`
    "http://127.0.0.1:5500",  # Alamat dari `python -m http.server 5500`
    "http://localhost:8080",  # Alamat server development frontend lainnya
    "https://frontend-bot-kesehatan.vercel.app", # URL Frontend Vercel Anda yang sudah di-deploy
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # Mengizinkan origin yang spesifik
    allow_credentials=True,   # Mengizinkan cookies/authorization headers
    allow_methods=["*"],        # Mengizinkan semua metode (GET, POST, dll.)
    allow_headers=["*"],        # Mengizinkan semua header
)

# Include API routers
# Endpoint untuk web (aman dengan JWT)
app.include_router(web_chat_router.router, prefix="/api/v1/chat", tags=["Web Chat"])
# Endpoint untuk bot (aman dengan secret header)
app.include_router(internal_chat_router.router, prefix="/api/v1/internal/chat", tags=["Internal Bot Chat"])
app.include_router(users_router.router, prefix="/api/v1/users", tags=["Users & Profiling"])
app.include_router(web_auth_router.router, prefix="/api/v1/auth", tags=["Authentication"])

# --- Mount Static Files (Dinonaktifkan) ---
# Baris ini dinonaktifkan karena folder 'static' (frontend) sudah dipisah dan di-deploy ke Vercel.
# app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "static"), html=True), name="static")

@app.get("/api")
async def welcome_api():
    """Endpoint selamat datang untuk /api."""
    return {"message": "welcome to fastapi"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "api": "running"
    }

def main():
    """Main function to run the application"""
    uvicorn.run(
        "backend.app:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )

if __name__ == "__main__":
    main()
