from telegram import Update
from telegram.ext import ContextTypes
from core.config import TAB_PEGAWAI

class AuthMixin:
    """Logika untuk Login dan Logout"""

    async def proses_login(self, update, context, text, chat_id):
        # Jika user mengirim angka (ID Pegawai)
        if text.isdigit():
            id_input = int(text)
            
            # Cari di database pegawai
            found_user = None
            for p in self.db_pegawai:
                # Pastikan perbandingannya string vs string atau int vs int
                if str(p['ID_Pegawai']) == str(id_input):
                    found_user = p
                    break
            
            if found_user:
                # --- PERBAIKAN DI SINI ---
                # Kita harus simpan Jabatan ke dalam sesi
                # Ambil kolom 'Jabatan 1' dari Excel. Jika kosong, default ke string kosong.
                jabatan_user = str(found_user.get('Jabatan 1', '')).strip() 
                
                # Simpan ke memori sesi (RAM)
                self.sessions[chat_id] = {
                    'id': id_input,
                    'nama': found_user['Nama'],
                    'jabatan': jabatan_user, # <-- PENTING: Agar menu admin muncul
                    'state': 'MAIN_MENU'
                }
                
                # Simpan Chat ID ke Excel (Auto-Save fitur Checkpoint 2)
                self.google.simpan_chat_id(id_input, chat_id)
                
                # Tampilkan Menu Utama
                # Kita panggil fungsi tampilkan_menu_utama dari CommonMixin
                # Karena AuthMixin nanti digabung di MainHandler, kita bisa panggil self.tampilkan_menu_utama
                await self.tampilkan_menu_utama(update, found_user['Nama'])
                
            else:
                await update.message.reply_text("❌ ID tidak ditemukan. Coba lagi.")
        else:
            await update.message.reply_text(
                "🔒 **Anda belum login.**\n"
                "Silakan ketik **ID Pegawai** Anda (Angka) untuk masuk."
            )

    async def proses_logout(self, update, chat_id):
        if chat_id in self.sessions:
            nama = self.sessions[chat_id]['nama']
            del self.sessions[chat_id]
            await update.message.reply_text(f"👋 Sampai jumpa, {nama}!\nAnda berhasil logout.")