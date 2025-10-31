# src/services/profiling_service.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# Biodata fields and options
# Disesuaikan dengan skema tabel `users` di database
# Field 'password' ada di sini untuk alur ConversationHandler, tapi tidak disimpan di tabel `profiles`.
BIODATA_FIELDS = [
    ("email", "1. Masukkan Email Anda:"),
    ("inisial", "2. Masukkan Inisial Nama Anda:"), # Dimulai dari index 2
    ("no_wa", "3. Masukkan Nomor WhatsApp Aktif: (contoh: 081923456789)"),
    ("usia", "4. Masukkan Usia Anda (dalam tahun):"),
    ("jenis_kelamin", "5. Pilih Jenis Kelamin:"),
    ("pendidikan", "6. Pilih Pendidikan Terakhir:"),
    ("lama_bekerja", "7. Berapa lama Anda bekerja di RSUP M Djamil? (angka dalam tahun):"),
    ("status_pegawai", "8. Pilih Status Kepegawaian:"),
    ("jabatan", "9. Pilih Jabatan Anda:"),
    ("jabatan_lain", "Jika jabatan Anda 'Yang lain', sebutkan:"), # Hanya ditanya jika perlu
    ("unit_ruangan", "10. Masukkan Unit/Ruangan tempat Anda bekerja:"),
    ("status_perkawinan", "11. Pilih Status Perkawinan:"),
    ("status_kehamilan", "12. Apakah Anda sedang hamil?"),
    ("jumlah_anak", "13. Masukkan Jumlah Anak (ketik '0' jika belum ada):")
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
    "14. Saya merasa ceria dan bersemangat",
    "15. Saya merasa tenang dan rileks",
    "16. Saya merasa aktif dan penuh semangat",
    "17. Saya bangun dengan perasaan segar dan cukup istirahat",
    "18. Kehidupan sehari-hari saya dipenuhi dengan hal-hal yang menarik minat saya"
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
    "19. Merasa gugup, cemas atau gelisah",
    "20. Tidak mampu menghentikan atau mengendalikan kekhawatiran",
    "21. Terlalu khawatir tentang berbagai hal ",
    "22. Kesulitan bersantai",
    "23. Menjadi begitu gelisah sehingga sulit untuk duduk diam ",
    "24. Menjadi mudah tersinggung",
    "25. Merasa takut seolah-olah sesuatu yang buruk akan terjadi"
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

K10_QUESTIONS = [
    "26. Merasa sangat lelah tanpa alasan yang kuat?",
    "27. Merasa gugup/cemas?",
    "28. Merasa sangat gugup/cemas sampai-sampai tidak ada sesuatupun yang bisa menenangkan Anda?",
    "29. Merasa putus asa/tidak ada harapan?",
    "30. Merasa gelisah atau resah?",
    "31. Merasa sangat gelisah sampai-sampai Anda tidak bisa duduk dengan tenang?",
    "32. Merasa tertekan?",
    "33. Merasa sangat tertekan sampai-sampai tidak ada yang dapat membuat Anda ceria/terhibur?",
    "34. Merasakan bahwa semua yang diinginkan membutuhkan usaha keras?",
    "35. Merasa tidak berguna?"
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

MBI_QUESTIONS = [
    # Kelelahan Emosional (1-9)
    "36. Saya merasa emosi saya terkuras karena pekerjaan",
    "37. Menghadapi dan bekerja secara langsung dnegan orang menyebabkan saya stres",
    "38. Saya merasa seakan akan hidup dan karir saya tidak akan berubah ",
    "39. Pekerjaan sebagai pemberi jasa membuat saya merasa frustasi ",
    "40. Saya merasa bekerja terlampau keras dalam pekerjaan saya",
    "41. Menghadapi orang/klien dan bekerja untuk mereka seharian penuh membuat saya 'tertekan'",
    "42. Saya merasa jenuh dan 'burnout' karena pekerjaan saya",
    "43. Saya merasa lesu ketika bangun pagi karena harus menjalani hari di tempat kerja untuk menghadapi klien",
    "44. Saya merasakan kelelahan fisik yang amat sangat di akhir hari kerja",
    # Pencapaian Pribadi (10-17)
    "45. Saya telah mendapatkan dan mengalami banyak hal yang berharga dalam pekerjaan ini",
    "46. Saya merasa sangat bersemangat dalam melakukan pekerjaan saya dan dalam menghadapi para klien saya",
    "47. Saya dengan mudah dapat memahami bagimana perasaan klien tentang hal hal ingin mereka penuhi dan mereka peroleh dari layanan yang saya berikan",
    "48. Saya bisa menjawab dan melayani klien saya dengan efektif",
    "49. Saya menghadapi masalah-masalah emosional dalam pekerjaan saya dengan tenang dan 'kepala dingin'",
    "50. Saya merasa memberikan pengaruh positif terhadap kehidupan orang lain melalui pekerjaan saya sebagai pemberi jasa",
    "51. Saya dengan mudah bisa menciptakan suasana yang santai/relaks dengan para klien",
    "52. Saya merasa gembira setelah melakukan tugas saya untuk para klien secara langsung",
    # Sikap Sinis (18-22)
    "53. Saya merasa bahwa saya memperlakukan beberapa klien seolah mereka objek impersonal",
    "54. Saya merasa para pengguna menyalahkan saya atas masalah-masalah yang mereka alami",
    "55. Saya benar-benar tidak peduli pada apa yang terjadi terhadap klien saya",
    "56. Saya menjadi semakin 'kaku' terhadap orang lain sejak saya bekerja sebagai pemberi jasa",
    "57. Saya khawatir pekerjaan ini membuat saya 'dingin' secara emosional",
]
MBI_LIKERT_OPTIONS = [
    ("Tidak pernah", 0),
    ("Beberapa kali dalam setahun", 1),
    ("Sekali dalam sebulan", 2),
    ("Beberapa Kali dalam sebulan", 3),
    ("Sekali dalam seminggu", 4),
    ("Beberapa kali dalam seminggu", 5),
    ("Setiap hari", 6)
]
MBI_SUBSCALES = {
    "emosional": list(range(0, 9)),
    "pencapaian": list(range(9, 17)),
    "sinis": list(range(17, 22))
}
MBI_CATEGORY = {
    "emosional": [(14, "Rendah"), (23, "Sedang"), (999, "Tinggi")],
    "pencapaian": [(11, "Rendah"), (18, "Sedang"), (999, "Tinggi")],
    "sinis": [(3, "Rendah"), (8, "Sedang"), (999, "Tinggi")],
    "total": [(32, "Rendah"), (49, "Sedang"), (999, "Tinggi")]
}

NAQR_QUESTIONS = [
    "58. Seseorang menahan informasi yang mempengaruhi ke kinerja Saya",
    "59. Saya dipermalukan atau ditertawakan karena hal yang berkaitan dengan pekerjaan saya",
    "60. Saya diperintahkan untuk melakukan pekerjaan di bawah tingkat kompetensi Saya",
    "61. Tanggung jawab utama Saya dihilangkan atau diganti dengan tugas yang lebih remeh/ tidak penting/ rendah/ tidak menyenangkan",
    "62. Ada yang menyebarkan gosip dan desas desus tentang saya",
    "63. Saya diabaikan atau dikucilkan (dianggap tidak ada) di lingkungan kerja saya",
    "64. Saya dihina atau menerima kata-kata kasar tentang diri saya (misalnya tentang kebiasaan dan latar belakang saya, sikap, atau kehidupan pribadi saya)",
    "65. Saya dibentak atau menjadi target kemarahan spontan (atau amukan spontan)",
    "66. Saya menerima perlakuan yang intimidatif seperti ditunjuk-tunjuk, pelanggaran ruang pribadi/privasi, didorong, dihambat/dihalangi saat berjalan",
    "67. Saya menerima kata-kata sindiran atau tanda-tanda dari rekan lain bahwa saya seharusnya mengundurkan diri dari pekerjaan saya",
    "68. Saya terus menerus diingatkan pada kesalahan dan kelalaian saya",
    "69. Saya diabaikan atau menerima reaksi yang tidak bersahabat ketika saya mendekati seseorang",
    "70. Saya terus menerus menerima kritikan terkait pekerjaan dan usaha saya",
    "71. Pendapat dan pandangan saya tidak didengar",
    "72. Saya menjadi korban lelucon orang-orang yang tidak cocok dengan saya",
    "73. Saya diberi tugas dengan target atau tenggat waktu yang tidak masuk akal",
    "74. Saya pernah dituduh berbuat salah atau ilegal tanpa bukti",
    "75. Saya diawasi secara berlebihan di tempat kerja saya",
    "76. Saya tidak diperbolehkan untuk mengambil apa yang menjadi hak saya di tempat kerja (misalnya cuti sakit, hak libur, biaya perjalanan)",
    "77. Saya menjadi target ejekan dan sindiran kasar (sarcasm)",
    "78. Saya diberi beban kerja yang tidak mungkin dapat saya kelola",
    "79. Saya menerima ancaman kekerasan atau pelecehan secara ﬁsik atau verbal/ ujaran (perkataan)",
    # Item tambahan (80–82)
    "80. Apakah Anda pernah mengalami perundungan di tempat kerja dalam enam bulan terakhir? (Gunakan definisi perundungan sebagaimana dijelaskan)",
    "81. Siapa saja yang melakukan perundungan terhadap Anda? (Boleh lebih dari satu)",
    "82. Sebutkan jumlah pelaku perundungan terhadap Anda (laki-laki dan perempuan)",
]
NAQR_LIKERT_OPTIONS = [
    ("Tidak Pernah", 1),
    ("Kadang-kadang", 2),
    ("Setiap Bulan", 3),
    ("Setiap Minggu", 4),
    ("Setiap Hari", 5)
]
NAQR_BULLYING_EXPERIENCE_OPTIONS = [
    ("Tidak", 1),
    ("Ya, tapi jarang", 2),
    ("Ya, kadang-kadang", 3),
    ("Ya, beberapa kali per minggu", 4),
    ("Ya, hampir tiap hari", 5)
]
# Opsi pelaku (item 81)
NAQR_BULLYING_ACTORS = [
    "Atasan langsung saya",
    "Atasan/manajer lain dalam organisasi",
    "Rekan kerja",
    "Bawahan",
    "Pelanggan/Pasien/Pelajar, dll",
    "Yang lain (tuliskan)"
]
NAQR_SUBSCALES = {
    "pribadi": [1,4,5,6,8,9,11,14,16,19,21], # index 2,5,6,7,9,10,12,15,17,20,22 (1-based)
    "pekerjaan": [0,2,3,13,15,18,20], # index 1,3,4,14,16,19,21 (1-based)
    "intimidasi": [7,10,12,17] # index 8,11,13,18 (1-based)
}

NAQR_CATEGORY = [
    (33, "Rendah / Tidak ada"),
    (55, "Sedang"),
    (77, "Tinggi"),
    (999, "Sangat tinggi") # Batas atas untuk skor >= 78
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
        self.NAQR_BULLYING_EXPERIENCE_OPTIONS = NAQR_BULLYING_EXPERIENCE_OPTIONS
        self.naqr_subscales = NAQR_SUBSCALES
        self.naqr_category = NAQR_CATEGORY
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
    def get_naqr_keyboard_for_question(self, idx):
        """
        Mengembalikan InlineKeyboardMarkup yang sesuai untuk pertanyaan NAQ-R berdasarkan indeks.
        Untuk pertanyaan teks, mengembalikan None.
        """
        if idx < 22: # Pertanyaan NAQ-R utama (0-21)
            return InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{label} ({score})", callback_data=str(score))] for label, score in self.naqr_options
            ])
        elif idx == 22: # Pertanyaan 80: Opsi pengalaman perundungan
            return InlineKeyboardMarkup([
                [InlineKeyboardButton(label, callback_data=str(score))] for label, score in NAQR_BULLYING_EXPERIENCE_OPTIONS
            ])
        elif idx == 23: # Pertanyaan 81: Input teks
            return None
        elif idx == 24: # Pertanyaan 82: Input teks
            return None
        return None

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
        total_score = pribadi + pekerjaan + intimidasi
        category = self.get_naqr_category_from_total(total_score)

        return (
            f"Perundungan Pribadi: {pribadi}\n"
            f"Perundungan Pekerjaan: {pekerjaan}\n" # K10 is now before MBI
            f"Intimidasi: {intimidasi}\n" # K10 is now before MBI
            f"Total Skor: {total_score}\n"
            f"Kategori: *{category}*"
        )

    def get_naqr_question(self, idx):
        if 0 <= idx < len(self.naqr_questions):
            if idx < 22: # Main NAQR questions (0-21)
                return f"Selama enam bulan terakhir, seberapa sering Anda mengalami tindakan negatif berikut di tempat kerja?\n{self.naqr_questions[idx]}"
            elif idx == 22: # Q80
                return self.naqr_questions[idx]
            elif idx == 23: # Q81
                return f"{self.naqr_questions[idx]}\n(Sebutkan nama/jabatan, pisahkan dengan koma jika lebih dari satu)"
            elif idx == 24: # Q82
                return f"{self.naqr_questions[idx]}\n(Contoh: 2 laki-laki, 1 perempuan)"
        return None

    def get_naqr_result(self, scores):
        pribadi = sum([scores[i] for i in self.naqr_subscales["pribadi"]])
        pekerjaan = sum([scores[i] for i in self.naqr_subscales["pekerjaan"]])
        intimidasi = sum([scores[i] for i in self.naqr_subscales["intimidasi"]])
        total = sum(scores)
        category = self.get_naqr_category_from_total(total)
        return {
            "pribadi": pribadi,
            "pekerjaan": pekerjaan,
            "intimidasi": intimidasi,
            "total": total,
            "category": category
        }

    def get_naqr_category_from_total(self, total_score: int) -> str:
        """Mendapatkan kategori NAQ-R dari total skor yang sudah dihitung."""
        if total_score <= 33:
            return self.naqr_category[0][1]
        elif total_score <= 55:
            return self.naqr_category[1][1]
        elif total_score <= 77:
            return self.naqr_category[2][1]
        return self.naqr_category[3][1] # >= 78

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
