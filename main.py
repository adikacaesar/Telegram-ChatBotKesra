import logging
from telegram.ext import ApplicationBuilder

# Import dari folder sendiri
from core.config import TOKEN_TELEGRAM
from core.services import GoogleService
from core.bot_setup import daftar_handlers, daftar_jobs # <-- Import file baru tadi
from handlers.main_handler import BotHandler

# Setup Logging (Biar ketahuan kalau ada error)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

if __name__ == '__main__':
    print("🤖 MENYALAKAN SISTEM (MODULAR)...")
    
    # 1. Siapkan Otak & Layanan
    google_service = GoogleService()
    bot_logic = BotHandler(google_service)
    
    # 2. Bangun Aplikasi Bot
    app = ApplicationBuilder().token(TOKEN_TELEGRAM).build()
    
    # 3. Pasang Komponen (Panggil dari core/bot_setup.py)
    daftar_handlers(app, bot_logic)
    daftar_jobs(app, bot_logic)
    
    # 4. Jalankan!
    print("🚀 BOT KESRA SIAP BERAKSI!")
    app.run_polling()