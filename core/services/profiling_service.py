# src/services/profiling_service.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# Biodata fields and options
# Disesuaikan dengan skema tabel `users` di database
# Field 'password' ada di sini untuk alur ConversationHandler, tapi tidak disimpan di tabel `profiles`.
BIODATA_FIELDS = [
    ("email", "Masukkan Email Anda:"),
    ("inisial", "Masukkan Inisial Nama Anda:"), # Dimulai dari index 2
    ("no_wa", "Masukkan Nomor WhatsApp Aktif:"),
    ("usia", "Masukkan Usia Anda (dalam tahun):"),
    ("jenis_kelamin", "Pilih Jenis Kelamin:"),
    ("pendidikan", "Pilih Pendidikan Terakhir:"),
    ("lama_bekerja", "Berapa lama Anda bekerja di RSUP? (angka dalam tahun):"),
    ("status_pegawai", "Pilih Status Kepegawaian:"),
    ("jabatan", "Pilih Jabatan Anda:"),
    ("jabatan_lain", "Jika jabatan Anda 'Yang lain', sebutkan:"), # Hanya ditanya jika perlu
    ("unit_ruangan", "Masukkan Unit/Ruangan tempat Anda bekerja:"),
    ("status_perkawinan", "Pilih Status Perkawinan:"),
    ("status_kehamilan", "Apakah Anda sedang hamil?"),
    ("jumlah_anak", "Masukkan Jumlah Anak (ketik '0' jika belum ada):")
]

BIODATA_OPTIONS = {
    "jenis_kelamin": [
        ("Laki-laki", "Laki-laki"),
        ("Perempuan", "Perempuan")
    ],
    "pendidikan": [
        ("D3 Keperawatan", "D3 Keperawatan"),
        ("Ners", "Ners"),
        ("Magister Keperawatan", "Magister Keperawatan"),
        ("Ners Spesialis", "Ners Spesialis")
    ],
    "status_pegawai": [
        ("ASN", "ASN"),
        ("Non ASN", "Non ASN"),
        ("Yang lain", "Yang lain")
    ],
    "jabatan": [
        ("Kepala Ruangan", "Kepala Ruangan"),
        ("Penanggung Jawab Mutu", "Penanggung Jawab Mutu"),
        ("PPJA", "PPJA"),
        ("Ketua tim/PJ shift", "Ketua tim/PJ shift"),
        ("Perawat Pelaksana", "Perawat Pelaksana"),
        ("Yang lain", "Yang lain")
    ],
    "status_perkawinan": [
        ("Belum Menikah", "Belum Menikah"),
        ("Menikah", "Menikah"),
        ("Cerai Mati", "Cerai Mati"),
        ("Cerai Hidup", "Cerai Hidup")
    ],
    "status_kehamilan": [
        ("Ya", "Ya"),
        ("Tidak", "Tidak")
    ]
}

# WHO-5
WHO5_QUESTIONS = [
    "1. Saya merasa ceria dan bersemangat",
    "2. Saya merasa tenang dan rileks",
    "3. Saya merasa aktif dan energik",
    "4. Saya bangun dengan perasaan segar dan cukup istirahat",
    "5. Kehidupan sehari-hari saya dipenuhi dengan hal-hal yang menarik minat saya"
]
WHO5_LIKERT_OPTIONS = [
    ("Setiap Saat", 6),
    ("Sering Sekali", 5),
    ("Sering", 4),
    ("Cukup Sering", 3),
    ("Kadang-Kadang", 2),
    ("Tidak Pernah", 1)
]
WHO5_CATEGORY = [
    (11, "Gejala Depresi Berat"),
    (13, "Gejala Depresi Sedang"),
    (15, "Gejala Depresi Ringan"),
    (30, "Tidak ada gejala Depresi")
]

# GAD-7
GAD7_QUESTIONS = [
    "1. Merasa gelisah, cemas atau amat tegang",
    "2. Tidak mampu menghentikan atau mengendalikan rasa khawatir",
    "3. Terlalu mengkhawatirkan berbagai hal",
    "4. Sulit untuk santai",
    "5. Sangat gelisah sehingga sulit untuk duduk diam",
    "6. Menjadi mudah jengkel atau lekas marah",
    "7. Merasa takut seolah-olah sesuatu yang mengerikan mungkin terjadi"
]
GAD7_LIKERT_OPTIONS = [
    ("Sama sekali tidak", 0),
    ("Beberapa hari", 1),
    ("Lebih dari setengah hari", 2),
    ("Hampir setiap hari", 3)
]
GAD7_CATEGORY = [
    (4, "Kecemasan Minimal"),
    (9, "Kecemasan Ringan"),
    (14, "Kecemasan Sedang"),
    (21, "Kecemasan Berat")
]

MBI_QUESTIONS = [
    # Kelelahan Emosional (1-9)
    "1. Saya merasa emosi saya terkuras karena pekerjaan",
    "2. Menghadapi dan bekerja secara langsung dnegan orang menyebabkan saya stres",
    "3. Saya merasa seakan-akan hidup dan karir saya tidak akan berubah",
    "4. Pekerjaan sebagai pemberi jasa membuat saya merasa frustasi",
    "5. Saya merasa bekerja terlampau keras dalam pekerjaan saya",
    "6. Menghadapi orang/klien dan bekerja untuk mereka seharian penuh membuat saya 'tertekan'",
    "7. Saya merasa jenuh dan 'burnout' karena pekerjaan saya",
    "8. Saya merasa lesu ketika bangun pagi karena harus menjalani hari di tempat kerja untuk menghadapi klien",
    "9. Saya merasakan kelelahan fisik yang amat sangat di akhir hari kerja",
    # Sikap Sinis (10-14)
    "10. Saya merasa bahwa saya memperlakukan beberapa klien seolah merka objek impersonal",
    "11. Saya merasa para pengguna menyalahkan saya atas masalah-masalah yang mereka alami",
    "12. Saya benar-benar tidak peduli pada apa yang terjadi terhadap klien saya",
    "13. Saya menjadi semakin 'kaku' terhadap orang lain sejak saya mendapatkan pekerjaan ini",
    "14. Saya khawatir pekerjaan ini membuat saya 'dingin' secara emosional",
    # Pencapaian Pribadi (15-22)
    "15. Saya telah mendapatkan dan mengalami banyak hal yang berharga dalam pekerjaan ini",
    "16. Saya merasa sangat bersemangat dalam melakukan pekerjaan saya",
    "17. Saya dengan mudah dapat memahami bagimana perasaan klien",
    "18. Saya dapat bertindak secara efektif ketika klien menghadapi suatu masalah",
    "19. Saya menghadapi masalah-masalah emosional dalam pekerjaan saya dengan tenang dan 'kepala dingin'",
    "20. Saya memberikan pengaruh positif terhadap kehidupan orang lain melalui pekerjaan saya",
    "21. Saya dengan mudah bisa menciptakan suasana yang santai / rileks dengan para klien",
    "22. Saya merasa gembira setelah melakukan tugas saya untuk para klien secara langsung"
]
MBI_LIKERT_OPTIONS = [
    ("Tidak pernah", 1),
    ("Beberapa kali dalam setahun", 2),
    ("Sekali dalam sebulan", 3),
    ("Beberapa Kali dalam sebulan", 4),
    ("Sekali dalam seminggu", 5),
    ("Beberapa kali dalam seminggu", 6),
    ("Setiap hari", 7)
]
MBI_SUBSCALES = {
    "emosional": list(range(0, 9)),
    "sinis": list(range(9, 14)),
    "pencapaian": list(range(14, 22))
}
MBI_CATEGORY = {
    "emosional": [(14, "Rendah"), (23, "Sedang"), (999, "Tinggi")],
    "sinis": [(3, "Rendah"), (8, "Sedang"), (999, "Tinggi")],
    "pencapaian": [(11, "Rendah"), (18, "Sedang"), (999, "Tinggi")],
    "total": [(32, "Rendah"), (49, "Sedang"), (999, "Tinggi")]
}

NAQR_QUESTIONS = [
    "1. Seseorang menahan informasi yang mempengaruhi ke kinerja Saya",
    "2. Saya dipermalukan atau ditertawakan karena hal yang berkaitan dengan pekerjaan saya",
    "3. Saya diperintahkan untuk melakukan pekerjaan di bawah tingkat kompetensi Saya",
    "4. Tanggung jawab utama Saya dihilangkan atau diganti dengan tugas yang lebih remeh/ tidak penting/ rendah/ tidak menyenangkan",
    "5. Ada yang menyebarkan gosip dan desas desus tentang saya",
    "6. Saya diabaikan atau dikucilkan (dianggap tidak ada) di lingkungan kerja saya",
    "7. Saya dihina atau menerima kata-kata kasar tentang diri saya (misalnya tentang kebiasaan dan latar belakang saya, sikap, atau kehidupan pribadi saya)",
    "8. Saya dibentak atau menjadi target kemarahan spontan (atau amukan spontan)",
    "9. Saya menerima perlakuan yang intimidatif seperti ditunjuk-tunjuk, pelanggaran ruang pribadi/privasi, didorong, dihambat/dihalangi saat berjalan",
    "10. Saya menerima kata-kata sindiran atau tanda-tanda dari rekan lain bahwa saya seharusnya mengundurkan diri dari pekerjaan saya",
    "11. Saya terus menerus diingatkan pada kesalahan dan kelalaian saya",
    "12. Saya diabaikan atau menerima reaksi yang tidak bersahabat ketika saya mendekati seseorang",
    "13. Saya terus menerus menerima kritikan terkait pekerjaan dan usaha saya",
    "14. Pendapat dan pandangan saya tidak didengar",
    "15. Saya menjadi korban lelucon orang-orang yang tidak cocok dengan saya",
    "16. Saya diberi tugas dengan target atau tenggat waktu yang tidak masuk akal",
    "17. Saya pernah dituduh berbuat salah atau ilegal tanpa bukti",
    "18. Saya diawasi secara berlebihan di tempat kerja saya",
    "19. Saya tidak diperbolehkan untuk mengambil apa yang menjadi hak saya di tempat kerja (misalnya cuti sakit, hak libur, biaya perjalanan)",
    "20. Saya menjadi target ejekan dan sindiran kasar (sarcasm)",
    "21. Saya diberi beban kerja yang tidak mungkin dapat saya kelola",
    "22. Saya menerima ancaman kekerasan atau pelecehan secara ﬁsik atau verbal/ ujaran (perkataan)"
]
NAQR_LIKERT_OPTIONS = [
    ("Tidak Pernah", 1),
    ("Kadang-kadang", 2),
    ("Setiap Bulan", 3),
    ("Setiap Minggu", 4),
    ("Setiap Hari", 5)
]
NAQR_SUBSCALES = {
    "pribadi": [1,4,5,6,8,9,11,14,16,19,21], # index 2,5,6,7,9,10,12,15,17,20,22 (1-based)
    "pekerjaan": [0,2,3,13,15,18,20], # index 1,3,4,14,16,19,21 (1-based)
    "intimidasi": [7,10,12,17] # index 8,11,13,18 (1-based)
}

K10_QUESTIONS = [
    "1. Merasa sangat lelah tanpa alasan yang kuat?",
    "2. Merasa gugup/cemas?",
    "3. Merasa sangat gugup/cemas sampai-sampai tidak ada sesuatupun yang bisa menenangkan Anda?",
    "4. Merasa putus asa/tidak ada harapan?",
    "5. Merasa gelisah atau resah?",
    "6. Merasa sangat gelisah sampai-sampai Anda tidak bisa duduk dengan tenang?",
    "7. Merasa tertekan?",
    "8. Merasa sangat tertekan sampai-sampai tidak ada yang dapat membuat Anda ceria/terhibur?",
    "9. Merasakan bahwa semua yang diinginkan membutuhkan usaha keras?",
    "10. Merasa tidak berguna?"
]
K10_LIKERT_OPTIONS = [
    ("Tidak Pernah", 1),
    ("Jarang", 2),
    ("Kadang-kadang", 3),
    ("Hampir setiap saat", 4),
    ("Setiap saat", 5)
]
K10_CATEGORY = [
    (15, "Distres rendah"),
    (21, "Distres sedang"),
    (29, "Distres tinggi"),
    (50, "Distres sangat tinggi")
]

from core.services.database import Database
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

# Konteks untuk hashing password, sekarang menggunakan Argon2
# bcrypt disimpan sebagai skema lama untuk kompatibilitas jika ada password lama
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        return False

def get_password_hash(password):
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Password hashing failed: {e}")
        raise

class ProfilingService:
    def analyze_stress(self, profile):
        """Analisis kemungkinan penyebab stres berdasarkan hasil survey"""
        reasons = []
        # WHO-5
        if profile.get("who5_scores"):
            total_who5, category_who5 = self.get_who5_result(profile["who5_scores"])
            if total_who5 <= 13:
                reasons.append("Skor WHO-5 Anda menunjukkan gejala depresi atau penurunan kesejahteraan.")
        # GAD-7
        if profile.get("gad7_scores"):
            total_gad7, category_gad7 = self.get_gad7_result(profile["gad7_scores"])
            if total_gad7 >= 10:
                reasons.append("Skor GAD-7 Anda menunjukkan kecemasan sedang atau berat.")
        # MBI
        if profile.get("mbi_scores"):
            mbi_result = self.get_mbi_result(profile["mbi_scores"])
            if mbi_result['emosional'][1] == "Tinggi":
                reasons.append("Kelelahan emosional Anda tinggi, ini bisa menjadi faktor stres.")
            if mbi_result['sinis'][1] == "Tinggi":
                reasons.append("Sikap sinis terhadap pekerjaan/lingkungan tinggi, bisa memicu stres.")
            if mbi_result['pencapaian'][1] == "Rendah":
                reasons.append("Perasaan pencapaian pribadi rendah, bisa berkontribusi pada stres.")
        # NAQ-R
        if profile.get("naqr_scores"):
            naqr_result = self.get_naqr_result(profile["naqr_scores"])
            if naqr_result['pribadi'] > 20 or naqr_result['intimidasi'] > 10:
                reasons.append("Ada indikasi perundungan atau intimidasi yang cukup tinggi.")
        # K10
        if profile.get("k10_scores"):
            total_k10, category_k10 = self.get_k10_result(profile["k10_scores"])
            if total_k10 >= 22:
                reasons.append(f"Skor K10 Anda menunjukkan distres psikososial {category_k10}.")
        if not reasons:
            reasons.append("Profil Anda tidak menunjukkan faktor stres yang sangat menonjol, namun faktor lain bisa berperan.")
        return "\n".join(reasons)
    def __init__(self):
        # Default: WHO-5
        self.who5_questions = WHO5_QUESTIONS
        self.who5_options = WHO5_LIKERT_OPTIONS
        self.who5_category = WHO5_CATEGORY
        # GAD-7
        self.gad7_questions = GAD7_QUESTIONS
        self.gad7_options = GAD7_LIKERT_OPTIONS
        self.gad7_category = GAD7_CATEGORY
        # MBI
        self.mbi_questions = MBI_QUESTIONS
        self.mbi_options = MBI_LIKERT_OPTIONS
        self.mbi_subscales = MBI_SUBSCALES
        self.mbi_category = MBI_CATEGORY
        # NAQ-R
        self.naqr_questions = NAQR_QUESTIONS
        self.naqr_options = NAQR_LIKERT_OPTIONS
        self.naqr_subscales = NAQR_SUBSCALES
        # K10
        self.k10_questions = K10_QUESTIONS
        self.k10_options = K10_LIKERT_OPTIONS
        self.k10_category = K10_CATEGORY
        # Biodata
        self.BIODATA_FIELDS = BIODATA_FIELDS
        self.BIODATA_OPTIONS = BIODATA_OPTIONS

    # WHO-5
    def get_who5_keyboard(self):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{label} ({score})", callback_data=str(score))] for label, score in self.who5_options
        ])

    def get_who5_question(self, idx):
        if 0 <= idx < len(self.who5_questions):
            return f"Selama 2 minggu terakhir, seberapa sering Anda mengalami perasaan berikut?\n{self.who5_questions[idx]}"
        return None

    def get_who5_result(self, scores):
        total = sum(scores)
        if total <= 11:
            cat = self.who5_category[0][1]
        elif total <= 13:
            cat = self.who5_category[1][1]
        elif total <= 15:
            cat = self.who5_category[2][1]
        else:
            cat = self.who5_category[3][1]
        return total, cat

    def get_who5_category_from_total(self, total_score: int) -> str:
        """Mendapatkan kategori WHO-5 dari total skor yang sudah dihitung."""
        if total_score <= 11:
            return self.who5_category[0][1]
        elif total_score <= 13:
            return self.who5_category[1][1]
        elif total_score <= 15:
            return self.who5_category[2][1]
        return self.who5_category[3][1]

    # GAD-7
    def get_gad7_keyboard(self):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{label} ({score})", callback_data=str(score))] for label, score in self.gad7_options
        ])

    def get_gad7_question(self, idx):
        if 0 <= idx < len(self.gad7_questions):
            return f"Selama 2 minggu terakhir, seberapa sering Anda terganggu oleh masalah berikut?\n{self.gad7_questions[idx]}"
        return None

    def get_gad7_result(self, scores):
        total = sum(scores)
        if total <= 4:
            cat = self.gad7_category[0][1]
        elif total <= 9:
            cat = self.gad7_category[1][1]
        elif total <= 14:
            cat = self.gad7_category[2][1]
        else:
            cat = self.gad7_category[3][1]
        return total, cat

    def get_gad7_category_from_total(self, total_score: int) -> str:
        """Mendapatkan kategori GAD-7 dari total skor yang sudah dihitung."""
        if total_score <= 4:
            return self.gad7_category[0][1]
        elif total_score <= 9:
            return self.gad7_category[1][1]
        elif total_score <= 14:
            return self.gad7_category[2][1]
        return self.gad7_category[3][1]
    
    def get_k10_category_from_total(self, total_score: int) -> str:
        """Mendapatkan kategori K10 dari total skor yang sudah dihitung."""
        for lim, label in self.k10_category:
            if total_score <= lim:
                return label
        return self.k10_category[-1][1]


    def get_biodata_fields(self):
        """Return list of biodata fields and prompts."""
        return self.BIODATA_FIELDS

    def get_biodata_keyboard(self, field):
        """Return InlineKeyboardMarkup for polling fields."""
        options = self.BIODATA_OPTIONS.get(field)
        if not options:
            return None
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(label, callback_data=value)] for label, value in options
        ])

    def is_polling_field(self, field):
        """Check if field should use polling."""
        return field in self.BIODATA_OPTIONS

    def validate_biodata(self, biodata: dict):
        """Comprehensive validation for biodata dictionary."""
        import re

        # Phone number validation
        no_wa = biodata.get("no_wa")
        # Pola regex yang lebih fleksibel untuk nomor Indonesia (08, 628, +628)
        # dengan total 10-15 digit.
        if not no_wa or not re.match(r"^(08|\+628|628)\d{8,15}$", no_wa.replace("-", "").replace(" ", "")):
            raise ValueError("Format nomor WhatsApp tidak valid. Contoh: 081234567890 atau +6281234567890.")

        # Age validation
        usia = biodata.get("usia")
        try:
            usia_int = int(usia) # type: ignore
            if not (18 <= usia_int <= 65): # type: ignore
                raise ValueError("Usia harus antara 18 dan 65 tahun.")
        except (ValueError, TypeError):
            raise ValueError("Usia harus berupa angka.")

        # Gender-specific validation
        if biodata.get("jenis_kelamin") == "Laki-laki" and biodata.get("status_kehamilan") == "Ya":
            raise ValueError("Laki-laki tidak bisa hamil.")

        return True

    def get_mbi_keyboard(self):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{label} ({score})", callback_data=str(score))] for label, score in self.mbi_options
        ])

    def get_mbi_question(self, idx):
        if 0 <= idx < len(self.mbi_questions):
            return f"Seberapa sering Anda merasakan hal-hal berikut?\n{self.mbi_questions[idx]}"
        return None

    def get_mbi_result(self, scores):
        # scores: list of 22 int
        emosional = sum([scores[i] for i in self.mbi_subscales["emosional"]])
        sinis = sum([scores[i] for i in self.mbi_subscales["sinis"]])
        pencapaian = sum([scores[i] for i in self.mbi_subscales["pencapaian"]])
        total = sum(scores)
        def cat(val, scale):
            for lim, label in self.mbi_category[scale]:
                if val <= lim:
                    return label
            return self.mbi_category[scale][-1][1]
        return {
            "emosional": (emosional, cat(emosional, "emosional")),
            "sinis": (sinis, cat(sinis, "sinis")),
            "pencapaian": (pencapaian, cat(pencapaian, "pencapaian")),
            "total": (total, cat(total, "total"))
        }

    def get_mbi_category(self, scale: str, value: int) -> str:
        """Mendapatkan label kategori untuk subskala MBI tertentu berdasarkan skor."""
        for lim, label in self.mbi_category[scale]:
            if value <= lim:
                return label
        return self.mbi_category[scale][-1][1]
    # NAQ-R

    def get_mbi_result_from_totals(self, health_result: dict) -> str:
        """Mendapatkan ringkasan MBI dari total skor yang sudah ada."""
        emosional_total = health_result.get('mbi_emosional_total', 0)
        sinis_total = health_result.get('mbi_sinis_total', 0)
        pencapaian_total = health_result.get('mbi_pencapaian_total', 0)
        
        emosional_cat = self.get_mbi_category('emosional', emosional_total)
        sinis_cat = self.get_mbi_category('sinis', sinis_total)
        pencapaian_cat = self.get_mbi_category('pencapaian', pencapaian_total)
        
        total_score = emosional_total + sinis_total + pencapaian_total
        
        return (
            f"Kelelahan Emosional: {emosional_total} ({emosional_cat})\n"
            f"Sikap Sinis: {sinis_total} ({sinis_cat})\n"
            f"Pencapaian Pribadi: {pencapaian_total} ({pencapaian_cat})\n"
            f"Total Skor: {total_score}"
        )

    def get_naqr_result_from_totals(self, health_result: dict) -> str:
        """Mendapatkan ringkasan NAQ-R dari total skor yang sudah ada."""
        pribadi = health_result.get('naqr_pribadi_total', 0)
        pekerjaan = health_result.get('naqr_pekerjaan_total', 0)
        intimidasi = health_result.get('naqr_intimidasi_total', 0)
        total = pribadi + pekerjaan + intimidasi
        return (
            f"Perundungan Pribadi: {pribadi}\n"
            f"Perundungan Pekerjaan: {pekerjaan}\n"
            f"Intimidasi: {intimidasi}\n"
            f"Total Skor: {total}"
        )

    def get_naqr_keyboard(self):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{label} ({score})", callback_data=str(score))] for label, score in self.naqr_options
        ])

    def get_naqr_question(self, idx):
        if 0 <= idx < len(self.naqr_questions):
            return f"Selama enam bulan terakhir, seberapa sering Anda mengalami tindakan negatif berikut di tempat kerja?\n{self.naqr_questions[idx]}"
        return None

    def get_naqr_result(self, scores):
        pribadi = sum([scores[i] for i in self.naqr_subscales["pribadi"]])
        pekerjaan = sum([scores[i] for i in self.naqr_subscales["pekerjaan"]])
        intimidasi = sum([scores[i] for i in self.naqr_subscales["intimidasi"]])
        total = sum(scores)
        return {
            "pribadi": pribadi,
            "pekerjaan": pekerjaan,
            "intimidasi": intimidasi,
            "total": total
        }

    # K10
    def get_k10_keyboard(self):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{label} ({score})", callback_data=str(score))] for label, score in self.k10_options
        ])

    def get_k10_question(self, idx):
        if 0 <= idx < len(self.k10_questions):
            return f"Selama 30 hari terakhir, seberapa seringkah Anda?\n{self.k10_questions[idx]}"
        return None

    def get_k10_result(self, scores):
        total = sum(scores)
        for lim, label in self.k10_category:
            if total <= lim:
                return total, label
        return total, self.k10_category[-1][1]
    
    def create_user_account(self, email: str, password: str) -> int:
        """
        Creates a new user account and returns the new user's ID.
        """
        try:
            db = Database()
            hashed_password = get_password_hash(password)
            return db.create_user_account(email, hashed_password)
        except Exception as e:
            raise e

    def save_user_profile(self, user_id: int, biodata: dict):
        """
        Saves or updates a user's profile (biodata) in the `profiles` table.
        """
        try:
            db = Database()
            # Buat salinan untuk menghindari modifikasi objek asli
            profile_data = biodata.copy()
            profile_data.setdefault('jabatan_lain', None)
            # The user_id is passed from the bot's context
            db.insert_or_update_profile(user_id, profile_data)
        except Exception as e:
            raise e

    def save_health_results(self, health_data: dict):
        """
        Saves the user's questionnaire results to the `health_results` table.
        """
        try:
            db = Database()
            db.insert_health_result(health_data)
        except Exception as e:
            # Di sini kita bisa log errornya, tapi biarkan bot yang menangani notifikasi ke user
            raise e

profiling_service = ProfilingService()
