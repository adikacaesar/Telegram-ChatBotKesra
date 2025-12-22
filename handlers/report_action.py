import os
from core.config import TAB_RKM

class ReportActionMixin:
    """Bagian 2: Eksekusi Upload & Simpan"""

    # --- HANDLER FOTO LOOPING ---
    async def proses_terima_foto(self, update, session):
        chat_id = update.message.chat_id
        rapat = session['selected_rapat']
        jenis = session.get('jenis_laporan', 'HADIR')
        
        caption_foto = update.message.caption or ""
        label_file = "Bukti" if jenis == "HADIR" else "SuratSakit"
        
        try:
            # 1. Download
            photo_file = await update.message.photo[-1].get_file()
            import time
            nama_lokal = f"temp_{chat_id}_{int(time.time())}.jpg"
            await photo_file.download_to_drive(nama_lokal)
            
            # 2. Upload Drive
            nama_drive = f"{label_file}_{session['nama']}_{rapat['Kegiatan'][:10]}_{int(time.time())}.jpg"
            link = self.google.upload_ke_drive(nama_lokal, nama_drive)
            
            if os.path.exists(nama_lokal): os.remove(nama_lokal)

            if link:
                if caption_foto:
                    data_simpan = f"{link} (Note: {caption_foto})"
                else:
                    data_simpan = link
                
                session['collected_links'].append(data_simpan)
                
                jml = len(session['collected_links'])
                await update.message.reply_text(f"✅ Foto ke-{jml} diterima.\n(Ketik **SELESAI** jika sudah semua)")
            else:
                await update.message.reply_text("❌ Gagal Upload Drive.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    # --- HANDLER SELESAI UPLOAD ---
    async def proses_selesai_upload_foto(self, update, session):
        if not session.get('collected_links'):
            await update.message.reply_text("⚠️ Belum ada foto yang diterima! Kirim foto dulu.")
            return

        session['state'] = 'AWAITING_FINAL_CAPTION'
        await update.message.reply_text(
            "🆗 Foto tersimpan sementara.\n\n"
            "Apakah ada **Keterangan Tambahan** untuk laporan ini?\n"
            "(Contoh: 'Hadir mewakili Pak Kabag' atau ketik 'skip' jika tidak ada)"
        )

    # --- FINALISASI SIMPAN EXCEL ---
    async def proses_simpan_akhir(self, update, session):
        keterangan_tambahan = update.message.text
        if keterangan_tambahan.lower() == 'skip':
            keterangan_tambahan = ""

        rapat = session['selected_rapat']
        jenis = session.get('jenis_laporan', 'HADIR')
        links = session['collected_links']

        await update.message.reply_text("⏳ Menggabungkan data & update Excel...")

        gabungan_link = "\n".join(links)
        if keterangan_tambahan:
            gabungan_link += f"\n\n[Keterangan: {keterangan_tambahan}]"

        # Panggil Service
        if jenis == "HADIR":
            sukses, msg = self.google.update_bukti(session['nama'], rapat['Kegiatan'], rapat['Tanggal'], gabungan_link, jenis_laporan="HADIR")
        else:
            sukses, msg = self.google.update_bukti(session['nama'], rapat['Kegiatan'], rapat['Tanggal'], gabungan_link, jenis_laporan="SAKIT")

        if sukses:
            await update.message.reply_text(f"✅ **LAPORAN SUKSES!**\n{len(links)} Foto berhasil ditautkan.")
            await self.tampilkan_menu_utama(update, session['nama'])
        else:
            await update.message.reply_text(f"⚠️ Gagal Update Excel: {msg}")

    # --- KHUSUS IZIN (TEXT ONLY) ---
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