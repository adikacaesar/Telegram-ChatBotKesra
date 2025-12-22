from telegram import Update
from telegram.ext import ContextTypes
from core.config import TAB_PEGAWAI, TAB_RKM

class AdminMixin:
    """
    Logika Admin dengan Sistem Wizard (Tanya Jawab Bertahap)
    REVISI: Support Multi-Jabatan & Struktur Kolom RKM Baru
    """

    # --- TAHAP 1: INISIALISASI (Saat pilih menu 3) ---
    async def admin_menu_init(self, update, session):
        jabatan = session.get('jabatan', '').lower()
        if 'kabag' not in jabatan and 'ketua' not in jabatan:
            await update.message.reply_text("⛔ Akses Ditolak.")
            return

        session['temp_rapat'] = {
            'peserta_list': [] 
        }
        session['state'] = 'ADMIN_INPUT_TANGGAL'
        
        await update.message.reply_text(
            "📅 **TAMBAH JADWAL BARU**\n"
            "Silakan ikuti langkah-langkah berikut.\n\n"
            "Ketik 'batal' kapan saja untuk membatalkan.\n\n"
            "1️⃣ **Masukkan TANGGAL Rapat:**\n"
            "(Contoh: 25 Januari 2026)"
        )

    # --- TAHAP 2 s/d 8 (LOGIKA SAMA, HANYA MENERUSKAN DATA) ---
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
        await update.message.reply_text("4️⃣ **Masukkan NAMA KEGIATAN:**\n(Contoh: Rapat Koordinasi Awal Tahun)")

    async def admin_terima_nama(self, update, text, session):
        session['temp_rapat']['kegiatan'] = text
        session['state'] = 'ADMIN_INPUT_LOKASI'
        await update.message.reply_text("5️⃣ **Masukkan LOKASI:**\n(Contoh: Aula Barat / Zoom Meeting)")

    async def admin_terima_lokasi(self, update, text, session):
        session['temp_rapat']['lokasi'] = text
        session['state'] = 'ADMIN_INPUT_PESERTA'
        jml = len(session['temp_rapat']['peserta_list']) + 1
        await update.message.reply_text(
            f"📍 Data Lokasi tersimpan.\n\n"
            f"6️⃣ **Masukkan PESERTA ke-{jml}:**\n"
            "Bisa berupa **Nama Orang** atau **Nama Jabatan**.\n"
            "(Bot akan mencari di Jabatan 1 s.d 4)\n\n"
            "👉 Ketik **SELESAI** jika sudah tidak ada peserta lagi."
        )

    async def admin_terima_peserta(self, update, text, session):
        if text.upper() == 'SELESAI':
            await self.admin_finalisasi_simpan(update, session)
            return

        session['temp_rapat']['temp_nama_input'] = text
        session['state'] = 'ADMIN_INPUT_STATUS_PESERTA'
        await update.message.reply_text(
            f"👤 Peserta: **{text}**\n"
            "❓ **Apa status/peran dia?**\n"
            "(Contoh: Peserta, Pembicara, Notulen, Tamu)"
        )

    async def admin_terima_status(self, update, text, session):
        nama_input = session['temp_rapat']['temp_nama_input']
        status_input = text
        
        session['temp_rapat']['peserta_list'].append({
            'target': nama_input,
            'status': status_input
        })
        
        session['state'] = 'ADMIN_INPUT_PESERTA'
        jml = len(session['temp_rapat']['peserta_list']) + 1
        await update.message.reply_text(
            f"✅ **{nama_input}** ({status_input}) ditambahkan.\n\n"
            f"👉 **Masukkan PESERTA ke-{jml}:**\n"
            "(Atau ketik **SELESAI** untuk menyimpan semua jadwal)"
        )

    # --- TAHAP FINAL: EKSEKUSI KE EXCEL (REVISI BESAR) ---
    async def admin_finalisasi_simpan(self, update, session):
        data = session['temp_rapat']
        peserta_raw = data['peserta_list']
        
        if not peserta_raw:
            await update.message.reply_text("⚠️ Belum ada peserta yang dimasukkan!")
            session['state'] = 'ADMIN_INPUT_PESERTA'
            return

        await update.message.reply_text("⏳ **Sedang memproses data...**\nBot sedang mencari nama pegawai dan menyusun jadwal.")

        # 1. Expand Group/Jabatan menjadi Nama Asli
        self.db_pegawai = self.google.ambil_data(TAB_PEGAWAI)
        final_targets = []
        
        # Daftar Kolom Jabatan yang mau dicek
        cols_jabatan = ['Jabatan 1', 'Jabatan 2', 'Jabatan 3', 'Jabatan 4']

        for p in peserta_raw:
            target_str = p['target'].strip().lower()
            role_str = p['status']
            found = False
            
            for pegawai in self.db_pegawai:
                # 1. Cek Nama (Partial Match)
                nama_db = str(pegawai.get('Nama', '')).strip().lower()
                if target_str in nama_db:
                    final_targets.append({'data': pegawai, 'role': role_str})
                    found = True
                    continue # Lanjut ke pegawai berikutnya agar tidak double add
                
                # 2. Cek Semua Kolom Jabatan (Exact Match)
                for col in cols_jabatan:
                    jab_db = str(pegawai.get(col, '')).strip().lower()
                    if target_str == jab_db:
                        final_targets.append({'data': pegawai, 'role': role_str})
                        found = True
                        break # Sudah ketemu di salah satu jabatan, stop loop jabatan
            
            if not found:
                await update.message.reply_text(f"⚠️ Peringatan: '{p['target']}' tidak ditemukan di database pegawai.")

        if not final_targets:
            await update.message.reply_text("❌ Gagal menyimpan. Tidak ada pegawai valid yang ditemukan.")
            return

        # 2. Simpan ke Excel RKM (SESUAI STRUKTUR BARU)
        # Struktur: ['Tanggal', 'Jam', 'ID Kegiatan', 'Kegiatan', 'Lokasi', 'Peserta', 'Status', 'Bukti Kehadiran', 'Timestamp', 'Verifikasi', 'ID_Unik']
        
        sheet = self.google.sheet_client.open(self.google.NAMA_SPREADSHEET)
        ws_rkm = sheet.worksheet(TAB_RKM)
        
        rows_to_add = []
        notif_count = 0
        
        # Buat list ID Pegawai yang sudah diadd biar gak duplikat
        added_ids = []

        for item in final_targets:
            pegawai = item['data']
            role = item['role']
            
            # Cek duplikasi (misal Staff Kesra 1 ada nama Adika, tapi Adika juga diinput manual)
            if pegawai['ID_Pegawai'] in added_ids:
                continue
            added_ids.append(pegawai['ID_Pegawai'])
            
            # Buat ID Unik (Misal: RPT-001_101)
            id_unik = f"{data['id']}_{pegawai['ID_Pegawai']}"

            row = [
                data['tanggal'],        # Tanggal
                data['jam'],            # Jam
                data['id'],             # ID Kegiatan
                data['kegiatan'],       # Kegiatan
                data['lokasi'],         # Lokasi
                pegawai['Nama'],        # Peserta
                role,                   # Status
                "",                     # Bukti Kehadiran
                "",                     # Timestamp
                "FALSE",                # Verifikasi
                id_unik                 # ID_Unik
            ]
            rows_to_add.append(row)
            
            # Kirim Notifikasi
            if pegawai.get('Chat_ID'):
                try:
                    msg = (
                        f"📅 **UNDANGAN BARU**\n"
                        f"Kegiatan: {data['kegiatan']}\n"
                        f"Peran: {role}\n"
                        f"Waktu: {data['tanggal']} pukul {data['jam']}\n"
                        f"Lokasi: {data['lokasi']}\n\n"
                        "Mohon kehadirannya."
                    )
                    await update.get_bot().send_message(chat_id=pegawai['Chat_ID'], text=msg)
                    notif_count += 1
                except:
                    pass

        try:
            ws_rkm.append_rows(rows_to_add)
            await update.message.reply_text(
                f"✅ **SUKSES!**\n"
                f"Jadwal berhasil dibuat.\n"
                f"- Total Undangan: {len(rows_to_add)} orang\n"
                f"- Notifikasi Terkirim: {notif_count}"
            )
            await self.tampilkan_menu_utama(update, session['nama'])
        except Exception as e:
            await update.message.reply_text(f"❌ Error Excel: {e}")