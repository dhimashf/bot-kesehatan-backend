import psycopg2
from psycopg2 import pool
from psycopg2.extras import DictCursor
from typing import Optional, Any
import threading
import os
import logging

# Lock untuk memastikan inisialisasi pool thread-safe
_pool_lock = threading.Lock()
_connection_pool = None

class Database:
    """
    Kelas Database yang mengelola satu connection pool (singleton) untuk PostgreSQL.
    Ini thread-safe dan dirancang untuk digunakan di seluruh aplikasi.
    """
    def __init__(self, min_conn: int = 1, max_conn: int = 5):
        global _connection_pool
        if _connection_pool is None:
            with _pool_lock:
                if _connection_pool is None:
                    logging.info("✅ Menggunakan DATABASE_URL untuk koneksi pool.")
                    # SOLUSI: Gunakan DATABASE_URL secara langsung jika ada.
                    # Ini adalah cara yang paling andal dan standar.
                    try:
                        dsn = os.getenv("DATABASE_URL")
                        if dsn:
                            _connection_pool = psycopg2.pool.ThreadedConnectionPool(
                                min_conn, max_conn, dsn=dsn
                            )
                        else:
                            # Fallback jika DATABASE_URL tidak ada (untuk development lokal)
                            logging.warning("DATABASE_URL tidak ditemukan, menggunakan variabel DB individual.")
                            db_params = {
                                'dbname': os.getenv('DB_NAME', 'kesehatan'),
                                'user': os.getenv('DB_USER', 'postgres'),
                                'password': os.getenv('DB_PASSWORD', 'password'),
                                'host': os.getenv('DB_HOST', 'db'),
                                'port': int(os.getenv('DB_PORT', '5432'))
                            }
                            _connection_pool = psycopg2.pool.ThreadedConnectionPool(
                                min_conn, max_conn, **db_params
                            )
                        logging.info("✅ Koneksi pool PostgreSQL berhasil dibuat.")
                    except (Exception, psycopg2.OperationalError) as e:
                        logging.error(f"❌ GAGAL membuat koneksi pool ke PostgreSQL: {e}")
                        raise

        self.pool = _connection_pool
        self.conn = None
        self.cursor = None

    def __enter__(self):
        """Memungkinkan penggunaan 'with Database() as db:'."""
        self.conn = self.pool.getconn()
        self.cursor = self.conn.cursor(cursor_factory=DictCursor)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        PERBAIKAN: Menambahkan logic commit/rollback yang sangat penting.
        Tanpa ini, semua query 'with' Anda TIDAK AKAN TERSIMPAN.
        """
        try:
            if exc_type:
                # Jika terjadi error di dalam block 'with', batalkan (rollback)
                if self.conn:
                    self.conn.rollback()
            else:
                # Jika tidak ada error, simpan (commit)
                if self.conn:
                    self.conn.commit()
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.pool.putconn(self.conn)

    def execute_query(self, query, params=None, fetch=None):
        """
        PERBAIKAN: Disederhanakan untuk menangani commit & rollback dengan benar.
        """
        conn = None
        cursor = None
        try:
            conn = self.pool.getconn()
            cursor = conn.cursor(cursor_factory=DictCursor)
            
            cursor.execute(query, params)
            
            if fetch == 'one':
                conn.commit() # Commit untuk SELECT (diperlukan di beberapa mode)
                return cursor.fetchone()
            elif fetch == 'all':
                conn.commit() # Commit untuk SELECT
                return cursor.fetchall()
            elif fetch == 'returning':
                # Mode baru untuk mengambil ID dari RETURNING
                conn.commit()
                result = cursor.fetchone()
                return result[0] if result else None # Kembalikan nilai ID-nya saja
            else:
                # Default (INSERT, UPDATE, DELETE tanpa returning)
                conn.commit()
                return cursor.rowcount # Kembalikan jumlah baris yang terpengaruh
        
        except (Exception, psycopg2.Error) as e:
            if conn:
                conn.rollback() # Batalkan jika ada error
            logging.error(f"Error executing query: {e}", exc_info=True)
            raise e # Lemparkan error agar bisa ditangani
        
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.pool.putconn(conn) # Kembalikan koneksi

    def close(self):
        """Menutup seluruh connection pool. Panggil saat aplikasi berhenti."""
        global _connection_pool
        if _connection_pool is not None:
            _connection_pool.closeall()
            _connection_pool = None

    def create_user_account(self, email: str, hashed_password: str) -> Optional[int]:
        """
        Creates a new user account.
        """
        sql = """
        INSERT INTO users (email, hashed_password) VALUES (%s, %s)
        RETURNING id;
        """
        values = (email, hashed_password)
        # Gunakan fetch='returning' agar lebih jelas
        return self.execute_query(sql, values, fetch='returning')

    def insert_or_update_profile(self, user_id: int, biodata: dict):
        """
        (LOGIKA ANDA BAGUS!) Menggunakan ON CONFLICT (UPSERT).
        Ini akan meng-update jika user_id sudah ada, atau insert jika belum.
        """
        biodata.pop('email', None)
        valid_columns = [
            'inisial', 'no_wa', 'usia', 'jenis_kelamin', 'pendidikan', 
            'lama_bekerja', 'status_pegawai', 'jabatan', 'jabatan_lain', 
            'unit_ruangan', 'status_perkawinan', 'status_kehamilan', 'jumlah_anak'
        ]
        filtered_biodata = {k: v for k, v in biodata.items() if k in valid_columns}
        
        if not filtered_biodata:
            return 0 # Tidak ada yang di-update

        columns = ['user_id'] + list(filtered_biodata.keys())
        placeholders = ", ".join(['%s'] * len(columns))
        
        update_columns = ", ".join([f"{col} = EXCLUDED.{col}" for col in filtered_biodata.keys()])
        
        # CATATAN: Pastikan tabel 'profiles' Anda punya 'updated_at'
        # Jika tidak, hapus baris ", updated_at = CURRENT_TIMESTAMP"
        sql = f"""
        INSERT INTO profiles ({", ".join(columns)})
        VALUES ({placeholders})
        ON CONFLICT (user_id) DO UPDATE SET
        {update_columns}, updated_at = CURRENT_TIMESTAMP;
        """
        
        values = tuple([user_id] + list(filtered_biodata.values()))
        
        # PERBAIKAN: Panggil execute_query (akan mengembalikan rowcount)
        return self.execute_query(sql, values)

    def insert_health_result(self, health_data: dict):
        sql = """
        INSERT INTO health_results (user_id, who5_total, gad7_total, mbi_emosional_total, mbi_sinis_total, mbi_pencapaian_total, naqr_pribadi_total, naqr_pekerjaan_total, naqr_intimidasi_total, k10_total)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        values = (
            health_data['user_id'], health_data['who5_total'], health_data['gad7_total'], health_data['mbi_emosional_total'],
            health_data['mbi_sinis_total'], health_data['mbi_pencapaian_total'], health_data['naqr_pribadi_total'], health_data['naqr_pekerjaan_total'], health_data['naqr_intimidasi_total'], health_data['k10_total']
        )
        # Gunakan fetch='returning'
        return self.execute_query(sql, values, fetch='returning')

    # --- Metode GET (SELECT) sudah benar ---
    def get_user(self, email: str) -> Optional[dict]:
        return self.execute_query("SELECT * FROM users WHERE email=%s", (email,), fetch='one')

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        return self.execute_query("SELECT * FROM users WHERE id=%s", (user_id,), fetch='one')

    def get_profile_by_user_id(self, user_id: int) -> Optional[dict]:
        return self.execute_query("SELECT * FROM profiles WHERE user_id=%s", (user_id,), fetch='one')

    def get_latest_health_result(self, user_id: int) -> Optional[dict]:
        return self.execute_query("SELECT * FROM health_results WHERE user_id=%s ORDER BY created_at DESC LIMIT 1", (user_id,), fetch='one')

    def get_all_health_results(self, user_id: int) -> list:
        return self.execute_query("SELECT * FROM health_results WHERE user_id=%s ORDER BY created_at DESC", (user_id,), fetch='all')

    # --- Admin Get Methods ---
    def get_all_users(self) -> list:
        return self.execute_query("SELECT id, email, role, created_at FROM users ORDER BY id", fetch='all')

    def get_all_profiles(self) -> list:
        return self.execute_query("SELECT p.*, u.email FROM profiles p JOIN users u ON p.user_id = u.id ORDER BY p.user_id", fetch='all')

    def get_all_health_results_admin(self) -> list:
        return self.execute_query("SELECT hr.*, u.email FROM health_results hr JOIN users u ON hr.user_id = u.id ORDER BY hr.created_at DESC", fetch='all')


    # --- PERBAIKAN: Sederhanakan metode DELETE dan UPDATE ---
    def delete_health_result_by_id(self, result_id: int, user_id: int) -> bool:
        """PERBAIKAN: Dibuat konsisten menggunakan execute_query."""
        query = "DELETE FROM health_results WHERE id = %s AND user_id = %s"
        try:
            rowcount = self.execute_query(query, (result_id, user_id))
            return rowcount > 0 # True jika 1 baris (atau lebih) terhapus
        except Exception as e:
            logging.error(f"Error deleting health result: {e}")
            return False

    def update_user_password(self, user_id: int, hashed_password: str) -> bool:
        """PERBAIKAN: Dibuat konsisten menggunakan execute_query."""
        query = "UPDATE users SET hashed_password = %s WHERE id = %s"
        try:
            rowcount = self.execute_query(query, (hashed_password, user_id))
            return rowcount > 0 # True jika 1 baris (atau lebih) ter-update
        except Exception as e:
            logging.error(f"Error updating password for user {user_id}: {e}")
            return False