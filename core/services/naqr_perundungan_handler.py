import logging
from telegram import Update
from telegram.ext import (
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from core.services.profiling_service import profiling_service
from core.services.database import Database

logger = logging.getLogger(__name__)

# Definisikan states untuk conversation handler
ASK_Q80, HANDLE_Q80_ANSWER, ASK_Q81, ASK_Q82 = range(4)

async def start_naqr_perundungan(update: Update, context: CallbackContext) -> int:
    """Memulai kuesioner perundungan dengan menanyakan pertanyaan 80."""
    query = update.callback_query
    if query:
        await query.answer()

    question = profiling_service.get_naqr_perundungan_question(0)
    keyboard = profiling_service.get_naqr_perundungan_keyboard(0)

    # Inisialisasi penyimpanan jawaban
    context.user_data['naqr_perundungan_answers'] = {}

    message_text = "Terima kasih telah menyelesaikan kuesioner NAQ-R. Berikut adalah beberapa pertanyaan tambahan terkait perundungan."
    
    # Kirim pesan pengantar jika ini adalah awal dari handler
    if query and query.data == 'start_naqr_perundungan':
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message_text)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=question, reply_markup=keyboard)
    return HANDLE_Q80_ANSWER

async def handle_q80_answer(update: Update, context: CallbackContext) -> int:
    """Menangani jawaban dari pertanyaan 80 dan menentukan langkah selanjutnya."""
    query = update.callback_query
    await query.answer()

    answer = int(query.data)
    context.user_data['naqr_perundungan_answers']['naqr_bullying_experience'] = answer

    if answer == 1:  # Jawaban "Tidak"
        # Set jawaban lain ke None dan langsung simpan
        context.user_data['naqr_perundungan_answers']['naqr_bullying_actors'] = None
        context.user_data['naqr_perundungan_answers']['naqr_bullying_perpetrators_detail'] = None
        
        await save_bullying_data(update, context)
        return ConversationHandler.END
    else:
        # Lanjut ke pertanyaan 81
        question = profiling_service.get_naqr_perundungan_question(1)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=question)
        return ASK_Q81 # PERBAIKAN: Lanjut ke state untuk menunggu jawaban Q81

async def handle_q81_answer(update: Update, context: CallbackContext) -> int:
    """Menyimpan jawaban pertanyaan 81 (teks) dan lanjut ke pertanyaan 82."""
    answer = update.message.text
    context.user_data['naqr_perundungan_answers']['naqr_bullying_actors'] = answer

    question = profiling_service.get_naqr_perundungan_question(2)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=question)
    return ASK_Q82 # PERBAIKAN: Lanjut ke state untuk menunggu jawaban Q82

async def handle_q82_answer(update: Update, context: CallbackContext) -> int:
    """Menyimpan jawaban pertanyaan 82 (teks) dan mengakhiri kuesioner."""
    answer = update.message.text
    context.user_data['naqr_perundungan_answers']['naqr_bullying_perpetrators_detail'] = answer

    await save_bullying_data(update, context)
    return ConversationHandler.END

async def save_bullying_data(update: Update, context: CallbackContext):
    """Menyimpan data kuesioner perundungan ke database."""
    user_id = context.user_data.get('user_id')
    answers = context.user_data.get('naqr_perundungan_answers', {})

    if not user_id or not answers:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Terjadi kesalahan: Data pengguna tidak ditemukan untuk menyimpan hasil.")
        return

    try:
        db = Database()
        db.update_health_result_bullying(user_id, answers)
        logger.info(f"Successfully saved bullying data for user_id: {user_id}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Terima kasih, jawaban Anda telah disimpan.")
    except Exception as e:
        logger.error(f"Failed to save bullying data for user_id {user_id}: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Mohon maaf, terjadi kesalahan saat menyimpan jawaban Anda.")


naqr_perundungan_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_naqr_perundungan, pattern='^start_naqr_perundungan$')],
    states={
        HANDLE_Q80_ANSWER: [CallbackQueryHandler(handle_q80_answer)],
        # State ASK_Q81 menangani jawaban dari Q80, lalu menanyakan Q81
        # State ASK_Q82 menangani jawaban dari Q81, lalu menanyakan Q82
        ASK_Q81: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_q81_answer)],
        ASK_Q82: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_q82_answer)],
    },
    fallbacks=[],
)