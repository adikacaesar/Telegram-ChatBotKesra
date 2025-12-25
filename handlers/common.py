from telegram import Update
from telegram.ext import ContextTypes

class CommonMixin:
    """Khusus menangani Start & Menu UI"""

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user.first_name
        await update.message.reply_text(f"Halo {user}!\nSilakan ketik **ID Pegawai** untuk Login.")

    async def tampilkan_menu_utama(self, update, nama_user, pesan_tambahan=""):
        chat_id = update.message.chat_id
        
        # --- RESET STATE (PENTING AGAR TIDAK ERROR SAAT KEMBALI) ---
        if chat_id in self.sessions:
            self.sessions[chat_id]['state'] = 'MAIN_MENU'
            self.sessions[chat_id]['selected_rapat'] = None
            # Hapus sisa data admin jika ada agar bersih
            if 'temp_rapat' in self.sessions[chat_id]:
                del self.sessions[chat_id]['temp_rapat']
        
        # --- CEK JABATAN UNTUK MENU ADMIN ---
        user_session = self.sessions.get(chat_id, {})
        jabatan = user_session.get('jabatan', '').lower()
        
        # Logika: Apakah dia admin? (Kata kunci: kabag atau ketua)
        is_admin = 'kabag' in jabatan or 'ketua' in jabatan
        
        # --- SUSUN TAMPILAN MENU ---
        text = (f"{pesan_tambahan}\n\n" if pesan_tambahan else "")
        text += f"✅ Halo **{nama_user}**!\n"
        text += "1️⃣ Cek Jadwal\n"
        text += "2️⃣ Perbarui Status Jadwal\n"
        
        if is_admin:
            text += "3️⃣ Tambah Jadwal (Admin)\n"
            text += "4️⃣ Upload Surat Resmi (Admin)\n"
            text += "5️⃣ Konfigurasi Notifikasi (Admin)" # <-- TAMBAHAN DI SINI
            
        await update.message.reply_text(text)