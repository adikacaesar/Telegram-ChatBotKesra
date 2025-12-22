import os
from core.config import TAB_PEGAWAI, TAB_RKM, ID_FOLDER_SURAT # <-- Import ID Folder Baru

class AdminActionMixin:
    """Bagian 4: Pemrosesan Data Admin"""

    async def admin_finalisasi_simpan(self, update, session):
        data = session['temp_rapat']
        peserta_raw = data['peserta_list']
        
        if not peserta_raw:
            await update.message.reply_text("⚠️ Belum ada peserta!")
            session['state'] = 'ADMIN_INPUT_PESERTA'
            return

        await update.message.reply_text("⏳ **Memproses data...**")

        self.db_pegawai = self.google.ambil_data(TAB_PEGAWAI)
        final_targets = []
        cols_jabatan = ['Jabatan 1', 'Jabatan 2', 'Jabatan 3', 'Jabatan 4']

        for p in peserta_raw:
            target_str = p['target'].strip().lower()
            role_str = p['status']
            found = False
            
            for pegawai in self.db_pegawai:
                nama_db = str(pegawai.get('Nama', '')).strip().lower()
                if target_str in nama_db:
                    final_targets.append({'data': pegawai, 'role': role_str})
                    found = True
                    continue 
                
                for col in cols_jabatan:
                    jab_db = str(pegawai.get(col, '')).strip().lower()
                    if target_str == jab_db:
                        final_targets.append({'data': pegawai, 'role': role_str})
                        found = True
                        break 
            
            if not found:
                await update.message.reply_text(f"⚠️ Peringatan: '{p['target']}' tidak ditemukan.")

        if not final_targets:
            await update.message.reply_text("❌ Gagal. Tidak ada target valid.")
            return

        sheet = self.google.sheet_client.open(self.google.NAMA_SPREADSHEET)
        ws_rkm = sheet.worksheet(TAB_RKM)
        
        rows_to_add = []
        notif_count = 0
        added_signatures = set()

        for item in final_targets:
            pegawai = item['data']
            role = item['role']
            
            signature = f"{pegawai['ID_Pegawai']}_{pegawai['Nama']}"
            if signature in added_signatures: continue
            added_signatures.add(signature)
            
            id_unik = f"{data['id']}_{pegawai['ID_Pegawai']}"

            row = [
                data['tanggal'], data['jam'], data['id'],
                data['kegiatan'], data['lokasi'],
                pegawai['Nama'], role,
                "", "", "FALSE", id_unik, "", ""
            ]
            rows_to_add.append(row)
            
            if pegawai.get('Chat_ID'):
                try:
                    msg = f"📅 **UNDANGAN BARU**\nKegiatan: {data['kegiatan']}\nWaktu: {data['tanggal']} {data['jam']}\nLokasi: {data['lokasi']}"
                    await update.get_bot().send_message(chat_id=pegawai['Chat_ID'], text=msg)
                    notif_count += 1
                except: pass

        try:
            ws_rkm.append_rows(rows_to_add)
            await update.message.reply_text(
                f"✅ **SUKSES!**\nTotal Undangan: {len(rows_to_add)}\nNotifikasi: {notif_count}"
            )
            await self.tampilkan_menu_utama(update, session['nama'])
        except Exception as e:
            await update.message.reply_text(f"❌ Error Excel: {e}")

    async def admin_proses_file_surat(self, update, session):
        id_kegiatan = session['selected_id_surat']
        user_name = session['nama']
        
        file_obj = None
        mime_type = ""
        ext = ""

        if update.message.document:
            file_obj = await update.message.document.get_file()
            mime_type = update.message.document.mime_type
            ext = update.message.document.file_name.split('.')[-1]
        elif update.message.photo:
            file_obj = await update.message.photo[-1].get_file()
            mime_type = "image/jpeg"
            ext = "jpg"
        else:
            await update.message.reply_text("⚠️ Kirim PDF atau Foto.")
            return

        await update.message.reply_text("⏳ **Mengupload surat resmi...**")

        try:
            import time
            timestamp = int(time.time())
            nama_lokal = f"temp_surat_{timestamp}.{ext}"
            await file_obj.download_to_drive(nama_lokal)

            nama_drive = f"SURAT_{id_kegiatan}_{timestamp}.{ext}"
            
            # --- UPLOAD KE FOLDER KHUSUS SURAT ---
            link = self.google.upload_file_bebas(
                nama_lokal, 
                nama_drive, 
                mime_type, 
                target_folder_id=ID_FOLDER_SURAT # <-- Parameter Baru
            )

            if os.path.exists(nama_lokal): os.remove(nama_lokal)

            if link:
                sukses, msg = self.google.update_surat_resmi_by_id(id_kegiatan, link)
                if sukses:
                    await update.message.reply_text(
                        f"✅ **SURAT RESMI TERSIMPAN!**\n🆔 {id_kegiatan}\n📎 {link}"
                    )
                    await self.tampilkan_menu_utama(update, user_name)
                else:
                    await update.message.reply_text(f"⚠️ Gagal Excel: {msg}")
            else:
                await update.message.reply_text("❌ Gagal Upload Drive.")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")