import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from bot_tele.bot import psikobot
from backend.api.v1 import api_router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the bot's lifecycle.
    The bot starts polling when the FastAPI server starts and stops when it shuts down.
    """
    logger.info("Application starting up...")
    await psikobot.run_polling()
    yield
    logger.info("Application shutting down...")
    await psikobot.stop_polling()

# Initialize FastAPI app with the lifespan manager
app = FastAPI(
    title="PsikoBot Backend",
    lifespan=lifespan
)

# --- Konfigurasi CORS Middleware ---
# Ini mengizinkan frontend (misalnya, yang berjalan di localhost:3000)
# untuk berkomunikasi dengan backend FastAPI ini.
origins = [
    "http://localhost:3000",  # Alamat server development frontend
    "http://127.0.0.1:3000", # Alternatif untuk localhost
    # Anda bisa menambahkan alamat frontend produksi di sini nanti
    # "https://your-production-frontend.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Mengizinkan semua metode (GET, POST, dll.)
    allow_headers=["*"], # Mengizinkan semua header
)
# --- Akhir Konfigurasi CORS ---

# Include the API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Health check endpoint for Docker and monitoring."""
    return {"status": "ok"}