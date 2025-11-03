import uvicorn
from common.config.settings import settings
import logging

# --- Konfigurasi Logging Global ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    # Server FastAPI sekarang mengelola siklus hidup bot melalui lifespan events.
    # Tidak perlu lagi menjalankan bot di thread terpisah.
    print(f"Starting FastAPI server at http://{settings.APP_HOST}:{settings.APP_PORT}")
    # Gunakan file backend/app.py sebagai target uvicorn. `reload` diaktifkan hanya untuk development.
    uvicorn.run("backend.app:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=False) # Set reload ke False untuk tes OAuth