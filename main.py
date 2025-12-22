import logging
from telegram.ext import ApplicationBuilder
from telegram.request import HTTPXRequest # <-- IMPORT BARU

# Import dari folder sendiri
from core.config import TOKEN_TELEGRAM
from core.services import GoogleService
from core.bot_setup import daftar_handlers, daftar_jobs
from handlers.main_handler import BotHandler

# Setup Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
# Kurangi noise log dari library networking biar gak pusing bacanya
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

if __name__ == '__main__':
    print("🤖 MENYALAKAN SISTEM (MODULAR)...")
    
    # 1. Siapkan Otak & Layanan
    google_service = GoogleService()
    bot_logic = BotHandler(google_service)
    
    # 2. Bangun Aplikasi Bot dengan SETTING KONEKSI KUAT
    # Kita perpanjang timeout jadi 20 detik (default cuma 5 detik)
    trequest = HTTPXRequest(
        connection_pool_size=8, 
        read_timeout=20.0, 
        write_timeout=20.0, 
        connect_timeout=20.0
    )
    
    app = ApplicationBuilder().token(TOKEN_TELEGRAM).request(trequest).build()
    
    # 3. Pasang Komponen
    daftar_handlers(app, bot_logic)
    daftar_jobs(app, bot_logic)
    
    # 4. Jalankan!
    print("🚀 BOT KESRA SIAP BERAKSI!")
    app.run_polling()