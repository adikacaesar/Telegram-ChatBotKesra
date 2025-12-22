from telegram import Update
from telegram.ext import ContextTypes

class CommonMixin:
    """Khusus menangani Start & Menu UI"""

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user.first_name
        await update.message.reply_text(f"Halo {user}!\nSilakan ketik **ID Pegawai** untuk Login.")

    async def tampilkan_menu_utama(self, update, nama_user, pesan_tambahan=""):
        # Reset State ke Menu Utama
        chat_id = update.message.chat_id
        if chat_id in self.sessions:
            self.sessions[chat_id]['state'] = 'MAIN_MENU'
            self.sessions[chat_id]['selected_rapat'] = None
        
        text = (f"{pesan_tambahan}\n\n" if pesan_tambahan else "")
        # Menu disesuaikan dengan fitur Checkpoint 3 (Perbarui Status Jadwal)
        text += f"✅ Halo **{nama_user}**!\n1️⃣ Cek Jadwal\n2️⃣ Perbarui Status Jadwal"
        await update.message.reply_text(text)