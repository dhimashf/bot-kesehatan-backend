import os
from dotenv import load_dotenv

load_dotenv()

class DBConfig:
    """
    Memuat konfigurasi database dari environment variables.
    Akan memprioritaskan DATABASE_URL jika tersedia.
    """
    
    # 1. Tambahkan baris ini untuk membaca DATABASE_URL Anda
    #    Ini adalah variabel terpenting untuk koneksi PostgreSQL baru Anda.
    DATABASE_URL = os.getenv('DATABASE_URL')

    # 2. Variabel di bawah ini sekarang berfungsi sebagai 'fallback' 
    #    jika DATABASE_URL tidak diset.
    
    HOST = os.getenv('DB_HOST', '127.0.0.1')
    
    # 3. GANTI port default dari 3306 menjadi 5432
    #    Ini adalah port default untuk PostgreSQL.
    PORT = int(os.getenv('DB_PORT', '5432')) 
    
    USER = os.getenv('DB_USER', 'root')
    PASSWORD = os.getenv('DB_PASSWORD', '')
    NAME = os.getenv('DB_NAME', 'kesehatan')