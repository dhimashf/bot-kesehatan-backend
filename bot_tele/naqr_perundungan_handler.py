import logging
from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters, CommandHandler
from core.services.profiling_service import profiling_service
from enum import Enum, auto

# Impor State dari file states.py yang terpusat
from .states import State as MainState

logger = logging.getLogger(__name__)

# State lokal untuk handler ini
class State(Enum):
    HANDLE_Q80 = auto()
    HANDLE_Q81 = auto()
    HANDLE_Q82 = auto()

async def handle_q80_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Menangani jawaban dari pertanyaan 80 dan menentukan langkah selanjutnya."""
    query = update.callback_query
    await query.answer()

    answer = int(query.data)
    profile = context.user_data["profile"]
    profile['naqr_perundungan_answers']['naqr_bullying_experience'] = answer

    # Edit pesan untuk memberikan feedback
    # Menggunakan format yang sama dengan kuesioner lain
    q_info = {'text': profiling_service.naqr_perundungan_questions[0], 'options': profiling_service.NAQR_BULLYING_EXPERIENCE_OPTIONS}
    feedback_text = f"{q_info['text']}\n\n*Jawaban Anda:* {next(label for label, val in q_info['options'] if val == answer)}"
    await query.edit_message_text(feedback_text, parse_mode='Markdown')

    if answer == 1:  # Jawaban "Tidak"
        # Set jawaban lain ke None, simpan semua data, dan akhiri
        profile['naqr_perundungan_answers']['naqr_bullying_actors'] = None
        profile['naqr_perundungan_answers']['naqr_bullying_perpetrators_detail'] = None
        
        # Panggil fungsi save_naqr_results_and_end dari instance psikobot
        from .bot import psikobot
        return await psikobot.save_naqr_results_and_end(update, context)
    else:
        # Lanjut ke pertanyaan 81
        question = profiling_service.get_naqr_perundungan_question(1)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=question)
        return State.HANDLE_Q81

async def handle_q81_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Menyimpan jawaban q81 dan menanyakan q82."""
    answer = update.message.text
    profile = context.user_data["profile"]
    profile['naqr_perundungan_answers']['naqr_bullying_actors'] = answer

    question = profiling_service.get_naqr_perundungan_question(2)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=question)
    
    return State.HANDLE_Q82

async def handle_q82_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Menyimpan jawaban q82 dan menyelesaikan survei."""
    answer = update.message.text
    profile = context.user_data["profile"]
    profile['naqr_perundungan_answers']['naqr_bullying_perpetrators_detail'] = answer

    # Panggil fungsi save_naqr_results_and_end dari instance psikobot
    from .bot import psikobot
    return await psikobot.save_naqr_results_and_end(update, context)

async def cancel_perundungan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Membatalkan sub-kuesioner dan mengakhiri semuanya."""
    await update.message.reply_text("Kuesioner perundungan dibatalkan. Sesi diakhiri.")
    return ConversationHandler.END

naqr_perundungan_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(handle_q80_choice)],
    states={
        State.HANDLE_Q81: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_q81_answer)],
        State.HANDLE_Q82: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_q82_answer)],
    },
    fallbacks=[CommandHandler("cancel", cancel_perundungan)],
    # Ini penting agar state tidak bentrok dengan handler utama
    map_to_parent={
        # Ketika sub-handler ini selesai, kirim sinyal END ke handler utama
        # agar seluruh percakapan berakhir dengan benar.
        ConversationHandler.END: ConversationHandler.END,
    }
)