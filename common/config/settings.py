import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # OpenRouter Configuration - GUNAKAN INI
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
    OPENROUTER_REFERRER = "https://github.com/Psiko-bot"  # Bebas!
    OPENROUTER_TITLE = "Psiko Chatbot Indonesia"  # Bebas!
    
    # Application Configuration
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", 8000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # JWT Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "9a8f7a5e6d5c4b3a2e1f0d9c8b7a6e5d4c3b2a1f0e9d8c7b6a5d4c3b2a1f0e9d")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

    # Secret token for internal communication between bot and backend
    INTERNAL_BOT_TOKEN = os.getenv("INTERNAL_BOT_TOKEN", "a_very_secret_internal_token_that_should_be_long_and_random")
    
    # Bot Configuration
    BOT_NAME = "🤖 Chatbot Psiko"
    MAX_CONTEXT_LENGTH = 4000
    
    # System Prompt
    SYSTEM_PROMPT = """Anda adalah asisten ahli Psiko ... dan dapat menjawab pertanyaan selain itu namun sesuai data di kitab.pdf"""  # Isi dengan prompt Anda

settings = Settings()