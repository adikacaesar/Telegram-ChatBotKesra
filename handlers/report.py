import os
from core.config import TAB_RKM

class ReportMixin:
    """Bagian Otak untuk Upload & Laporan (Versi Upgrade Izin/Sakit)"""

    async def menu_upload_init(self, update, session):
        await update.message.reply_text("🔄 Sinkronisasi data...")
        self.db_rkm = self.google.ambil_data(TAB_RKM)
        
        # Cari jadwal yang 'Bukti Kehadiran'-nya masih kosong
        jadwal_belum = [
            r for r in self.db_rkm 
            if r.get('Peserta') == session['nama'] and not r.get('Bukti Kehadiran')
        ]
        
        if not jadwal_belum:
            await self.tampilkan_menu_utama(update, session['nama'], "🎉 **LUAR BIASA!** Semua laporan selesai.")
            return

        session['temp_list'] = jadwal_belum
        session['state'] = 'SELECTING_RAPAT'
        
        pesan = "📝 **PERBARUI STATUS KEHADIRAN:**\nSilakan pilih kegiatan yang ingin dilaporkan:\n\n"
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
                
                # --- UPDATE ALUR: Tanya Status Dulu ---
                session['state'] = 'SELECTING_STATUS'
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
        """Memproses pilihan 1. Hadir, 2. Izin, 3. Sakit"""
        if text == '1': # HADIR
            session['state'] = 'AWAITING_PHOTO'
            await update.message.reply_text("📸 Silakan kirim **FOTO BUKTI** kegiatan.")
        
        elif text == '2': # IZIN
            session['state'] = 'AWAITING_REASON_IZIN'
            await update.message.reply_text("📝 Silakan ketik **ALASAN** Anda izin:\n(Contoh: Ada urusan keluarga mendesak)")
        
        elif text == '3': # SAKIT
            session['state'] = 'AWAITING_PHOTO_SAKIT'
            await update.message.reply_text("dws 🏥 Silakan kirim **FOTO SURAT DOKTER** atau keterangan sakit.")
        
        elif text.lower() == 'batal':
            await self.tampilkan_menu_utama(update, session['nama'])
        else:
            await update.message.reply_text("Pilih angka 1, 2, atau 3.")

    # --- HANDLER 1: FOTO HADIR ---
    async def proses_terima_foto(self, update, session):
        await self._upload_generic(update, session, jenis="HADIR")

    # --- HANDLER 2: ALASAN IZIN (TEKS) ---
    async def proses_terima_alasan_izin(self, update, session):
        alasan = update.message.text
        chat_id = update.message.chat_id
        rapat = session['selected_rapat']
        
        await update.message.reply_text("⏳ Menyimpan catatan izin ke Drive...")
        
        # Nama file: IZIN_Nama_Kegiatan.txt
        nama_file = f"IZIN_{session['nama']}_{rapat['Kegiatan'][:10]}.txt"
        
        # Upload Teks
        link = self.google.upload_text_ke_drive(nama_file, f"Alasan Izin: {alasan}\nOleh: {session['nama']}")
        
        if link:
            sukses, msg = self.google.update_bukti(session['nama'], rapat['Kegiatan'], rapat['Tanggal'], link, jenis_laporan="IZIN")
            if sukses:
                await update.message.reply_text(f"✅ **IZIN TERCATAT!**\nCatatan disimpan di Drive.\nLink: {link}")
                await self.tampilkan_menu_utama(update, session['nama'])
            else:
                await update.message.reply_text(f"⚠️ Gagal Excel: {msg}")
        else:
            await update.message.reply_text("❌ Gagal Upload ke Drive.")

    # --- HANDLER 3: FOTO SAKIT ---
    async def proses_terima_foto_sakit(self, update, session):
        await self._upload_generic(update, session, jenis="SAKIT")

    # --- HELPER UPLOAD FOTO (Bisa buat Hadir / Sakit) ---
    async def _upload_generic(self, update, session, jenis):
        chat_id = update.message.chat_id
        rapat = session['selected_rapat']
        
        label_file = "Bukti" if jenis == "HADIR" else "SuratSakit"
        await update.message.reply_text(f"⏳ Mengupload {label_file}...")
        
        try:
            photo_file = await update.message.photo[-1].get_file()
            nama_lokal = f"temp_{chat_id}.jpg"
            await photo_file.download_to_drive(nama_lokal)
            
            nama_drive = f"{label_file}_{session['nama']}_{rapat['Kegiatan'][:10]}.jpg"
            link = self.google.upload_ke_drive(nama_lokal, nama_drive)
            
            if os.path.exists(nama_lokal): os.remove(nama_lokal)

            if link:
                sukses, msg = self.google.update_bukti(session['nama'], rapat['Kegiatan'], rapat['Tanggal'], link, jenis_laporan=jenis)
                if sukses:
                    await update.message.reply_text(f"✅ **Laporan {jenis} Diterima!**\nLink: {link}")
                    await self.tampilkan_menu_utama(update, session['nama'])
                else:
                    await update.message.reply_text(f"⚠️ Gagal Excel: {msg}")
            else:
                await update.message.reply_text("❌ Gagal Upload Drive.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")