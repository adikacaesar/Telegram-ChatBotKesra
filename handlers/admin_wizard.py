from core.config import TAB_RKM

class AdminWizardMixin:
    """Bagian 3: Interaksi Chat Admin (Wizard & Menu Pilihan)"""

    # ==========================================
    # FITUR 1: TAMBAH JADWAL BARU (WIZARD)
    # ==========================================

    async def admin_menu_init(self, update, session):
        jabatan = session.get('jabatan', '').lower()
        if 'kabag' not in jabatan and 'ketua' not in jabatan:
            await update.message.reply_text("⛔ Akses Ditolak.")
            return

        session['temp_rapat'] = {'peserta_list': []}
        session['state'] = 'ADMIN_INPUT_TANGGAL'
        await update.message.reply_text("📅 **TAMBAH JADWAL BARU**\n1️⃣ **Masukkan TANGGAL Rapat:**\n(Contoh: 25 Januari 2026)")

    async def admin_terima_tanggal(self, update, text, session):
        session['temp_rapat']['tanggal'] = text
        session['state'] = 'ADMIN_INPUT_JAM'
        await update.message.reply_text("2️⃣ **Masukkan JAM Rapat:**\n(Contoh: 09:00 WIB)")

    async def admin_terima_jam(self, update, text, session):
        session['temp_rapat']['jam'] = text
        session['state'] = 'ADMIN_INPUT_ID'
        await update.message.reply_text("3️⃣ **Buat ID Rapat:**\n(Contoh: RPT-001)")

    async def admin_terima_id(self, update, text, session):
        session['temp_rapat']['id'] = text
        session['state'] = 'ADMIN_INPUT_NAMA_KEGIATAN'
        await update.message.reply_text("4️⃣ **Masukkan NAMA KEGIATAN:**\n(Contoh: Rapat Koordinasi)")

    async def admin_terima_nama(self, update, text, session):
        session['temp_rapat']['kegiatan'] = text
        session['state'] = 'ADMIN_INPUT_LOKASI'
        await update.message.reply_text("5️⃣ **Masukkan LOKASI:**\n(Contoh: Aula Barat)")

    async def admin_terima_lokasi(self, update, text, session):
        session['temp_rapat']['lokasi'] = text
        session['state'] = 'ADMIN_INPUT_PESERTA'
        jml = len(session['temp_rapat']['peserta_list']) + 1
        await update.message.reply_text(f"📍 Lokasi disimpan.\n6️⃣ **Masukkan PESERTA ke-{jml}:**\n(Nama Orang / Jabatan / Grup)\n👉 Ketik **SELESAI** jika sudah.")

    async def admin_terima_peserta(self, update, text, session):
        if text.upper() == 'SELESAI':
            # Pindah ke AdminActionMixin untuk simpan
            await self.admin_finalisasi_simpan(update, session)
            return
        session['temp_rapat']['temp_nama_input'] = text
        session['state'] = 'ADMIN_INPUT_STATUS_PESERTA'
        await update.message.reply_text(f"👤 Peserta: **{text}**\n❓ **Status/Peran?** (Peserta, Tamu, dll)")

    async def admin_terima_status(self, update, text, session):
        nama_input = session['temp_rapat']['temp_nama_input']
        session['temp_rapat']['peserta_list'].append({'target': nama_input, 'status': text})
        session['state'] = 'ADMIN_INPUT_PESERTA'
        jml = len(session['temp_rapat']['peserta_list']) + 1
        await update.message.reply_text(f"✅ **{nama_input}** ditambahkan.\n👉 **Masukkan PESERTA ke-{jml}:**\n(Atau ketik **SELESAI**)")


    # ==========================================
    # FITUR 2: UPLOAD SURAT RESMI (PILIH EVENT)
    # ==========================================

    async def admin_upload_surat_init(self, update, session):
        # 1. Validasi Admin
        jabatan = session.get('jabatan', '').lower()
        if 'kabag' not in jabatan and 'ketua' not in jabatan:
            await update.message.reply_text("⛔ Akses Ditolak.")
            return

        await update.message.reply_text("🔄 Mengambil daftar kegiatan...")
        self.db_rkm = self.google.ambil_data(TAB_RKM)
        
        # 2. Ambil Daftar Kegiatan UNIK
        # Agar yang muncul bukan per peserta, tapi per ID Kegiatan
        kegiatan_unik = {}
        for row in self.db_rkm:
            id_keg = str(row.get('ID Kegiatan', ''))
            nama_keg = row.get('Kegiatan', '')
            tgl = row.get('Tanggal', '')
            
            # Hanya ambil yang punya ID dan belum masuk list
            if id_keg and id_keg not in kegiatan_unik:
                kegiatan_unik[id_keg] = f"{nama_keg} ({tgl})"

        if not kegiatan_unik:
            await update.message.reply_text("⚠️ Belum ada kegiatan di RKM.")
            return

        # 3. Tampilkan Menu Pilihan
        session['temp_surat_list'] = [] # Simpan urutan ID di RAM agar bisa dipilih pakai nomor
        pesan = "📂 **PILIH KEGIATAN UNTUK UPLOAD SURAT:**\n\n"
        
        nomor = 1
        for id_keg, info in kegiatan_unik.items():
            pesan += f"**{nomor}.** [{id_keg}] {info}\n"
            session['temp_surat_list'].append(id_keg) # Simpan ID ke list sementara
            nomor += 1
            
        pesan += "\nKetik **Nomor** kegiatan yang dimaksud.\nAtau ketik 'batal'."
        
        session['state'] = 'ADMIN_SELECT_EVENT_FOR_LETTER'
        await update.message.reply_text(pesan)

    async def admin_terima_pilihan_surat(self, update, text, session):
        if not text.isdigit():
            await update.message.reply_text("⚠️ Ketik nomor urutnya saja.")
            return

        idx = int(text) - 1
        daftar_id = session.get('temp_surat_list', [])
        
        if 0 <= idx < len(daftar_id):
            id_terpilih = daftar_id[idx]
            session['selected_id_surat'] = id_terpilih
            
            # Ganti status agar siap menerima file (PDF/Gambar)
            session['state'] = 'ADMIN_UPLOAD_LETTER_FILE'
            
            await update.message.reply_text(
                f"✅ Kegiatan Terpilih: **{id_terpilih}**\n\n"
                "📤 **Silakan Kirim File Surat Resmi.**\n"
                "Bisa berupa:\n"
                "- Foto (JPG/PNG)\n"
                "- File Dokumen (PDF)\n\n"
                "Silakan upload sekarang."
            )
        else:
            await update.message.reply_text("❌ Nomor tidak ada di daftar.")