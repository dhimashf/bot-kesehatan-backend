import os
from dotenv import load_dotenv

# Nonaktifkan telemetri ChromaDB sebelum library lain diimpor.
# Ini mencegah error "capture() takes 1 positional argument but 3 were given".
os.environ["ANONYMIZED_TELEMETRY"] = "false"

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
    APP_PORT = int(os.getenv("APP_PORT", 8010))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    INTERNAL_API_HOST = os.getenv("INTERNAL_API_HOST") # Host untuk komunikasi internal (bot -> api)

    # JWT Configuration
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError(
            "ERROR: SECRET_KEY environment variable is not set. "
            "The application cannot start without it for security reasons."
        )
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