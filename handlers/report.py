import os
# UPDATE IMPORT
from core.config import TAB_RKM

class ReportMixin:
    """Bagian Otak untuk Upload & Laporan"""

    async def menu_upload_init(self, update, session):
        await update.message.reply_text("🔄 Sinkronisasi data...")
        # Refresh Data
        self.db_rkm = self.google.ambil_data(TAB_RKM)
        
        # Filter: Hanya yang belum ada bukti
        jadwal_belum = [
            r for r in self.db_rkm 
            if r.get('Peserta') == session['nama'] and not r.get('Bukti Kehadiran')
        ]
        
        if not jadwal_belum:
            await self.tampilkan_menu_utama(update, session['nama'], "🎉 **LUAR BIASA!** Semua laporan selesai.")
            return

        session['temp_list'] = jadwal_belum
        session['state'] = 'SELECTING_RAPAT'
        
        pesan = "📸 **TANGGUNGAN LAPORAN:**\n\n"
        for i, j in enumerate(jadwal_belum):
            pesan += f"**{i+1}.** {j['Kegiatan']} ({j['Tanggal']})\n"
        pesan += "\n❌ Ketik 'batal' untuk kembali."
        await update.message.reply_text(pesan)

    async def proses_pilih_rapat(self, update, text, session):
        if text.lower() == 'batal':
            await self.tampilkan_menu_utama(update, session['nama'], "🔙 Kembali ke Menu.")
            return

        if text.isdigit():
            idx = int(text) - 1
            if 0 <= idx < len(session['temp_list']):
                session['selected_rapat'] = session['temp_list'][idx]
                session['state'] = 'AWAITING_PHOTO'
                await update.message.reply_text(f"✅ Dipilih: {session['selected_rapat']['Kegiatan']}\n📸 **KIRIM FOTO BUKTI!**")
            else:
                await update.message.reply_text("Nomor salah.")
        else:
            await update.message.reply_text("Ketik nomor atau 'batal'.")

    async def proses_terima_foto(self, update, session):
        chat_id = update.message.chat_id
        rapat = session['selected_rapat']
        
        await update.message.reply_text("⏳ Uploading...")
        try:
            photo_file = await update.message.photo[-1].get_file()
            nama_lokal = f"temp_{chat_id}.jpg"
            await photo_file.download_to_drive(nama_lokal)
            
            nama_drive = f"Bukti_{session['nama']}_{rapat['Kegiatan'][:10]}.jpg"
            link = self.google.upload_ke_drive(nama_lokal, nama_drive)
            
            if os.path.exists(nama_lokal): os.remove(nama_lokal)

            if link:
                sukses, msg = self.google.update_bukti(session['nama'], rapat['Kegiatan'], rapat['Tanggal'], link)
                if sukses:
                    await update.message.reply_text(f"🎉 **SELESAI!**\nLink: {link}\n✅ Laporan tercatat.")
                    await self.tampilkan_menu_utama(update, session['nama'])
                else:
                    await update.message.reply_text(f"⚠️ Gagal Excel: {msg}")
            else:
                await update.message.reply_text("❌ Gagal Upload Drive.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")