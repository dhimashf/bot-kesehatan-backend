# State untuk setiap langkah biodata
BIODATA_EMAIL, BIODATA_INISIAL, BIODATA_NOWA, BIODATA_USIA, BIODATA_JK, BIODATA_PENDIDIKAN, BIODATA_LAMA_BEKERJA, BIODATA_STATUS_PEGAWAI, BIODATA_JABATAN, BIODATA_JABATAN_LAIN, BIODATA_UNIT, BIODATA_PERKAWINAN, BIODATA_KEHAMILAN, BIODATA_JUMLAH_ANAK = range(100, 114)

# Daftar state biodata secara berurutan, sesuai dengan BIODATA_FIELDS
BIODATA_STATES_LIST = [
    BIODATA_EMAIL, BIODATA_INISIAL, BIODATA_NOWA, BIODATA_USIA, BIODATA_JK, BIODATA_PENDIDIKAN,
    BIODATA_LAMA_BEKERJA, BIODATA_STATUS_PEGAWAI, BIODATA_JABATAN, BIODATA_JABATAN_LAIN,
    BIODATA_UNIT, BIODATA_PERKAWINAN, BIODATA_KEHAMILAN, BIODATA_JUMLAH_ANAK
]
# State untuk login & register
ASK_ACCOUNT, AWAIT_LOGIN_EMAIL, REGISTER_EMAIL = range(115, 118)

import logging
import os
import sys
import httpx
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler, ExtBot, Defaults

from common.config.settings import settings
from core.services.openrouter_service import openrouter_service
from common.data.kitab_loader import kitab_loader
from core.services.profiling_service import profiling_service
from backend.services import web_auth_service, user_service

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.INFO)
logging.getLogger("telegram").setLevel(logging.INFO)



# Conversation states
WHO5_Q1, WHO5_Q2, WHO5_Q3, WHO5_Q4, WHO5_Q5 = range(5)
GAD7_Q1, GAD7_Q2, GAD7_Q3, GAD7_Q4, GAD7_Q5, GAD7_Q6, GAD7_Q7 = range(5, 12)
MBI_Q1, MBI_Q2, MBI_Q3, MBI_Q4, MBI_Q5, MBI_Q6, MBI_Q7, MBI_Q8, MBI_Q9, MBI_Q10, MBI_Q11, MBI_Q12, MBI_Q13, MBI_Q14, MBI_Q15, MBI_Q16, MBI_Q17, MBI_Q18, MBI_Q19, MBI_Q20, MBI_Q21, MBI_Q22 = range(12, 34)
NAQR_Q1, NAQR_Q2, NAQR_Q3, NAQR_Q4, NAQR_Q5, NAQR_Q6, NAQR_Q7, NAQR_Q8, NAQR_Q9, NAQR_Q10, NAQR_Q11, NAQR_Q12, NAQR_Q13, NAQR_Q14, NAQR_Q15, NAQR_Q16, NAQR_Q17, NAQR_Q18, NAQR_Q19, NAQR_Q20, NAQR_Q21, NAQR_Q22 = range(34, 56)
K10_Q1, K10_Q2, K10_Q3, K10_Q4, K10_Q5, K10_Q6, K10_Q7, K10_Q8, K10_Q9, K10_Q10 = range(56, 66)

# State untuk menampung handler kuesioner
PROFILING_FLOW = 67

from core.services.database import Database

class PsikoBot:
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        profile = self.get_user_profile(context)

        # Skenario 1: Pengguna sudah login dan profil lengkap.
        if profile.get('completed'):
            await update.message.reply_text("Selamat datang kembali! Anda sudah login dan profil Anda lengkap. Silakan ajukan pertanyaan Anda.")
            return ConversationHandler.END

        # Skenario 2: Pengguna sudah login, biodata lengkap, tapi kuesioner belum.
        if profile.get('db_user_id') and profile.get('biodata_completed'):
            await update.message.reply_text(
                "Anda sebelumnya belum menyelesaikan kuesioner. Mari kita lanjutkan."
            )
            return await self.start_profiling(update, context)

        # Skenario 3: Pengguna sudah login (punya akun), tapi biodata belum lengkap.
        if profile.get('db_user_id'):
            await update.message.reply_text("Akun Anda ditemukan, tetapi biodata belum lengkap. Mari kita lengkapi sekarang.")
            
            # Initialize biodata if not present
            context.user_data['biodata'] = profile.get('biodata') or {}

            # Find the first missing biodata field
            next_idx = 1 # Start from 'inisial' (index 1)
            for i, (field_name, _) in enumerate(profiling_service.BIODATA_FIELDS):
                if i == 0: continue # Skip email
                if field_name not in context.user_data['biodata']:
                    next_idx = i
                    break
            else: # If all biodata fields are already filled (unlikely here, but for safety)
                profile['biodata_completed'] = True
                await update.message.reply_text("Biodata Anda sudah lengkap. Mari lanjutkan ke kuesioner.")
                return await self.start_profiling(update, context)

            context.user_data['state'] = BIODATA_STATES_LIST[next_idx]
            return await self.ask_next_biodata(update.message, context, next_idx)

        # Skenario 4: Pengguna benar-benar baru atau sudah logout.

        keyboard = [
            [InlineKeyboardButton("Sudah punya akun (Login)", callback_data='login')],
            [InlineKeyboardButton("Belum punya akun (Daftar)", callback_data='register')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Selamat datang di Chatbot Psiko!\n\n"
            "Untuk melanjutkan, silakan login atau daftar jika Anda belum memiliki akun.",
            reply_markup=reply_markup
        )
        return ASK_ACCOUNT

    async def ask_account_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == 'login':
            await query.edit_message_text("Baik, silakan masukkan email Anda untuk login:")
            return AWAIT_LOGIN_EMAIL
        elif query.data == 'register':
            await query.edit_message_text(
                "Baik, mari kita mulai proses pendaftaran.\n\n"
                "Silakan masukkan Email Anda:"
            )
            return REGISTER_EMAIL

    async def register_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles new user registration by email."""
        email = update.message.text.strip()
        message = update.effective_message

        try:
            # Coba buat akun pengguna baru tanpa password
            new_user = user_service.create_user_from_telegram(email)
            
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

        # Find user by email only
        user = web_auth_service.find_user_by_email(email=email)

        if not user:
            await update.message.reply_text(
                "Login gagal. Email tidak ditemukan. Silakan coba lagi atau daftar akun baru dengan /start."
            )
            # Reset state
            return ConversationHandler.END

        # Login berhasil
        await update.message.reply_text("Login berhasil! Memuat profil Anda...")

        # Ambil profil lengkap dari DB
        full_profile = web_auth_service.get_user_full_profile_by_id(user['id'])

        # Set profile di context.user_data
        profile = self.get_user_profile(context)
        profile['db_user_id'] = user['id']
        profile['biodata'] = full_profile.get('biodata', {})
        profile['biodata_completed'] = bool(full_profile.get('biodata'))

        health_results = full_profile.get('health_results')
        if health_results:
            profile['completed'] = True
            # Simpan seluruh hasil kesehatan dari DB ke dalam profile
            profile['health_results'] = health_results
            await update.message.reply_text(
                "Profil Anda telah dimuat. Anda dapat melanjutkan percakapan atau melihat ringkasan profil dengan /profile.\n\n"
                "Silakan ajukan pertanyaan Anda."
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
        # Index 0 (email) dilewati karena sudah ditangani di register_handler
        state_map = {
            BIODATA_EMAIL: (0, 'email'), # Meskipun email ditangani di register, ini untuk kelengkapan
            BIODATA_INISIAL: (1, 'inisial'), # index 1
            BIODATA_NOWA: (2, 'no_wa'),
            BIODATA_USIA: (3, 'usia'),
            BIODATA_JK: (4, 'jenis_kelamin'),
            BIODATA_PENDIDIKAN: (5, 'pendidikan'),
            BIODATA_LAMA_BEKERJA: (6, 'lama_bekerja'),
            BIODATA_STATUS_PEGAWAI: (7, 'status_pegawai'),
            BIODATA_JABATAN: (8, 'jabatan'),
            BIODATA_JABATAN_LAIN: (9, 'jabatan_lain'),
            BIODATA_UNIT: (10, 'unit_ruangan'),
            BIODATA_PERKAWINAN: (11, 'status_perkawinan'),
            BIODATA_KEHAMILAN: (12, 'status_kehamilan'),
            BIODATA_JUMLAH_ANAK: (13, 'jumlah_anak'),
        } # Note: some indices are skipped to match BIODATA_FIELDS

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

        context.user_data['biodata'][field] = user_input

        next_idx = idx + 1
        
        # Skip 'jabatan_lain' jika tidak perlu
        if next_idx < len(profiling_service.BIODATA_FIELDS):
            next_field, _ = profiling_service.BIODATA_FIELDS[next_idx]
            if next_field == 'jabatan_lain' and context.user_data['biodata'].get('jabatan') != 'Yang lain':
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
        biodata = context.user_data['biodata']

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
            "Terima kasih, biodata Anda telah tersimpan. Sekarang, mari kita mulai sesi kuesioner singkat.",
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
        """Tampilkan pertanyaan MBI ke user"""
        question = profiling_service.get_mbi_question(idx)
        keyboard = profiling_service.get_mbi_keyboard()
        current_message = update.message or update.callback_query.message
        await current_message.reply_text(question, reply_markup=keyboard, parse_mode='Markdown')
        return MBI_Q1 + idx

    async def set_bot_commands(self, application: Application):
        """Mengatur daftar perintah yang akan muncul di menu bot."""
        commands = [
            BotCommand("start", "Mulai atau login ke akun Anda"),
            BotCommand("kuesioner", "Isi ulang kuesioner perkembangan"),
            BotCommand("profile", "Lihat ringkasan profil dan hasil"),
            BotCommand("logout", "Keluar dari sesi saat ini"),
            BotCommand("help", "Tampilkan pesan bantuan"),
            BotCommand("reset", "Reset profil sesi (tidak menghapus akun)"),
        ]
        await application.bot.set_my_commands(commands)

    def __init__(self):
        logger.info("Initializing Psiko Bot...")
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

        logger.info("Telegram application created")
        self._load_kitab_data()

        # Perintah logout harus menjadi bagian dari handler agar bisa mengakhirinya
        logout_handler = CommandHandler("logout", self.logout_command)
        # Demikian pula dengan reset
        reset_handler = CommandHandler("reset", self.reset_profile)

        main_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", self.start_command),
                CommandHandler("kuesioner", self.kuesioner_command)
            ],
            states={
                # --- GABUNGKAN SEMUA ALUR PROFILING AWAL (LOGIN, REGISTRASI, BIODATA) ---
                # Dengan menggabungkan semua state ini, transisi dari login_handler ke state biodata menjadi valid.
                **{
                    ASK_ACCOUNT: [CallbackQueryHandler(self.ask_account_handler)],
                    REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.register_handler)],
                    AWAIT_LOGIN_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.login_handler)],
                    **{state: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.biodata_handler), CallbackQueryHandler(self.biodata_handler)] for state in range(BIODATA_INISIAL, BIODATA_JUMLAH_ANAK + 1)}
                },

                # Handler untuk setiap kuesioner secara terpisah
                **{state: [CallbackQueryHandler(self.who5_callback)] 
                    for state in range(WHO5_Q1, WHO5_Q5 + 1)},
                **{state: [CallbackQueryHandler(self.gad7_callback)] 
                    for state in range(GAD7_Q1, GAD7_Q7 + 1)},
                **{state: [CallbackQueryHandler(self.mbi_callback)] 
                    for state in range(MBI_Q1, MBI_Q22 + 1)},
                **{state: [CallbackQueryHandler(self.naqr_callback)] 
                    for state in range(NAQR_Q1, NAQR_Q22 + 1)},
                **{state: [CallbackQueryHandler(self.k10_callback)] 
                    for state in range(K10_Q1, K10_Q10 + 1)},
            },
            fallbacks=[CommandHandler("cancel", self.cancel_profiling), logout_handler, reset_handler],
        )

        self.application.add_handler(main_handler)
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("profile", self.show_profile))
        self.application.add_handler(reset_handler) # Tetap daftarkan di luar untuk akses global
        self.application.add_handler(logout_handler) # Tetap daftarkan di luar untuk akses global
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.initialized = True
        logger.info("Psiko Bot initialized successfully")
    
    def _load_kitab_data(self):
        """Load kitab data dari PDF file dan build index di ChromaDB"""
        try:
            logger.info("Loading kitab data...")
            # Path is relative to the project root where main.py is executed
            kitab_path = os.path.join("common", "data", "kitab.pdf")
            
            loaded = False
            abs_path = os.path.abspath(kitab_path)
            logger.info(f"Trying path: {abs_path} (exists={os.path.exists(abs_path)})")
            if os.path.exists(abs_path):
                paragraphs = kitab_loader.load_pdf(abs_path)
                if paragraphs:
                    try:
                        from core.services.rag_service import rag_service
                        chunk_count = rag_service.build_index(abs_path)
                        logger.info(f"Successfully built index with {chunk_count} chunks from: {abs_path}")
                        loaded = True
                    except ImportError as e:
                        logger.warning(f"RAG service not available: {e}")
                        loaded = True
            if not loaded:
                logger.warning(f"⚠ Tidak menemukan file kitab.pdf di path: {abs_path}")
        except Exception as e:
            logger.error(f"Error loading kitab data: {str(e)}")
    async def gad7_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle jawaban GAD-7 callback"""
        query = update.callback_query
        await query.answer()
        score = int(query.data)
        profile = self.get_user_profile(context)
        profile["gad7_scores"].append(score)
        idx = len(profile["gad7_scores"])
        await query.edit_message_text(f"✅ Jawaban Anda: {score}", parse_mode='Markdown')
        if idx < 7:
            return await self.ask_gad7_question(update, context, idx)
        else:
            profile["mbi_scores"] = []
            return await self.ask_mbi_question(update, context, 0)

    async def mbi_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle jawaban MBI callback"""
        query = update.callback_query
        await query.answer()
        score = int(query.data)
        profile = self.get_user_profile(context)
        profile["mbi_scores"].append(score)
        idx = len(profile["mbi_scores"])
        await query.edit_message_text(f"✅ Jawaban Anda: {score}", parse_mode='Markdown')
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
                "naqr_scores": [],
                "k10_scores": [],
                "completed": False,
                "biodata_completed": False,
                "db_user_id": None,
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
        await query.edit_message_text(f"✅ Jawaban Anda: {score}", parse_mode='Markdown')
        if idx < len(profiling_service.who5_questions):
            # Lanjut ke pertanyaan berikutnya
            return await self.ask_who5_question(update, context, idx)
        else:
            # Selesai WHO-5, mulai GAD-7
            profile["gad7_scores"] = []
            return await self.ask_gad7_question(update, context, 0)

    async def ask_gad7_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, idx: int):
        """Tampilkan pertanyaan GAD-7 ke user"""
        question = profiling_service.get_gad7_question(idx)
        keyboard = profiling_service.get_gad7_keyboard()
        current_message = update.message or update.callback_query.message
        await current_message.reply_text(question, reply_markup=keyboard, parse_mode='Markdown')
        return GAD7_Q1 + idx

    async def ask_who5_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, idx: int):
        """Tampilkan pertanyaan WHO-5 ke user"""
        question = profiling_service.get_who5_question(idx)
        keyboard = profiling_service.get_who5_keyboard()
        current_message = update.message or update.callback_query.message
        await current_message.reply_text(question, reply_markup=keyboard, parse_mode='Markdown')
        return WHO5_Q1 + idx

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages with user profile context"""
        try:
            user_message = update.message.text
            user_id = update.message.from_user.id
            logger.info(f"Received message from user {user_id}: {user_message}")

            # Check if user has completed profiling
            profile = self.get_user_profile(context)
            if not profile.get("completed"):
                await update.message.reply_text( # type: ignore
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

            async with httpx.AsyncClient() as client:
                headers = {
                    "X-Internal-Token": settings.INTERNAL_BOT_TOKEN
                }
                response = await client.post(
                    f"http://{settings.APP_HOST}:{settings.APP_PORT}/api/v1/internal/chat/",
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
        """Tampilkan pertanyaan NAQ-R ke user"""
        question = profiling_service.get_naqr_question(idx)
        keyboard = profiling_service.get_naqr_keyboard()
        current_message = update.message or update.callback_query.message
        await current_message.reply_text(question, reply_markup=keyboard, parse_mode='Markdown')
        return NAQR_Q1 + idx

    async def naqr_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle jawaban NAQ-R callback"""
        query = update.callback_query
        await query.answer()
        score = int(query.data)
        profile = self.get_user_profile(context)
        profile["naqr_scores"].append(score)
        idx = len(profile["naqr_scores"])
        await query.edit_message_text(f"✅ Jawaban Anda: {score}", parse_mode='Markdown')
        if idx < 22:
            # Lanjut ke pertanyaan berikutnya
            return await self.ask_naqr_question(update, context, idx)
        else:
            # Selesai NAQ-R, mulai K10
            profile["k10_scores"] = []
            return await self.ask_k10_question(update, context, 0)

    async def ask_k10_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, idx: int):
        """Tampilkan pertanyaan K10 ke user"""
        question = profiling_service.get_k10_question(idx)
        keyboard = profiling_service.get_k10_keyboard()
        current_message = update.message or update.callback_query.message
        await current_message.reply_text(question, reply_markup=keyboard, parse_mode='Markdown')
        return K10_Q1 + idx

    async def k10_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle jawaban K10 callback"""
        query = update.callback_query
        await query.answer()
        user_id = update.effective_user.id
        score = int(query.data)
        profile = self.get_user_profile(context)
        profile["k10_scores"].append(score)
        idx = len(profile["k10_scores"])
        await query.edit_message_text(f"✅ Jawaban Anda: {score}", parse_mode='Markdown')
        if idx < 10:
            # Lanjut ke pertanyaan berikutnya
            return await self.ask_k10_question(update, context, idx)
        else:
            # Selesai K10, tampilkan hasil semua survey
            total_who5, category_who5 = profiling_service.get_who5_result(profile["who5_scores"])
            total_gad7, category_gad7 = profiling_service.get_gad7_result(profile["gad7_scores"])
            mbi_result = profiling_service.get_mbi_result(profile["mbi_scores"])
            naqr_result = profiling_service.get_naqr_result(profile["naqr_scores"])
            total_k10, category_k10 = profiling_service.get_k10_result(profile["k10_scores"])
            profile["completed"] = True

            # Simpan hasil profiling ke database
            if profile.get('db_user_id'):
                try:
                    profiling_data = {
                        'user_id': profile['db_user_id'],
                        'who5_total': total_who5,
                        'gad7_total': total_gad7,
                        'mbi_emosional_total': mbi_result['emosional'][0],
                        'mbi_sinis_total': mbi_result['sinis'][0],
                        'mbi_pencapaian_total': mbi_result['pencapaian'][0],
                        'naqr_pribadi_total': naqr_result['pribadi'],
                        'naqr_pekerjaan_total': naqr_result['pekerjaan'],
                        'naqr_intimidasi_total': naqr_result['intimidasi'],
                        'k10_total': total_k10
                    }
                    profiling_service.save_health_results(profiling_data)
                    logger.info(f"Health results for DB user ID {profile['db_user_id']} saved.")
                except Exception as e:
                    logger.error(f"Service failed to save health results for DB user ID {profile['db_user_id']}: {e}")
            else:
                logger.warning(f"Cannot save health results for user {user_id}, db_user_id not found.")


            summary = (
                f"✨ Survey Selesai!\n\n"
                f"*WHO-5 WELL-BEING INDEX*\nSkor: {total_who5} dari 30\nKategori: *{category_who5}*\n\n"
                f"*GAD-7 (Generalized Anxiety Disorder)*\nSkor: {total_gad7} dari 21\nKategori: *{category_gad7}*\n\n"
                f"*Maslach Burnout Inventory (MBI)*\n"
                f"Kelelahan Emosional: {mbi_result['emosional'][0]} ({mbi_result['emosional'][1]})\n"
                f"Sikap Sinis: {mbi_result['sinis'][0]} ({mbi_result['sinis'][1]})\n"
                f"Pencapaian Pribadi: {mbi_result['pencapaian'][0]} ({mbi_result['pencapaian'][1]})\n"
                f"Total Skor: {mbi_result['total'][0]} ({mbi_result['total'][1]})\n\n"
                f"*NAQ-R (Negative Acts Questionnaire-Revised)*\n"
                f"Perundungan Pribadi: {naqr_result['pribadi']}\n"
                f"Perundungan Pekerjaan: {naqr_result['pekerjaan']}\n"
                f"Intimidasi: {naqr_result['intimidasi']}\n"
                f"Total Skor: {naqr_result['total']}\n\n"
                f"*Kessler (K10) Skala Gangguan Psikososial*\nSkor: {total_k10} dari 50\nKategori: *{category_k10}*\n\n"
                "Sekarang Anda bisa bertanya tentang Psiko.\n"
                "Ketik /help untuk melihat panduan lengkap."
            )
            await query.message.reply_text(summary, parse_mode='Markdown')
            return ConversationHandler.END
    
    
    
    async def cancel_profiling(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel profiling process"""
        await update.message.reply_text("Profiling dibatalkan. Gunakan /start untuk memulai lagi.")
        return ConversationHandler.END
    
    async def show_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show WHO-5, GAD-7, MBI, NAQ-R & K10 profile"""
        profile = self.get_user_profile(context)

        if not profile.get("biodata_completed"):
            await update.message.reply_text( # type: ignore
                "Anda belum mengisi biodata. Gunakan /start untuk memulai.",
                parse_mode='Markdown'
            )
            return

        if not profile.get("completed"):
            await update.message.reply_text( # type: ignore
                "Anda belum menyelesaikan profiling. Gunakan /start untuk memulai.",
                parse_mode='Markdown'
            )
            return

        biodata_text = "\n".join([f"*{key.replace('_', ' ').title()}:* {val}" for key, val in profile.get('biodata', {}).items()]) # type: ignore

        # Cek apakah data berasal dari login (health_results) atau sesi kuesioner
        if profile.get("health_results"):
            # Data dari login (DB)
            # Ambil hasil terbaru dari daftar riwayat.
            # `isinstance` check menangani kasus di mana data mungkin bukan list.
            hr = profile["health_results"][0] if isinstance(profile["health_results"], list) and profile["health_results"] else profile["health_results"]
            if not hr: # Jika hr kosong setelah pengecekan
                return # Tidak bisa menampilkan profil
            total_who5, category_who5 = profiling_service.get_who5_result([hr['who5_total']])
            total_gad7, category_gad7 = profiling_service.get_gad7_result([hr['gad7_total']])
            total_k10, category_k10 = profiling_service.get_k10_result([hr['k10_total']])
            
            # Untuk MBI dan NAQR, kita tidak punya skor mentah, hanya total
            mbi_result = {
                'emosional': (hr['mbi_emosional_total'], profiling_service.get_mbi_category('emosional', hr['mbi_emosional_total'])),
                'sinis': (hr['mbi_sinis_total'], profiling_service.get_mbi_category('sinis', hr['mbi_sinis_total'])),
                'pencapaian': (hr['mbi_pencapaian_total'], profiling_service.get_mbi_category('pencapaian', hr['mbi_pencapaian_total'])),
                'total': (hr['mbi_emosional_total'] + hr['mbi_sinis_total'] + hr['mbi_pencapaian_total'], "N/A")
            }
            naqr_result = {
                'pribadi': hr['naqr_pribadi_total'],
                'pekerjaan': hr['naqr_pekerjaan_total'],
                'intimidasi': hr['naqr_intimidasi_total'],
                'total': hr['naqr_pribadi_total'] + hr['naqr_pekerjaan_total'] + hr['naqr_intimidasi_total']
            }
        else:
            # Data dari sesi kuesioner saat ini
            total_who5, category_who5 = profiling_service.get_who5_result(profile["who5_scores"])
            total_gad7, category_gad7 = profiling_service.get_gad7_result(profile["gad7_scores"])
            mbi_result = profiling_service.get_mbi_result(profile["mbi_scores"])
            naqr_result = profiling_service.get_naqr_result(profile["naqr_scores"])
            total_k10, category_k10 = profiling_service.get_k10_result(profile["k10_scores"])

        profile_text = (
            f"👤 Profil Anda\n\n"
            f"*BIODATA*\n{biodata_text}\n\n"
            f"*WHO-5 WELL-BEING INDEX*\nSkor: {total_who5} dari 30\nKategori: *{category_who5}*\n\n"
            f"*GAD-7 (Generalized Anxiety Disorder)*\nSkor: {total_gad7} dari 21\nKategori: *{category_gad7}*\n\n"
            f"*Maslach Burnout Inventory (MBI)*\n"
            f"Kelelahan Emosional: {mbi_result['emosional'][0]} ({mbi_result['emosional'][1]})\n"
            f"Sikap Sinis: {mbi_result['sinis'][0]} ({mbi_result['sinis'][1]})\n"
            f"Pencapaian Pribadi: {mbi_result['pencapaian'][0]} ({mbi_result['pencapaian'][1]})\n"
            f"Total Skor: {mbi_result['total'][0]} ({mbi_result['total'][1]})\n\n"
            f"*NAQ-R (Negative Acts Questionnaire-Revised)*\n"
            f"Perundungan Pribadi: {naqr_result['pribadi']}\n"
            f"Perundungan Pekerjaan: {naqr_result['pekerjaan']}\n"
            f"Intimidasi: {naqr_result['intimidasi']}\n"
            f"Total Skor: {naqr_result['total']}\n\n"
            f"*Kessler (K10) Skala Gangguan Psikososial*\nSkor: {total_k10} dari 50\nKategori: *{category_k10}*\n\n"
            "Gunakan /reset untuk mengatur ulang profil."
        )
        await update.message.reply_text(profile_text, parse_mode='Markdown') # type: ignore
    
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
• /help - Tampilkan bantuan
• /profile - Lihat profil Anda
• /kuesioner - Mengisi ulang kuesioner untuk melihat perkembangan
• /logout - Keluar dari sesi saat ini

Cara penggunaan:
Cukup ketik pertanyaan Psiko Anda, dan bot akan memberikan jawaban berdasarkan kitab referensi dengan mempertimbangkan profil Anda.

Contoh pertanyaan:
• Apa itu kesehatan mental ?
        """
        await update.message.reply_text(help_message, parse_mode='Markdown') # type: ignore
    
    def run(self):
        """Run the bot"""
        logger.info("Starting Psiko Bot polling...")
        
        self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )


# Global instance
psikobot = PsikoBot()

if __name__ == "__main__":
    psikobot.run()           
    allowed_updates=Update.ALL_TYPES,