import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# UPDATE IMPORT
from core.config import TOKEN_TELEGRAM
from core.services import GoogleService
from handlers.main_handler import BotHandler

# Setup Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

if __name__ == '__main__':
    print("🤖 MENYALAKAN SISTEM (STRUKTUR RAPI)...")
    
    # ... (Isinya ke bawah SAMA PERSIS)
    google_service = GoogleService()
    bot_logic = BotHandler(google_service)
    
    app = ApplicationBuilder().token(TOKEN_TELEGRAM).build()
    
    app.add_handler(CommandHandler('start', bot_logic.start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), bot_logic.proses_pesan))
    app.add_handler(MessageHandler(filters.PHOTO, bot_logic.handle_photo))
    
    print("🚀 BOT KESRA SIAP BERAKSI!")
    app.run_polling()