import os
from core.config import TAB_RKM

class ReportMixin:
    """Bagian Otak untuk Upload & Laporan (Support Multi-Upload)"""

    async def menu_upload_init(self, update, session):
        await update.message.reply_text("🔄 Sinkronisasi data...")
        self.db_rkm = self.google.ambil_data(TAB_RKM)
        
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
                
                # SIAPKAN LIST PENAMPUNG LINK (Fitur Baru Multi-Upload)
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

    # --- HANDLER 1: FOTO (HADIR & SAKIT - LOGIKA SAMA) ---
    async def proses_terima_foto(self, update, session):
        """
        Fungsi ini dipanggil berulang-ulang setiap ada foto masuk.
        Tugasnya cuma upload ke Drive & simpan link di RAM.
        """
        chat_id = update.message.chat_id
        rapat = session['selected_rapat']
        jenis = session.get('jenis_laporan', 'HADIR')
        
        # Ambil caption bawaan foto (jika user ngasih caption di foto Telegramnya)
        caption_foto = update.message.caption or ""
        
        label_file = "Bukti" if jenis == "HADIR" else "SuratSakit"
        
        try:
            # Download Foto
            photo_file = await update.message.photo[-1].get_file()
            # Nama file unik pakai timestamp
            import time
            nama_lokal = f"temp_{chat_id}_{int(time.time())}.jpg"
            await photo_file.download_to_drive(nama_lokal)
            
            # Upload Drive
            nama_drive = f"{label_file}_{session['nama']}_{rapat['Kegiatan'][:10]}_{int(time.time())}.jpg"
            link = self.google.upload_ke_drive(nama_lokal, nama_drive)
            
            # Hapus file lokal
            if os.path.exists(nama_lokal): os.remove(nama_lokal)

            if link:
                # FORMAT PENYIMPANAN: Link (Caption Foto)
                if caption_foto:
                    data_simpan = f"{link} (Note: {caption_foto})"
                else:
                    data_simpan = link
                
                # Masukkan ke keranjang sementara
                session['collected_links'].append(data_simpan)
                
                # REVISI: HAPUS quote=True YANG BIKIN ERROR
                jml = len(session['collected_links'])
                await update.message.reply_text(f"✅ Foto ke-{jml} diterima.\n(Ketik **SELESAI** jika sudah semua)")
            else:
                await update.message.reply_text("❌ Gagal Upload Drive.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    # --- HANDLER 2: KETIKA KETIK "SELESAI" ---
    async def proses_selesai_upload_foto(self, update, session):
        """User sudah selesai kirim foto, sekarang minta keterangan akhir"""
        if not session.get('collected_links'):
            await update.message.reply_text("⚠️ Belum ada foto yang diterima! Kirim foto dulu.")
            return

        session['state'] = 'AWAITING_FINAL_CAPTION'
        await update.message.reply_text(
            "🆗 Foto tersimpan sementara.\n\n"
            "Apakah ada **Keterangan Tambahan** untuk laporan ini?\n"
            "(Contoh: 'Hadir mewakili Pak Kabag' atau ketik 'skip' jika tidak ada)"
        )

    # --- HANDLER 3: FINALISASI (SIMPAN KE EXCEL) ---
    async def proses_simpan_akhir(self, update, session):
        keterangan_tambahan = update.message.text
        if keterangan_tambahan.lower() == 'skip':
            keterangan_tambahan = ""

        rapat = session['selected_rapat']
        jenis = session.get('jenis_laporan', 'HADIR')
        links = session['collected_links']

        await update.message.reply_text("⏳ Menggabungkan data & update Excel...")

        # GABUNG LINK DENGAN ENTER (\n)
        gabungan_link = "\n".join(links)
        
        if keterangan_tambahan:
            gabungan_link += f"\n\n[Keterangan: {keterangan_tambahan}]"

        # Tentukan masuk kolom mana
        if jenis == "HADIR":
            sukses, msg = self.google.update_bukti(session['nama'], rapat['Kegiatan'], rapat['Tanggal'], gabungan_link, jenis_laporan="HADIR")
        else:
            # Sakit
            sukses, msg = self.google.update_bukti(session['nama'], rapat['Kegiatan'], rapat['Tanggal'], gabungan_link, jenis_laporan="SAKIT")

        if sukses:
            await update.message.reply_text(f"✅ **LAPORAN SUKSES!**\n{len(links)} Foto berhasil ditautkan.")
            await self.tampilkan_menu_utama(update, session['nama'])
        else:
            await update.message.reply_text(f"⚠️ Gagal Update Excel: {msg}")

    # --- HANDLER IZIN ---
    async def proses_terima_alasan_izin(self, update, session):
        alasan = update.message.text
        rapat = session['selected_rapat']
        await update.message.reply_text("⏳ Menyimpan catatan izin...")
        
        nama_file = f"IZIN_{session['nama']}_{rapat['Kegiatan'][:10]}.txt"
        link = self.google.upload_text_ke_drive(nama_file, f"Alasan Izin: {alasan}\nOleh: {session['nama']}")
        
        if link:
            sukses, msg = self.google.update_bukti(session['nama'], rapat['Kegiatan'], rapat['Tanggal'], link, jenis_laporan="IZIN")
            if sukses:
                await update.message.reply_text(f"✅ Izin Tercatat.")
                await self.tampilkan_menu_utama(update, session['nama'])
            else:
                await update.message.reply_text(f"⚠️ Gagal Excel: {msg}")