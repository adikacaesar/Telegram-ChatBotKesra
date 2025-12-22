from core.config import TAB_PEGAWAI, TAB_RKM

class AuthMixin:
    """Bagian Otak untuk Login & Logout"""

    async def proses_login(self, update, context, text, chat_id):
        # Cek apakah input berupa Angka (ID)
        if text.isdigit():
            id_input = int(text)
            
            # Cari di Database Pegawai (yang sudah diload di main_handler)
            # Mencari baris pegawai yang ID-nya cocok dengan input
            pegawai = next((p for p in self.db_pegawai if p.get('ID_Pegawai') == id_input), None)
            
            if pegawai:
                # 1. BUAT SESI BARU (Simpan di RAM)
                # Ini agar bot tahu siapa yang sedang chat sekarang
                self.sessions[chat_id] = {
                    'nama': pegawai.get('Nama'), 
                    'state': 'MAIN_MENU', 
                    'temp_list': [], 
                    'selected_rapat': None
                }
                
                # === FITUR BARU: SIMPAN CHAT ID KE EXCEL ===
                # Memanggil fungsi di services.py untuk menulis Chat ID ke kolom spreadsheet
                # Agar jika bot mati, kita tetap punya data kontak pegawai ini untuk broadcast
                self.google.simpan_chat_id(id_input, chat_id)
                # ===========================================

                # Kirim pesan sukses login
                await update.message.reply_text(
                    f"✅ Halo **{pegawai.get('Nama')}**!\n\n"
                    "Menu Utama:\n"
                    "1️⃣ Cek Jadwal\n"
                    "2️⃣ Perbarui Status Jadwal"
                )
            else:
                await update.message.reply_text("❌ ID Salah / Tidak Ditemukan di Database Pegawai.")
        else:
            await update.message.reply_text("🔒 Anda belum login.\nSilakan ketik **ID Pegawai** Anda (Angka) untuk masuk.")

    async def proses_logout(self, update, chat_id):
        if chat_id in self.sessions:
            # Hapus sesi dari memori
            del self.sessions[chat_id]
            await update.message.reply_text("👋 Logout berhasil. Sampai jumpa lagi!")
        else:
            await update.message.reply_text("⚠️ Anda belum login.")