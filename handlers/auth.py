from core.config import TAB_PEGAWAI, TAB_RKM
class AuthMixin:
    """Bagian Otak untuk Login & Logout"""

    async def proses_login(self, update, context, text, chat_id):
        # Cek apakah input berupa Angka (ID)
        if text.isdigit():
            id_input = int(text)
            # Cari di Database Pegawai
            pegawai = next((p for p in self.db_pegawai if p.get('ID_Pegawai') == id_input), None)
            
            if pegawai:
                # BUAT SESI BARU
                self.sessions[chat_id] = {
                    'nama': pegawai.get('Nama'), 
                    'state': 'MAIN_MENU', 
                    'temp_list': [], 
                    'selected_rapat': None
                }
                await update.message.reply_text(f"✅ Halo **{pegawai.get('Nama')}**!\n1️⃣ Cek Jadwal\n2️⃣ Upload Laporan")
            else:
                await update.message.reply_text("❌ ID Salah / Tidak Ditemukan.")
        else:
            await update.message.reply_text("🔒 Belum login. Silakan ketik **ID Pegawai** Anda.")

    async def proses_logout(self, update, chat_id):
        if chat_id in self.sessions:
            del self.sessions[chat_id]
            await update.message.reply_text("👋 Logout berhasil. Sampai jumpa!")