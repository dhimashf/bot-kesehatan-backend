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
        conn = None
        for attempt in range(2): # Coba maksimal 2 kali
            try:
                conn = self.pool.getconn()
                with conn.cursor(cursor_factory=DictCursor) as cursor:
                    cursor.execute(query, params)
                    
                    if fetch == 'one':
                        result = cursor.fetchone()
                    elif fetch == 'all':
                        result = cursor.fetchall()
                    elif fetch == 'returning':
                        row = cursor.fetchone()
                        result = row[0] if row else None
                    else:
                        result = cursor.rowcount
                
                conn.commit()
                return result

            except psycopg2.OperationalError as e:
                logging.warning(f"Attempt {attempt + 1}: OperationalError executing query: {e}. Retrying...")
                if conn:
                    # Jangan kembalikan koneksi yang rusak ke pool
                    self.pool.putconn(conn, close=True)
                    conn = None # Reset conn
                if attempt == 1: # Jika percobaan terakhir gagal, lemparkan error
                    raise e
                # Jika bukan percobaan terakhir, loop akan berlanjut untuk mencoba lagi

            except (Exception, psycopg2.Error) as e:
                if conn:
                    conn.rollback()
                logging.error(f"Error executing query: {e}", exc_info=True)
                raise e
            
            finally:
                if conn:
                    # Kembalikan koneksi yang baik ke pool
                    self.pool.putconn(conn)

    def close(self):
        """Menutup seluruh connection pool. Panggil saat aplikasi berhenti."""
        global _connection_pool
        if _connection_pool is not None:
            _connection_pool.closeall()
            _connection_pool = None

    def create_user_account(self, email: str, hashed_password: Optional[str]) -> Optional[int]:
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
        INSERT INTO health_results (
            user_id, who5_total, gad7_total, mbi_emosional_total, mbi_sinis_total, 
            mbi_pencapaian_total, naqr_pribadi_total, naqr_pekerjaan_total, 
            naqr_intimidasi_total, k10_total, naqr_bullying_experience, 
            naqr_bullying_actors, naqr_bullying_perpetrators_detail
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        values = (
            health_data['user_id'], health_data['who5_total'], health_data['gad7_total'], 
            health_data['mbi_emosional_total'], health_data['mbi_sinis_total'], 
            health_data['mbi_pencapaian_total'], health_data['naqr_pribadi_total'], 
            health_data['naqr_pekerjaan_total'], health_data['naqr_intimidasi_total'], 
            health_data['k10_total'],
            # Kolom baru, akan mengambil nilai dari health_data atau None jika tidak ada (dari setdefault)
            health_data.get('naqr_bullying_experience'),
            health_data.get('naqr_bullying_actors'),
            health_data.get('naqr_bullying_perpetrators_detail')
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

    def get_all_results_with_biodata_admin(self) -> list:
        """
        Fetches all health results and joins them with corresponding biodata and user email.
        This is an admin-only function.
        """
        sql = """
            SELECT
                p.inisial, p.no_wa, p.usia, p.jenis_kelamin, p.pendidikan,
                p.lama_bekerja, p.status_pegawai, p.jabatan, p.jabatan_lain,
                p.unit_ruangan, p.status_perkawinan, p.status_kehamilan, p.jumlah_anak,
                u.email,
                hr.*
            FROM
                health_results hr
            LEFT JOIN
                profiles p ON hr.user_id = p.user_id
            LEFT JOIN
                users u ON hr.user_id = u.id
            ORDER BY
                hr.created_at DESC;
        """
        return self.execute_query(sql, fetch='all')

    def get_all_users_with_status_and_data_admin(self) -> list:
        """
        Query yang dioptimalkan untuk mengambil semua pengguna beserta biodata dan
        riwayat kuesioner mereka dalam satu kali panggilan. Menggunakan LEFT JOIN.
        """
        sql = """
        SELECT
            u.id AS user_id,
            u.email,
            u.role,
            p.inisial, p.no_wa, p.usia, p.jenis_kelamin, p.pendidikan,
            p.lama_bekerja, p.status_pegawai, p.jabatan, p.jabatan_lain,
            p.unit_ruangan, p.status_perkawinan, p.status_kehamilan, p.jumlah_anak,
            hr.id AS health_result_id,
            hr.who5_total, hr.gad7_total, hr.mbi_emosional_total, hr.mbi_sinis_total,
            hr.mbi_pencapaian_total, hr.naqr_pribadi_total, hr.naqr_pekerjaan_total,
            hr.naqr_intimidasi_total, hr.k10_total, hr.created_at,
            hr.naqr_bullying_experience, hr.naqr_bullying_actors,
            hr.naqr_bullying_perpetrators_detail
        FROM
            users u
        LEFT JOIN
            profiles p ON u.id = p.user_id
        LEFT JOIN
            health_results hr ON u.id = hr.user_id
        ORDER BY
            u.id, hr.created_at DESC;
        """
        return self.execute_query(sql, fetch='all')

    def update_health_result_bullying(self, user_id: int, bullying_data: dict):
        """
        Updates the latest health_result for a user with bullying survey data.
        """
        # Menemukan ID hasil kesehatan terbaru untuk pengguna ini
        latest_result_id_query = "SELECT id FROM health_results WHERE user_id = %s ORDER BY created_at DESC LIMIT 1"
        latest_result_id = self.execute_query(latest_result_id_query, (user_id,), fetch='returning')

        if not latest_result_id:
            raise ValueError(f"No health_result found for user_id {user_id} to update.")

        sql = """
            UPDATE health_results SET
                naqr_bullying_experience = %(naqr_bullying_experience)s,
                naqr_bullying_actors = %(naqr_bullying_actors)s,
                naqr_bullying_perpetrators_detail = %(naqr_bullying_perpetrators_detail)s
            WHERE id = %(result_id)s
        """
        params = {**bullying_data, "result_id": latest_result_id}
        return self.execute_query(sql, params)

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

    def delete_health_result_by_id_admin(self, result_id: int) -> bool:
        """Menghapus entri health_result berdasarkan ID-nya. Hanya untuk admin."""
        query = "DELETE FROM health_results WHERE id = %s"
        try:
            rowcount = self.execute_query(query, (result_id,))
            return rowcount > 0  # True jika 1 baris terhapus
        except Exception as e:
            logging.error(f"Admin error deleting health result ID {result_id}: {e}")
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