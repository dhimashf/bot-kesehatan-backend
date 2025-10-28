import mysql.connector
from mysql.connector import pooling
from typing import Optional, Any
import threading

# Lock untuk memastikan inisialisasi pool thread-safe
_pool_lock = threading.Lock()
_connection_pool = None

class Database:
    """
    Kelas Database yang mengelola satu connection pool (singleton).
    Ini mencegah pembuatan pool baru pada setiap instansiasi.
    """
    def __init__(self, host: str = '127.0.0.1', user: str = 'root', password: str = '', database: str = 'kesehatan', pool_size: int = 5):
        global _connection_pool
        if _connection_pool is None:
            with _pool_lock:
                if _connection_pool is None:
                    _connection_pool = mysql.connector.pooling.MySQLConnectionPool(
                        pool_name="psikobot_pool",
                        pool_size=pool_size,
                        pool_reset_session=True,
                        host=host,
                        user=user,
                        password=password,
                        database=database
                    )
        self.pool = _connection_pool
        self.conn = None
        self.cursor = None

    def __enter__(self):
        """Memungkinkan penggunaan 'with Database() as db:'."""
        self.conn = self.pool.get_connection()
        self.cursor = self.conn.cursor(dictionary=True)
        return self # Mengembalikan instance itu sendiri

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Menutup cursor dan mengembalikan koneksi ke pool."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def execute_query(self, query, params=None, fetch=None):
        conn = self.pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            if fetch == 'one':
                return cursor.fetchone()
            elif fetch == 'all':
                return cursor.fetchall()
            else:
                conn.commit()
                return cursor.lastrowid
        finally:
            cursor.close()
            conn.close()

    def close(self):
        """Menutup seluruh connection pool. Panggil saat aplikasi berhenti."""
        global _connection_pool
        if _connection_pool is not None:
            # mysql-connector tidak punya metode close() untuk pool, jadi kita set ke None
            _connection_pool = None

    def create_user_account(self, email: str, hashed_password: str) -> int:
        """
        Creates a new user account with only email and hashed_password.
        The other biodata fields are left as default/NULL.
        """
        sql = """
        INSERT INTO users (email, hashed_password)
        VALUES (%s, %s)
        """
        values = (email, hashed_password)
        return self.execute_query(sql, values)

    def insert_or_update_profile(self, user_id: int, biodata: dict):
        """
        Inserts or updates a user's profile in the `profiles` table.
        """
        # Hapus field yang tidak ada di tabel 'profiles' sebelum insert/update
        biodata.pop('email', None)

        # Tentukan kolom yang valid untuk tabel profiles
        valid_columns = [
            'inisial', 'no_wa', 'usia', 'jenis_kelamin', 'pendidikan', 
            'lama_bekerja', 'status_pegawai', 'jabatan', 'jabatan_lain', 
            'unit_ruangan', 'status_perkawinan', 'status_kehamilan', 'jumlah_anak'
        ]
        
        # Filter biodata untuk hanya menyertakan kolom yang valid
        filtered_biodata = {k: v for k, v in biodata.items() if k in valid_columns}

        # Check if a profile already exists
        existing_profile = self.get_profile_by_user_id(user_id)

        if existing_profile:
            # Update existing profile
            set_clause = ", ".join([f"{key} = %s" for key in filtered_biodata.keys()])
            sql = f"UPDATE profiles SET {set_clause} WHERE user_id = %s"
            values = list(filtered_biodata.values()) + [user_id]
        else:
            # Insert new profile
            columns = ", ".join(['user_id'] + list(filtered_biodata.keys()))
            placeholders = ", ".join(['%s'] * (len(filtered_biodata) + 1))
            sql = f"INSERT INTO profiles ({columns}) VALUES ({placeholders})"
            values = [user_id] + list(filtered_biodata.values())

        return self.execute_query(sql, tuple(values))

    def insert_health_result(self, health_data: dict):
        sql = """
        INSERT INTO health_results (user_id, who5_total, gad7_total, mbi_emosional_total, mbi_sinis_total, mbi_pencapaian_total, naqr_pribadi_total, naqr_pekerjaan_total, naqr_intimidasi_total, k10_total)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            health_data['user_id'], health_data['who5_total'], health_data['gad7_total'], health_data['mbi_emosional_total'],
            health_data['mbi_sinis_total'], health_data['mbi_pencapaian_total'], health_data['naqr_pribadi_total'], health_data['naqr_pekerjaan_total'], health_data['naqr_intimidasi_total'], health_data['k10_total']
        )
        return self.execute_query(sql, values)

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

    def delete_health_result_by_id(self, result_id: int, user_id: int) -> bool:
        """Deletes a health result entry, ensuring the user owns it."""
        # We check user_id to make sure a user can't delete another user's results
        query = "DELETE FROM health_results WHERE id = %s AND user_id = %s"
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, (result_id, user_id))
        conn.commit()
        return cursor.rowcount > 0 # Returns True if a row was deleted, False otherwise

    def update_user_password(self, user_id: int, hashed_password: str) -> bool:
        """Updates the password for a given user ID."""
        query = "UPDATE users SET hashed_password = %s WHERE id = %s"
        try:
            # The execute_query returns lastrowid which is not useful for UPDATE.
            # We just need to know if it executed without error.
            self.execute_query(query, (hashed_password, user_id))
            return True
        except Exception as e:
            print(f"Error updating password for user {user_id}: {e}")
            return False
