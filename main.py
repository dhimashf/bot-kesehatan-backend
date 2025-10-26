import uvicorn
import threading
import asyncio
from common.config.settings import settings
from bot_tele.bot import psikobot

def run_bot():
    """Fungsi untuk menjalankan bot dalam thread terpisah."""
    # Buat dan atur event loop baru untuk thread ini
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    print("Starting Telegram bot polling...")
    psikobot.run()

if __name__ == "__main__":
    # Jalankan bot dalam thread terpisah untuk development lokal
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True  # Atur sebagai daemon thread
    bot_thread.start()

    # Jalankan server FastAPI
    print(f"Starting FastAPI server at http://{settings.APP_HOST}:{settings.APP_PORT}")
    # Gunakan file backend/app.py sebagai target uvicorn. `reload` diaktifkan hanya untuk development.
    uvicorn.run("backend.app:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=settings.DEBUG)