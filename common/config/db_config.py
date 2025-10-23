import os
from dotenv import load_dotenv

load_dotenv()

class DBConfig:
    HOST = os.getenv('DB_HOST', '127.0.0.1')
    PORT = int(os.getenv('DB_PORT', '3306'))
    USER = os.getenv('DB_USER', 'root')
    PASSWORD = os.getenv('DB_PASSWORD', '')
    NAME = os.getenv('DB_NAME', 'kesehatan')
