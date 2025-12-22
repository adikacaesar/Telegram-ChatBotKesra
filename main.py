import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from datetime import time
import pytz # <-- Import Timezone

# UPDATE IMPORT
from core.config import TOKEN_TELEGRAM
from core.services import GoogleService
from handlers.main_handler import BotHandler

# Setup Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

if __name__ == '__main__':
    print("🤖 MENYALAKAN SISTEM + JADWAL OTOMATIS...")
    
    google_service = GoogleService()
    bot_logic = BotHandler(google_service)
    
    app = ApplicationBuilder().token(TOKEN_TELEGRAM).build()
    
    # --- DAFTARKAN HANDLER ---
    app.add_handler(CommandHandler('start', bot_logic.start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), bot_logic.proses_pesan))
    app.add_handler(MessageHandler(filters.PHOTO, bot_logic.handle_photo))
    
    # --- SETUP JADWAL OTOMATIS (CRON JOB) ---
    job_queue = app.job_queue
    
    # Tentukan Zona Waktu WIB
    wib = pytz.timezone('Asia/Jakarta')
    
    # Atur Jam Notifikasi (Contoh: Jam 07:00:00 WIB Setiap Hari)
    # Ganti '07' dengan jam lain jika mau test
    waktu_notif = time(hour=7, minute=0, second=0, tzinfo=wib)
    
    job_queue.run_daily(bot_logic.jalankan_notifikasi_pagi, waktu_notif)
    print(f"⏰ Notifikasi dijadwalkan setiap pukul {waktu_notif}")

    print("🚀 BOT KESRA SIAP BERAKSI!")
    app.run_polling()