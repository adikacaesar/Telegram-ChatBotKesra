from core.config import TAB_RKM

class ReportMenuMixin:
    """Bagian 1: Navigasi Menu & Pilihan"""

    async def menu_upload_init(self, update, session):
        await update.message.reply_text("🔄 Sinkronisasi data...")
        self.db_rkm = self.google.ambil_data(TAB_RKM)
        
        # Cari jadwal yang pesertanya user ini & kolom bukti masih kosong
        jadwal_belum = [
            r for r in self.db_rkm 
            if r.get('Peserta') == session['nama'] and not r.get('Bukti Kehadiran')
        ]
        
        if not jadwal_belum:
            await self.tampilkan_menu_utama(update, session['nama'], "🎉 **LUAR BIASA!** Semua laporan selesai.")
            return

        session['temp_list'] = jadwal_belum
        session['state'] = 'SELECTING_RAPAT'
        
        pesan = "📝 **PERBARUI STATUS KEHADIRAN:**\nSilakan pilih kegiatan:\n\n"
        for i, j in enumerate(jadwal_belum):
            pesan += f"**{i+1}.** {j['Kegiatan']} ({j['Tanggal']})\n"
        pesan += "\n❌ Ketik 'batal' untuk kembali."
        await update.message.reply_text(pesan)

    async def proses_pilih_rapat(self, update, text, session):
        if text.lower() == 'batal':
            await self.tampilkan_menu_utama(update, session['nama'], "🔙 Kembali.")
            return

        if text.isdigit():
            idx = int(text) - 1
            if 0 <= idx < len(session['temp_list']):
                session['selected_rapat'] = session['temp_list'][idx]
                session['state'] = 'SELECTING_STATUS'
                
                # Reset penampung link
                session['collected_links'] = [] 
                
                rapat = session['selected_rapat']
                await update.message.reply_text(
                    f"✅ Kegiatan: **{rapat['Kegiatan']}**\n"
                    "Status kehadiran Anda?\n\n"
                    "1️⃣ **Hadir** (Upload Foto Kegiatan)\n"
                    "2️⃣ **Izin** (Tulis Alasan)\n"
                    "3️⃣ **Sakit** (Upload Surat Dokter)"
                )
            else:
                await update.message.reply_text("Nomor salah.")
        else:
            await update.message.reply_text("Ketik nomor.")

    async def proses_pilih_status(self, update, text, session):
        if text == '1': # HADIR
            session['state'] = 'AWAITING_PHOTO'
            session['jenis_laporan'] = "HADIR"
            await update.message.reply_text(
                "📸 **MODE MULTI-UPLOAD AKTIF**\n\n"
                "Silakan kirim FOTO kegiatan.\n"
                "Bisa kirim **banyak foto sekaligus** (Album).\n\n"
                "👉 Jika semua foto sudah terkirim, KETIK: **SELESAI**"
            )
        
        elif text == '2': # IZIN
            session['state'] = 'AWAITING_REASON_IZIN'
            await update.message.reply_text("📝 Silakan ketik **ALASAN** Anda izin:")
        
        elif text == '3': # SAKIT
            session['state'] = 'AWAITING_PHOTO_SAKIT'
            session['jenis_laporan'] = "SAKIT"
            await update.message.reply_text(
                "🏥 **UPLOAD SURAT DOKTER**\n\n"
                "Silakan kirim foto surat.\n"
                "👉 Jika sudah, KETIK: **SELESAI**"
            )
        
        elif text.lower() == 'batal':
            await self.tampilkan_menu_utama(update, session['nama'])
        else:
            await update.message.reply_text("Pilih angka 1, 2, atau 3.")