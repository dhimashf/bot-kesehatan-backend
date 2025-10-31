import logging
import os
import sys
import httpx
from enum import Enum, auto
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler, ExtBot, Defaults

from common.config.settings import settings
from core.services.openrouter_service import openrouter_service
from common.data.kitab_loader import kitab_loader
from core.services.profiling_service import profiling_service
from backend.services import web_auth_service, user_service
from core.services.database import Database


# --- State Management with Enums ---
# This makes the code more readable and less error-prone than using range().
class State(Enum):
    # Onboarding Flow
    ASK_ACCOUNT = auto()
    AWAIT_LOGIN_EMAIL = auto()
    REGISTER_EMAIL = auto()
    # Biodata Flow
    BIODATA_EMAIL = auto()
    BIODATA_INISIAL = auto()
    BIODATA_NOWA = auto()
    BIODATA_USIA = auto()
    BIODATA_JK = auto()
    BIODATA_PENDIDIKAN = auto()
    BIODATA_LAMA_BEKERJA = auto()
    BIODATA_STATUS_PEGAWAI = auto()
    BIODATA_JABATAN = auto()
    BIODATA_JABATAN_LAIN = auto()
    BIODATA_UNIT = auto()
    BIODATA_PERKAWINAN = auto()
    BIODATA_KEHAMILAN = auto()
    BIODATA_JUMLAH_ANAK = auto()
    # Questionnaire Flow
    WHO5 = auto()
    GAD7 = auto()
    MBI = auto()
    NAQR = auto()
    NAQR_Q81_TEXT = auto() # New state for NAQR Q81 text input
    NAQR_Q82_TEXT = auto() # New state for NAQR Q82 text input
    K10 = auto()

# List of biodata states in order, used for transitions
BIODATA_STATES_LIST = [
    State.BIODATA_EMAIL, State.BIODATA_INISIAL, State.BIODATA_NOWA, State.BIODATA_USIA,
    State.BIODATA_JK, State.BIODATA_PENDIDIKAN, State.BIODATA_LAMA_BEKERJA,
    State.BIODATA_STATUS_PEGAWAI, State.BIODATA_JABATAN, State.BIODATA_JABATAN_LAIN,
    State.BIODATA_UNIT, State.BIODATA_PERKAWINAN, State.BIODATA_KEHAMILAN,
    State.BIODATA_JUMLAH_ANAK
]

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.INFO)
logging.getLogger("telegram").setLevel(logging.INFO)

from core.services.database import Database

class PsikoBot:
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        profile = self.get_user_profile(context)
        
        # Jika pengguna sudah login dan profil lengkap, langsung berikan pesan sambutan.
        if profile.get('completed'):
            await update.message.reply_text("Selamat datang kembali! Anda sudah login dan profil Anda lengkap.")
            return

        # Untuk semua skenario lain (baru, belum login, belum selesai), tampilkan tombol "Mulai".
        # Ini menyederhanakan logika dan membuat alur lebih jelas bagi pengguna.
        keyboard = [[InlineKeyboardButton("▶️ Mulai", callback_data='start_conversation')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Selamat datang di Chatbot Psiko! Tekan 'Mulai' untuk login, mendaftar, atau melanjutkan sesi Anda.",
            reply_markup=reply_markup
        )

    async def start_conversation_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Titik masuk baru untuk ConversationHandler, dipicu oleh tombol 'Mulai'."""
        query = update.callback_query
        await query.answer()
        message = query.message

        profile = self.get_user_profile(context)

        # Skenario 1: Pengguna sudah login, biodata lengkap, tapi kuesioner belum.
        if profile.get('db_user_id') and profile.get('biodata_completed'):
            await message.edit_text("Anda sebelumnya belum menyelesaikan kuesioner. Mari kita lanjutkan.")
            return await self.start_profiling(update, context)

        # Skenario 2: Pengguna sudah login (punya akun), tapi biodata belum lengkap.
        if profile.get('db_user_id'):
            await message.edit_text("Akun Anda ditemukan, tetapi biodata belum lengkap. Mari kita lengkapi sekarang.")
            
            context.user_data['biodata'] = profile.get('biodata') or {}

            next_idx = 1
            for i, (field_name, _) in enumerate(profiling_service.BIODATA_FIELDS):
                if i == 0: continue
                if field_name not in context.user_data['biodata']:
                    next_idx = i
                    break
            else:
                profile['biodata_completed'] = True
                await message.reply_text("Biodata Anda sudah lengkap. Mari lanjutkan ke kuesioner.")
                return await self.start_profiling(update, context)

            context.user_data['state'] = BIODATA_STATES_LIST[next_idx]
            return await self.ask_next_biodata(message, context, next_idx)

        # Skenario 3: Pengguna benar-benar baru atau sudah logout.
        keyboard = [
            [InlineKeyboardButton("Sudah punya akun (Login)", callback_data='login')],
            [InlineKeyboardButton("Belum punya akun (Daftar)", callback_data='register')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.edit_text(
            "Selamat datang di Chatbot Psiko!\n\n"
            "Untuk melanjutkan, silakan login atau daftar jika Anda belum memiliki akun.",
            reply_markup=reply_markup
        )
        return State.ASK_ACCOUNT

    async def ask_account_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == 'login':
            await query.edit_message_text("Baik, silakan masukkan email Anda untuk login:")
            return State.AWAIT_LOGIN_EMAIL
        elif query.data == 'register':
            await query.edit_message_text(
                "Baik, mari kita mulai proses pendaftaran.\n\n"
                "Silakan masukkan Email Anda:"
            )
            return State.REGISTER_EMAIL

    async def register_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles new user registration by email."""
        email = update.message.text.strip()
        message = update.effective_message

        try:
            db = Database()
            try:
                # Coba buat akun pengguna baru tanpa password
                new_user = user_service.create_user_from_telegram(db, email)
            finally:
                db.close()

            # Inisialisasi profil dan simpan ID pengguna dari database
            profile = self.get_user_profile(context)
            profile['db_user_id'] = new_user['id']
            profile['biodata'] = {'email': email} # Simpan email di biodata

            logger.info(f"User account created/found with ID: {new_user['id']} for email: {email}")
            await message.reply_text("Terima kasih! Akun Anda telah dibuat. Mari kita lanjutkan dengan melengkapi biodata Anda.")
            
            # Mulai alur biodata dari 'inisial' (index 1)
            return await self.ask_next_biodata(message, context, 1)

        except Exception as e:
            logger.error(f"Failed to create account for {email}: {e}")
            await message.reply_text(f"Gagal membuat akun. Kemungkinan email sudah terdaftar atau terjadi kesalahan lain. Silakan coba lagi dengan /start.\n\nError: {e}")
            return ConversationHandler.END

    async def login_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles login by email without a password."""
        email = update.message.text

        db = Database()
        try:
            # Find user by email only
            user = web_auth_service.find_user_by_email(db, email=email)
        finally:
            db.close()

        if not user:
            await update.message.reply_text(
                "Login gagal. Email tidak ditemukan. Silakan coba lagi atau daftar akun baru dengan /start."
            )
            # Reset state
            return ConversationHandler.END

        # Login berhasil
        await update.message.reply_text("Login berhasil! Memuat profil Anda...")

        # Ambil profil lengkap dari DB
        db = Database()
        try:
            full_profile = web_auth_service.get_user_full_profile_by_id(db, user['id'])
        finally:
            db.close()

        # Set profile di context.user_data
        profile = self.get_user_profile(context)
        profile['db_user_id'] = user['id']
        profile['role'] = user['role'] # Simpan role pengguna
        # Pastikan biodata selalu berupa dict, bukan None
        profile['biodata'] = full_profile.get('biodata') or {}
        profile['biodata_completed'] = bool(full_profile.get('biodata'))

        health_results = full_profile.get('health_results')
        if health_results:
            profile['completed'] = True
            # Simpan seluruh hasil kesehatan dari DB ke dalam profile
            profile['health_results'] = health_results
            await update.message.reply_text(
                "Profil Anda telah dimuat. Anda dapat melanjutkan percakapan atau melihat ringkasan profil dengan /profile.\n\n"
            )
            return ConversationHandler.END
        elif profile['biodata_completed']:
            # Biodata ada, tapi kuesioner belum selesai
            profile['completed'] = False
            await update.message.reply_text(
                "Anda sebelumnya belum menyelesaikan kuesioner. Mari kita lanjutkan.")
            return await self.start_profiling(update, context)
        else:
            # Akun ada, tapi biodata belum lengkap
            await update.message.reply_text("Akun Anda ditemukan, tetapi biodata belum lengkap. Mari kita lengkapi sekarang.")
            
            # Salin biodata yang sudah ada dari profil ke context.user_data['biodata']
            # Ini penting agar biodata_handler bisa bekerja dengan data yang benar.
            context.user_data['biodata'] = profile.get('biodata') or {}

            # Cari pertanyaan biodata pertama yang belum diisi
            next_idx = 1 # Mulai dari 'inisial' (index 1)
            for i, (field_name, _) in enumerate(profiling_service.BIODATA_FIELDS):
                if i == 0: continue # Lewati email
                if field_name not in context.user_data['biodata']:
                    next_idx = i
                    break
            else: # Jika semua sudah terisi (kasus aneh, tapi untuk keamanan)
                profile['biodata_completed'] = True
                await update.message.reply_text("Biodata Anda sudah lengkap. Mari lanjutkan ke kuesioner.")
                return await self.start_profiling(update, context)

            # Dapatkan state yang sesuai untuk pertanyaan berikutnya
            next_state = BIODATA_STATES_LIST[next_idx]
            context.user_data['state'] = next_state # Set state for the next handler
            await self.ask_next_biodata(update.message, context, next_idx)
            return next_state

    async def biodata_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Mapping dari state ke informasi field
        state_map = {
            State.BIODATA_EMAIL: (0, 'email'),
            State.BIODATA_INISIAL: (1, 'inisial'),
            State.BIODATA_NOWA: (2, 'no_wa'),
            State.BIODATA_USIA: (3, 'usia'),
            State.BIODATA_JK: (4, 'jenis_kelamin'),
            State.BIODATA_PENDIDIKAN: (5, 'pendidikan'),
            State.BIODATA_LAMA_BEKERJA: (6, 'lama_bekerja'),
            State.BIODATA_STATUS_PEGAWAI: (7, 'status_pegawai'),
            State.BIODATA_JABATAN: (8, 'jabatan'),
            State.BIODATA_JABATAN_LAIN: (9, 'jabatan_lain'),
            State.BIODATA_UNIT: (10, 'unit_ruangan'),
            State.BIODATA_PERKAWINAN: (11, 'status_perkawinan'),
            State.BIODATA_KEHAMILAN: (12, 'status_kehamilan'),
            State.BIODATA_JUMLAH_ANAK: (13, 'jumlah_anak'),
        }

        current_state = context.user_data['state'] # State saat ini
        idx, field = state_map[current_state]

        query = update.callback_query
        user_input = ""
        message = update.effective_message

        if query:
            await query.answer()
            user_input = query.data
            # Edit pesan sebelumnya untuk menunjukkan pilihan
            await message.edit_text(f"✅ {profiling_service.BIODATA_FIELDS[idx][1].replace(':', '')}: {user_input}")
        elif update.message:
            user_input = update.message.text.strip()

        # Ambil profile dan pastikan 'biodata' di dalamnya ada
        profile = self.get_user_profile(context)
        profile['biodata'][field] = user_input

        next_idx = idx + 1
        
        # Skip 'jabatan_lain' jika tidak perlu
        if next_idx < len(profiling_service.BIODATA_FIELDS):
            next_field, _ = profiling_service.BIODATA_FIELDS[next_idx]
            if next_field == 'jabatan_lain' and profile['biodata'].get('jabatan') != 'Yang lain':
                next_idx += 1 # Langsung loncat ke pertanyaan setelahnya

        if next_idx >= len(profiling_service.BIODATA_FIELDS):
            # Semua biodata sudah terisi, simpan dan mulai profiling
            return await self.save_biodata(update, context)

        return await self.ask_next_biodata(message, context, next_idx)

    async def ask_next_biodata(self, message, context: ContextTypes.DEFAULT_TYPE, next_idx: int):
        """Mengajukan pertanyaan biodata berikutnya."""
        next_field, next_prompt = profiling_service.BIODATA_FIELDS[next_idx]

        keyboard = None
        if profiling_service.is_polling_field(next_field):
            keyboard = profiling_service.get_biodata_keyboard(next_field)

        await message.reply_text(next_prompt, reply_markup=keyboard)
        
        next_state = BIODATA_STATES_LIST[next_idx]
        context.user_data['state'] = next_state
        return next_state

    async def save_biodata(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        profile = self.get_user_profile(context)
        biodata = profile['biodata']

        # Hapus state dari user_data setelah selesai
        if 'state' in context.user_data:
            del context.user_data['state']

        try:
            # Validasi biodata sebelum menyimpan
            # Email divalidasi terpisah saat pembuatan akun
            profiling_service.validate_biodata({k: v for k, v in biodata.items() if k != 'email'})

            db_user_id = profile.get('db_user_id')
            if not db_user_id:
                raise Exception("User ID not found in context. Cannot save profile.")

            # Panggil service untuk menyimpan data.
            # Fungsi save_user_profile sudah cukup pintar untuk menangani data yang masuk.
            profiling_service.save_user_profile(db_user_id, biodata)
            logger.info(f"Biodata for user {user_id} saved to DB with ID {db_user_id}.")
        except ValueError as e:
            logger.error(f"Validation failed for user {user_id}: {e}")
            await update.effective_message.reply_text(
                f"Terjadi kesalahan validasi: {e}\nSilakan mulai lagi dengan /start."
            )
            # Reset biodata
            context.user_data['biodata'] = {}
            if 'profile' in context.user_data:
                del context.user_data['profile']
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"Service failed to save biodata for user {user_id}: {e}")
            await update.effective_message.reply_text(
                "Terjadi kesalahan saat menyimpan biodata Anda. Silakan coba lagi nanti dengan /start."
            )
            return ConversationHandler.END
            
        profile['biodata_completed'] = True
        profile['biodata'] = biodata

        await update.effective_message.reply_text(
            "Terima kasih, biodata Anda telah tersimpan. " \
            "Selanjutnya tahap pengisian Kuesioner. " \
            "Kuesioner ini bertujuan untuk memahami pengalaman perawat di tempat kerja dan kondisi kesejahteraan psikologis. " \
            "Beberapa pertanyaan mungkin terkait dengan pengalaman interaksi dengan rekan kerja, atasan, maupun pasien. " \
            "Semua jawaban bersifat rahasia, hanya digunakan untuk kepentingan penelitian dan tidak akan memengaruhi pekerjaan Anda." \
            "Mohon isi semua pertanyaan dengan jujur sesuai pengalaman Anda." \
            "Contact Person: Wahyudi (+62 852-7186-9761)" \
            "",
            parse_mode='Markdown'
        )
        return await self.start_profiling(update, context)

    async def kuesioner_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Memulai alur kuesioner baru untuk pengguna yang sudah login."""
        profile = self.get_user_profile(context)
        if not profile.get('db_user_id'):
            await update.message.reply_text("Anda harus login terlebih dahulu. Silakan gunakan /start untuk login atau mendaftar.")
            return
        
        if not profile.get('biodata_completed'):
            await update.message.reply_text("Anda harus melengkapi biodata terlebih dahulu sebelum mengisi kuesioner. Silakan gunakan /start.")
            return

        await update.message.reply_text("Baik, mari kita mulai sesi kuesioner yang baru untuk melihat perkembangan Anda.")
        # Langsung memulai kuesioner pertama
        return await self.start_profiling(update, context)

    async def start_profiling(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Memulai kuesioner pertama (WHO-5)"""
        profile = self.get_user_profile(context)
        profile["who5_scores"] = []
        return await self.ask_who5_question(update, context, 0)

    async def ask_mbi_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, idx: int):
        """Tampilkan pertanyaan MBI ke user. Mengedit pesan jika dari callback, mengirim baru jika tidak."""
        question = profiling_service.get_mbi_question(idx)
        keyboard = profiling_service.get_mbi_keyboard()
        
        if update.callback_query:
            await update.callback_query.message.reply_text(question, reply_markup=keyboard, parse_mode='Markdown') # Kirim sebagai pesan baru
        else:
            await update.effective_message.reply_text(question, reply_markup=keyboard, parse_mode='Markdown')
            
        context.user_data['current_question'] = {'text': profiling_service.mbi_questions[idx], 'options': profiling_service.mbi_options}

        return State.MBI

    async def set_bot_commands(self, application: Application):
        """Mengatur daftar perintah yang akan muncul di menu bot."""
        commands = [
            BotCommand("start", "Mulai atau login ke akun Anda"),
            BotCommand("profile", "Lihat biodata Anda"),
            BotCommand("kuesioner", "Isi ulang kuesioner perkembangan"),
            BotCommand("riwayatkuesioner", "Lihat riwayat hasil kuesioner"),
            BotCommand("logout", "Keluar dari sesi saat ini"),
            BotCommand("help", "Tampilkan pesan bantuan"),
            BotCommand("reset", "Reset profil sesi (tidak menghapus akun)"),
        ]
        await application.bot.set_my_commands(commands)

    def __init__(self):
        logger.info("Initializing Psiko Bot...")
        self.application = None
        self.job_queue = None
        self.initialized = False

    def setup(self):
        """Sets up the application, handlers, and job queue. Call this before run()."""
        if self.initialized:
            return

        # Tambahkan konfigurasi timeout untuk koneksi yang lebih stabil
        defaults = Defaults(
            parse_mode='Markdown'
        )
        self.application = (
            Application.builder()
            .token(settings.TELEGRAM_BOT_TOKEN)
            .defaults(defaults)
            .connect_timeout(20.0)
            .read_timeout(60.0)
            .post_init(self.set_bot_commands)
            .build()
        )
        
        # Perintah logout harus menjadi bagian dari handler agar bisa mengakhirinya
        logout_handler = CommandHandler("logout", self.logout_command)
        # Demikian pula dengan reset
        reset_handler = CommandHandler("reset", self.reset_profile)

        main_handler = ConversationHandler(
            entry_points=[
                # Titik masuk sekarang adalah CallbackQueryHandler dari tombol "Mulai"
                CallbackQueryHandler(self.start_conversation_callback, pattern='^start_conversation$'),
                CommandHandler("kuesioner", self.kuesioner_command) # Ini bisa tetap di sini untuk akses cepat
            ],
            states={
                # Onboarding states
                State.ASK_ACCOUNT: [CallbackQueryHandler(self.ask_account_handler)],
                State.REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.register_handler)],
                State.AWAIT_LOGIN_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.login_handler)],

                # Biodata states (all handled by biodata_handler)
                **{
                    state: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND, self.biodata_handler),
                        CallbackQueryHandler(self.biodata_handler)
                    ] for state in BIODATA_STATES_LIST if state != State.BIODATA_EMAIL
                },

                # Questionnaire states (each handled by its own callback)
                State.WHO5: [CallbackQueryHandler(self.who5_callback)],
                State.GAD7: [CallbackQueryHandler(self.gad7_callback)],
                State.MBI: [CallbackQueryHandler(self.mbi_callback)],
                State.NAQR: [CallbackQueryHandler(self.naqr_callback)],
                State.NAQR_Q81_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.naqr_q81_text_handler)],
                State.NAQR_Q82_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.naqr_q82_text_handler)],
                State.K10: [CallbackQueryHandler(self.k10_callback)],
            },
            fallbacks=[
                CommandHandler("start", self.start_command), # Izinkan /start untuk merestart percakapan
                CommandHandler("cancel", self.cancel_profiling), 
                logout_handler, 
                reset_handler
            ],
            # Mengikat status percakapan ke pesan, bukan hanya pengguna.
            # Konfigurasi ini adalah praktik terbaik untuk percakapan campuran.
            per_user=True,
            per_chat=True,
            per_message=False, # Penting: Setel ke False untuk mengizinkan handler selain CallbackQueryHandler
        )

        self.application.add_handler(main_handler)
        self.application.add_handler(CommandHandler("start", self.start_command)) # /start sekarang hanya menampilkan tombol
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("profile", self.show_profile))
        self.application.add_handler(CommandHandler("riwayatkuesioner", self.show_questionnaire_history))
        self.application.add_handler(reset_handler) # Tetap daftarkan di luar untuk akses global
        self.application.add_handler(logout_handler) # Tetap daftarkan di luar untuk akses global
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.initialized = True # Tandai bahwa setup sudah selesai
        logger.info("Psiko Bot initialized successfully")
    
    async def gad7_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle jawaban GAD-7 callback"""
        query = update.callback_query
        await query.answer()
        score = int(query.data)
        profile = self.get_user_profile(context)
        profile["gad7_scores"].append(score)

        idx = len(profile["gad7_scores"])
        
        # Tampilkan feedback jawaban di pesan yang sama
        feedback_text = self.format_answer_feedback(context.user_data.pop('current_question', {}), score)
        await query.edit_message_text(feedback_text, parse_mode='Markdown')
        if idx < 7:
            return await self.ask_gad7_question(update, context, idx)
        else:
            profile["k10_scores"] = [] # Mengarahkan ke K10 setelah GAD-7 selesai
            return await self.ask_k10_question(update, context, 0)

    async def mbi_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle jawaban MBI callback"""
        query = update.callback_query
        await query.answer()
        score = int(query.data)
        profile = self.get_user_profile(context)
        profile["mbi_scores"].append(score)

        idx = len(profile["mbi_scores"])
        
        # Tampilkan feedback jawaban di pesan yang sama
        feedback_text = self.format_answer_feedback(context.user_data.pop('current_question', {}), score)
        await query.edit_message_text(feedback_text, parse_mode='Markdown')
        if idx < 22:
            return await self.ask_mbi_question(update, context, idx)
        else:
            profile["naqr_scores"] = []
            return await self.ask_naqr_question(update, context, 0)
    
    def get_user_profile(self, context: ContextTypes.DEFAULT_TYPE) -> dict:
        """Get user profile from context or create a default one."""
        if "profile" not in context.user_data:
            context.user_data["profile"] = {
                "who5_scores": [],
                "gad7_scores": [],
                "mbi_scores": [],
                "naqr_q80_answer": None, # New
                "naqr_q81_answer": None, # New
                "naqr_q82_answer": None, # New
                "naqr_scores": [],
                "k10_scores": [],
                "completed": False,
                "biodata_completed": False,
                "db_user_id": None,
                "role": "user", # Default role
                "biodata": {}
            }
        return context.user_data["profile"]
    
    async def who5_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle jawaban WHO-5 callback"""
        query = update.callback_query
        await query.answer()
        score = int(query.data)
        profile = self.get_user_profile(context)
        profile["who5_scores"].append(score) # type: ignore

        idx = len(profile["who5_scores"])
        
        # Tampilkan feedback jawaban di pesan yang sama
        feedback_text = self.format_answer_feedback(context.user_data.pop('current_question', {}), score)
        await query.edit_message_text(feedback_text, parse_mode='Markdown')

        if idx < len(profiling_service.who5_questions):
            # Lanjut ke pertanyaan berikutnya
            return await self.ask_who5_question(update, context, idx)
        else:
            # Selesai WHO-5, mulai GAD-7
            profile["gad7_scores"] = []
            return await self.ask_gad7_question(update, context, 0)

    def format_answer_feedback(self, question_info: dict, score: int) -> str:
        """Memformat teks feedback setelah user menjawab."""
        question_text = question_info.get('text', 'Pertanyaan tidak ditemukan')
        options = question_info.get('options', [])
        
        answer_label = ""
        for label, opt_score in options:
            if opt_score == score:
                answer_label = label
                break
        
        return f"{question_text}\n\n*Jawaban Anda:* {answer_label} ({score})"

    async def ask_gad7_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, idx: int):
        """Tampilkan pertanyaan GAD-7 ke user. Mengedit pesan jika dari callback, mengirim baru jika tidak."""
        question = profiling_service.get_gad7_question(idx)
        keyboard = profiling_service.get_gad7_keyboard()
        
        if update.callback_query:
            await update.callback_query.message.reply_text(question, reply_markup=keyboard, parse_mode='Markdown') # Kirim sebagai pesan baru
        else:
            await update.effective_message.reply_text(question, reply_markup=keyboard, parse_mode='Markdown')

        context.user_data['current_question'] = {'text': profiling_service.gad7_questions[idx], 'options': profiling_service.gad7_options}

        return State.GAD7

    async def ask_who5_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, idx: int):
        """Tampilkan pertanyaan WHO-5 ke user. Mengedit pesan jika dari callback, mengirim baru jika tidak."""
        question = profiling_service.get_who5_question(idx)
        keyboard = profiling_service.get_who5_keyboard()
        
        if update.callback_query:
            await update.callback_query.message.reply_text(question, reply_markup=keyboard, parse_mode='Markdown') # Kirim sebagai pesan baru
        else:
            await update.effective_message.reply_text(question, reply_markup=keyboard, parse_mode='Markdown')

        context.user_data['current_question'] = {'text': profiling_service.who5_questions[idx], 'options': profiling_service.who5_options}

        return State.WHO5

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages with user profile context"""
        try:
            user_message = update.message.text
            user_id = update.message.from_user.id
            logger.info(f"Received message from user {user_id}: {user_message}")

            # Check if user has completed profiling
            profile = self.get_user_profile(context)
            # Admin dikecualikan dari keharusan mengisi kuesioner
            if not profile.get("completed") and profile.get("role") != "admin":
                await update.message.reply_text(
                    "Silakan selesaikan profiling terlebih dahulu dengan /start",
                    parse_mode='Markdown'
                )
                return

            # Show typing action
            await update.message.chat.send_action(action="typing")

            db_user_id = profile.get('db_user_id')
            if not db_user_id:
                await update.message.reply_text("Could not find your user profile. Please try /start again.")
                return

            # Gunakan host internal jika didefinisikan (untuk Docker), jika tidak, gunakan host aplikasi utama (untuk dev lokal)
            api_host = settings.INTERNAL_API_HOST or settings.APP_HOST
            api_url = f"http://{api_host}:{settings.APP_PORT}/api/v1/internal/chat/"

            # Atur timeout yang lebih lama (misal, 60 detik) untuk menunggu respons dari backend AI
            async with httpx.AsyncClient(timeout=60.0) as client:
                headers = {
                    "X-Internal-Token": settings.INTERNAL_BOT_TOKEN
                }
                response = await client.post(
                    api_url,
                    json={"user_id": db_user_id, "message": user_message},
                    headers=headers
                )

            if response.status_code != 200:
                logger.error(f"Error from chat API: {response.text}")
                await update.message.reply_text("Maaf, terjadi kesalahan saat memproses pesan Anda.")
                return

            answer = response.json().get("response", "Maaf, saya tidak mengerti.")

            await update.message.reply_text(answer, parse_mode='Markdown')
            logger.info(f"Sent response to user {user_id}")

        except Exception as e:
            logger.error(f"Error handling message: {str(e)}", exc_info=True)
            error_message = "Maaf, terjadi kesalahan. Silakan coba lagi nanti."
            await update.message.reply_text(error_message)

    async def ask_naqr_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, idx: int):
        """Tampilkan pertanyaan NAQ-R ke user. Mengedit pesan jika dari callback, mengirim baru jika tidak."""
        question = profiling_service.get_naqr_question(idx)
        keyboard = profiling_service.get_naqr_keyboard_for_question(idx)

        # Tentukan pesan yang akan dikirim atau diedit
        target_message = update.callback_query.message if update.callback_query else update.message

        if keyboard: # Untuk pertanyaan dengan tombol
            if update.callback_query:
                await target_message.reply_text(question, reply_markup=keyboard, parse_mode='Markdown') # Kirim sebagai pesan baru
            else:
                await target_message.reply_text(question, reply_markup=keyboard, parse_mode='Markdown')
        else: # Untuk pertanyaan input teks (Q81, Q82)
            await target_message.reply_text(question, parse_mode='Markdown')
        # Simpan info pertanyaan untuk feedback, kecuali untuk pertanyaan teks
        if idx < len(profiling_service.naqr_questions) and keyboard:
            context.user_data['current_question'] = {'text': profiling_service.naqr_questions[idx], 'options': profiling_service.naqr_options}

        # Tentukan state berikutnya berdasarkan jenis pertanyaan
        if idx == 23:
            return State.NAQR_Q81_TEXT
        if idx == 24:
            return State.NAQR_Q82_TEXT
        context.user_data['current_question'] = {'text': profiling_service.naqr_questions[idx], 'options': profiling_service.naqr_options}

        return State.NAQR

    async def naqr_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle jawaban NAQ-R callback (for questions 0-22)"""
        query = update.callback_query
        await query.answer()
        score = int(query.data)
        profile = self.get_user_profile(context)
        
        current_naqr_idx = len(profile["naqr_scores"])

        # Store score for NAQR main questions (0-21) and Q80 (index 22)
        if current_naqr_idx < 23: # Questions 0-22 (main NAQR + Q80)
            profile["naqr_scores"].append(score)
            # Store Q80 answer separately for display in summary
            if current_naqr_idx == 22:
                # Find the label for the score from NAQR_BULLYING_EXPERIENCE_OPTIONS
                q80_label = next((label for label, val in profiling_service.NAQR_BULLYING_EXPERIENCE_OPTIONS if val == score), str(score))
                profile["naqr_q80_answer"] = q80_label
        # Tampilkan feedback jawaban di pesan yang sama
        feedback_text = self.format_answer_feedback(context.user_data.pop('current_question', {}), score)
        await query.edit_message_text(feedback_text, parse_mode='Markdown')
        next_question_idx = current_naqr_idx + 1
        if next_question_idx < len(profiling_service.naqr_questions):
            return await self.ask_naqr_question(update, context, next_question_idx)
        else:
            # All NAQR questions (including text ones) are done. Save results and end.
            return await self.save_naqr_results_and_end(update, context)

    async def naqr_q81_text_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text input for NAQR Question 81 (Who are the bullies?)"""
        user_input = update.message.text.strip()
        profile = self.get_user_profile(context)
        profile["naqr_q81_answer"] = user_input
        
        question_info = context.user_data.pop('current_question', {})
        feedback_text = f"{question_info.get('text', 'Pertanyaan tidak ditemukan')}\n\n*Jawaban Anda:* {user_input}"
        await update.message.reply_text(feedback_text, parse_mode='Markdown')

        # Move to the next question (Q82, index 24)
        return await self.ask_naqr_question(update, context, 24)

    async def naqr_q82_text_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text input for NAQR Question 82 (Number of bullies)"""
        user_input = update.message.text.strip()
        profile = self.get_user_profile(context)
        profile["naqr_q82_answer"] = user_input

        question_info = context.user_data.pop('current_question', {})
        feedback_text = f"{question_info.get('text', 'Pertanyaan tidak ditemukan')}\n\n*Jawaban Anda:* {user_input}"
        await update.message.reply_text(feedback_text, parse_mode='Markdown')

        # All NAQR questions are done. Save results and end.
        return await self.save_naqr_results_and_end(update, context)

    async def save_naqr_results_and_end(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Saves all questionnaire results to DB and ends the conversation."""
        user_id = update.effective_user.id
        profile = self.get_user_profile(context)

        # Calculate all questionnaire results
        total_who5, category_who5 = profiling_service.get_who5_result(profile["who5_scores"])
        total_gad7, category_gad7 = profiling_service.get_gad7_result(profile["gad7_scores"])
        total_k10, category_k10 = profiling_service.get_k10_result(profile["k10_scores"]) # K10 is now before MBI
        mbi_result = profiling_service.get_mbi_result(profile["mbi_scores"])
        
        # NAQR subscale totals only from the first 22 scores
        naqr_main_scores = profile["naqr_scores"][:22]
        naqr_result = profiling_service.get_naqr_result(naqr_main_scores)
        
        profile["completed"] = True

        # Simpan hasil profiling ke database
        if profile.get('db_user_id'):
            try:
                profiling_data = {
                    'user_id': profile['db_user_id'],
                    'who5_total': total_who5,
                    'gad7_total': total_gad7,
                    'k10_total': total_k10, # K10 is now before MBI
                    'mbi_emosional_total': mbi_result['emosional'][0],
                    'mbi_sinis_total': mbi_result['sinis'][0],
                    'mbi_pencapaian_total': mbi_result['pencapaian'][0],
                    'naqr_pribadi_total': naqr_result['pribadi'],
                    'naqr_pekerjaan_total': naqr_result['pekerjaan'],
                    'naqr_intimidasi_total': naqr_result['intimidasi'],
                }
                profiling_service.save_health_results(profiling_data)
                logger.info(f"Health results for DB user ID {profile['db_user_id']} saved.")
                # Update profile with saved data for consistency (only DB-saved fields)
                profile['health_results'] = [profiling_data]
            except Exception as e:
                logger.error(f"Service failed to save health results for DB user ID {profile['db_user_id']}: {e}")
        else:
            logger.warning(f"Cannot save health results for user {user_id}, db_user_id not found.")

        # Generate summary
        summary = (
            f"✨ Survey Selesai!\n\n"
            f"*WHO-5 WELL-BEING INDEX*\nSkor: {total_who5} dari 30\nKategori: *{category_who5}*\n\n"
            f"*GAD-7 (Generalized Anxiety Disorder)*\nSkor: {total_gad7} dari 21\nKategori: *{category_gad7}*\n\n"
            f"*Kessler (K10) Skala Gangguan Psikososial*\nSkor: {total_k10} dari 50\nKategori: *{category_k10}*\n\n"
            f"*Maslach Burnout Inventory (MBI)*\n"
            f"Kelelahan Emosional: {mbi_result['emosional'][0]} ({mbi_result['emosional'][1]})\n"
            f"Sikap Sinis: {mbi_result['sinis'][0]} ({mbi_result['sinis'][1]})\n"
            f"Pencapaian Pribadi: {mbi_result['pencapaian'][0]} ({mbi_result['pencapaian'][1]})\n"
            f"Total Skor: {mbi_result['total'][0]}\n"
            f"Kategori: *{mbi_result['total'][1]}*\n\n"
            f"*NAQ-R (Negative Acts Questionnaire-Revised)*\n"
            f"Perundungan Pribadi: {naqr_result['pribadi']}\n"
            f"Perundungan Pekerjaan: {naqr_result['pekerjaan']}\n"
            f"Intimidasi: {naqr_result['intimidasi']}\n"
            f"Total Skor: {naqr_result['total']} | Kategori: *{naqr_result['category']}*\n"
        )
        # Add Q80, Q81, Q82 answers to summary if available in profile
        if profile.get("naqr_q80_answer"):
            summary += f"\n*Q80:* {profile['naqr_q80_answer']}"
        if profile.get("naqr_q81_answer"):
            summary += f"\n*Q81:* {profile['naqr_q81_answer']}"
        if profile.get("naqr_q82_answer"):
            summary += f"\n*Q82:* {profile['naqr_q82_answer']}"

        summary += "\n\nSekarang Anda bisa bertanya tentang Psiko.\nKetik /help untuk melihat panduan lengkap."

        await (update.message or update.callback_query.message).reply_text(summary, parse_mode='Markdown')
        return ConversationHandler.END

    async def ask_k10_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, idx: int):
        """Tampilkan pertanyaan K10 ke user. Mengedit pesan jika dari callback, mengirim baru jika tidak."""
        question = profiling_service.get_k10_question(idx)
        keyboard = profiling_service.get_k10_keyboard()
        
        if update.callback_query:
            await update.callback_query.message.reply_text(question, reply_markup=keyboard, parse_mode='Markdown') # Kirim sebagai pesan baru
        else:
            await update.effective_message.reply_text(question, reply_markup=keyboard, parse_mode='Markdown')

        context.user_data['current_question'] = {'text': profiling_service.k10_questions[idx], 'options': profiling_service.k10_options}

        return State.K10

    async def k10_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle jawaban K10 callback"""
        query = update.callback_query
        await query.answer()
        user_id = update.effective_user.id
        score = int(query.data)
        profile = self.get_user_profile(context)
        profile["k10_scores"].append(score)

        idx = len(profile["k10_scores"])        
        # Tampilkan feedback jawaban di pesan yang sama
        feedback_text = self.format_answer_feedback(context.user_data.pop('current_question', {}), score)
        await query.edit_message_text(feedback_text, parse_mode='Markdown')
        
        if idx < 10:
            # Lanjut ke pertanyaan berikutnya
            return await self.ask_k10_question(update, context, idx)
        else:
            # Selesai K10, mulai MBI
            profile["mbi_scores"] = []
            return await self.ask_mbi_question(update, context, 0)
    
    def _format_profile_summary(self, profile: dict) -> str:
        """Helper function to format the profile summary text."""
        hr_list = profile.get("health_results", [])
        if not hr_list or not isinstance(hr_list, list):
            return "Data hasil kuesioner tidak ditemukan atau formatnya salah."
        
        # Buat string untuk setiap entri riwayat
        history_texts = []
        for i, hr in enumerate(hr_list):
            total_who5 = hr.get('who5_total', 0)
            category_who5 = profiling_service.get_who5_category_from_total(total_who5)
            total_gad7 = hr.get('gad7_total', 0)
            category_gad7 = profiling_service.get_gad7_category_from_total(total_gad7)
            total_k10 = hr.get('k10_total', 0)
            category_k10 = profiling_service.get_k10_category_from_total(total_k10)
            
            mbi_result = profiling_service.get_mbi_result_from_totals(hr)
            naqr_result = profiling_service.get_naqr_result_from_totals(hr)
            
            # Ambil tanggal dari data, jika ada. Format agar lebih mudah dibaca.
            created_at_str = hr.get('created_at', 'Tanggal tidak diketahui')
            if isinstance(created_at_str, str) and len(created_at_str) > 10:
                created_at_str = created_at_str[:10] # Ambil YYYY-MM-DD

            entry_text = f" riwayat *{i+1}* (Tanggal: {created_at_str})\n" \
                         f"----------------------------------\n" \
                         f"*WHO-5 WELL-BEING INDEX*\nSkor: {total_who5} dari 30 | Kategori: *{category_who5}*\n\n" \
                         f"*GAD-7 (Generalized Anxiety Disorder)*\nSkor: {total_gad7} dari 21 | Kategori: *{category_gad7}*\n\n" \
                         f"*Kessler (K10) Skala Gangguan Psikososial*\nSkor: {total_k10} dari 50 | Kategori: *{category_k10}*\n\n" \
                         f"*Maslach Burnout Inventory (MBI)*\n{mbi_result}\n\n" \
                         f"*NAQ-R (Negative Acts Questionnaire-Revised)*\n{naqr_result}"
            history_texts.append(entry_text)

        return f" riwayat Kuesioner Anda\n\n" + "\n\n---\n\n".join(history_texts)


    
    async def cancel_profiling(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel profiling process"""
        await update.message.reply_text("Profiling dibatalkan. Gunakan /start untuk memulai lagi.")
        return ConversationHandler.END
    
    async def show_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show WHO-5, GAD-7, MBI, NAQ-R & K10 profile"""
        """Hanya menampilkan biodata pengguna."""
        profile = self.get_user_profile(context)

        if not profile.get("biodata_completed"):
            await update.message.reply_text(
                "Anda belum mengisi biodata. Gunakan /start untuk memulai.",
                parse_mode='Markdown'
            )
            return

        biodata = profile.get('biodata', {})
        if not biodata:
            await update.message.reply_text("Data biodata tidak ditemukan. Silakan coba /start lagi.")
            return

        # Format biodata menjadi teks yang rapi
        biodata_text_lines = []
        for key, val in biodata.items():
            # Format khusus untuk kunci tertentu, dan format umum untuk sisanya
            formatted_key = key.replace('_', ' ').title()
            biodata_text_lines.append(f"*{formatted_key}:* {val}")

        profile_text = "👤 *BIODATA*\n\n" + "\n".join(biodata_text_lines)
        await update.message.reply_text(profile_text, parse_mode='Markdown')

    async def show_questionnaire_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Menampilkan riwayat hasil kuesioner pengguna."""
        profile = self.get_user_profile(context)

        if not profile.get("completed"):
            await update.message.reply_text( # type: ignore
                "Anda belum menyelesaikan kuesioner. Gunakan /start untuk memulai.",
                parse_mode='Markdown'
            )
            return

        profile_text = self._format_profile_summary(profile)
        await update.message.reply_text(profile_text, parse_mode='Markdown')
    
    async def reset_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reset user profile"""
        user_id = update.effective_user.id
        if 'profile' in context.user_data:
            # Note: This does not delete from the database, only from memory for the current session.
            del context.user_data['profile']
            logger.info(f"In-memory profile for user {user_id} has been reset.")

        await update.message.reply_text( # type: ignore
            "Profil Anda telah direset. Gunakan /start untuk membuat profil baru.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    async def logout_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Logs the user out by clearing session data."""
        user_id = update.effective_user.id
        if 'profile' in context.user_data:
            del context.user_data['profile']
            logger.info(f"User {user_id} logged out. Session data cleared.")
            await update.message.reply_text(
                "Anda telah berhasil logout. Sesi Anda telah dibersihkan.\n\n"
                "Gunakan /start untuk login kembali."
            )
        else:
            logger.info(f"User {user_id} tried to log out but was not logged in.")
            await update.message.reply_text("Anda saat ini tidak sedang login.")
        return ConversationHandler.END

    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
📖 Bantuan Chatbot Psiko

Perintah yang tersedia: 
• /start - Mulai & setup profil
• /profile - Lihat biodata Anda
• /kuesioner - Mengisi ulang kuesioner untuk melihat perkembangan
• /riwayatkuesioner - Lihat riwayat hasil kuesioner
• /logout - Keluar dari sesi saat ini
• /reset - Reset profil sesi (tidak menghapus akun)
• /help - Tampilkan pesan bantuan ini

        """
        await update.message.reply_text(help_message, parse_mode='Markdown') # type: ignore
    
    async def run_polling(self):
        """Runs the bot with polling in an async-friendly way."""
        if not self.initialized:
            self.setup() # Pastikan setup dijalankan jika belum

        logger.info("Starting Psiko Bot polling...")
        await self.application.initialize() # type: ignore
        await self.application.start() # type: ignore
        await self.application.updater.start_polling( # type: ignore
            allowed_updates=Update.ALL_TYPES, drop_pending_updates=True
        )

    async def stop_polling(self):
        """Stops the bot polling gracefully."""
        if self.initialized and self.application and self.application.updater:
            logger.info("Stopping Psiko Bot polling...")
            await self.application.updater.stop() # type: ignore
            await self.application.stop() # type: ignore
            await self.application.shutdown() # type: ignore


# Global instance
psikobot = PsikoBot()