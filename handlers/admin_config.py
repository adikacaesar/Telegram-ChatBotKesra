from telegram import Update
from datetime import time
import pytz
from core.config import TAB_PEGAWAI

class AdminConfigMixin:
    """
    Mixin khusus untuk menangani Konfigurasi Notifikasi & Broadcast.
    """

    async def menu_config_notif(self, update, session):
        """Menampilkan Dashboard Konfigurasi"""
        items = self.google.ambil_config_notif()
        
        pesan = "⚙️ **PENGATURAN NOTIFIKASI & BROADCAST**\n\n"
        pesan += "Daftar Jadwal Otomatis:\n"
        
        if not items:
            pesan += "(Belum ada jadwal)\n"
        else:
            for i in items:
                status = i.get('Status', 'OFF')
                waktu = i.get('Waktu', '??:??')
                target = i.get('Target', 'ALL')
                isi = i.get('Pesan', '-')

                icon = "🟢" if status == 'ON' else "🔴"
                pesan += f"{icon} **{waktu}** [{target}] : {isi}\n"
        
        pesan += "\n👇 **PILIHAN MENU:**\n"
        pesan += "1️⃣ Tambah Jadwal Baru\n"
        pesan += "2️⃣ Hapus Jadwal\n"
        pesan += "3️⃣ Kembali ke Menu Utama\n"
        pesan += "4️⃣ BROADCAST PESAN (DADAKAN)"

        session['state'] = 'CONFIG_MENU'
        await update.message.reply_text(pesan)

    async def config_process_menu(self, update, context, text, session):
        if text == '1': # Tambah
            session['state'] = 'CONFIG_ADD_TIME'
            await update.message.reply_text("⏰ **Masukkan JAM Notifikasi:**\n(Format HH:MM, contoh: 07:00)")
            
        elif text == '2': # Hapus
            session['state'] = 'CONFIG_DELETE'
            await update.message.reply_text("🗑️ **Ketik JAM yang mau dihapus:**\n(Persis seperti di list, contoh: 07:00)")
            
        elif text == '3': # Kembali (Dulu nomor 4)
            await self.tampilkan_menu_utama(update, session['nama'])

        elif text == '4': # Broadcast (Dulu nomor 5)
            session['state'] = 'BROADCAST_INPUT'
            await update.message.reply_text(
                "📢 **MODE BROADCAST MANUAL**\n\n"
                "Ketik pesan yang ingin Anda kirimkan ke SEMUA pegawai.\n"
                "(Ketik 'batal' untuk kembali)"
            )
        else:
            await update.message.reply_text("Pilih angka 1-4.")

    # --- WIZARD TAMBAH JADWAL ---
    
    async def config_add_time(self, update, text, session):
        if ':' not in text:
            await update.message.reply_text("⚠️ Format salah. Gunakan HH:MM")
            return
        
        session['temp_config'] = {'waktu': text}
        session['state'] = 'CONFIG_SELECT_TARGET'
        
        await update.message.reply_text(
            "🎯 **PILIH TARGET PENERIMA:**\n\n"
            "Ketik salah satu:\n"
            "• **ALL** (Semua Pegawai)\n"
            "• **KABAG** (Hanya Pimpinan/Kabag)\n"
            "• **STAFF** (Hanya Staff/Pelaksana)"
        )

    async def config_select_target(self, update, text, session):
        target = text.upper()
        if target not in ['ALL', 'KABAG', 'STAFF']:
            await update.message.reply_text("⚠️ Pilihan salah. Ketik: ALL, KABAG, atau STAFF.")
            return

        session['temp_config']['target'] = target
        session['state'] = 'CONFIG_ADD_MSG'
        await update.message.reply_text(f"📝 **Target: {target}**. Sekarang masukkan isi pesan notifikasi:")

    async def config_add_msg(self, update, text, session):
        session['temp_config']['pesan'] = text
        session['state'] = 'CONFIG_CONFIRM_TEST'
        
        data = session['temp_config']
        await update.message.reply_text(
            f"📋 **KONFIRMASI JADWAL**\n"
            f"⏰ Jam: {data['waktu']}\n"
            f"🎯 Target: {data['target']}\n"
            f"💬 Pesan: {data['pesan']}\n\n"
            "👇 Pilih Tindakan:\n"
            "1️⃣ 🧪 **TEST DULU** (Kirim ke saya sekarang)\n"
            "2️⃣ 💾 **SIMPAN** (Masuk Database)"
        )

    async def config_confirm_test(self, update, context, text, session):
        data = session['temp_config']
        
        if text == '1': # TEST MODE
            await update.message.reply_text(
                f"🧪 **[TEST MODE]**\n"
                f"🔔 **{data['pesan']}**\n"
                f"📅 (Tanggal Hari Ini)\n\n"
                f"Halo {session['nama']}, (Isi Agenda)..."
            )
            await update.message.reply_text("Oke, sudah dicek? Ketik **2** untuk SIMPAN permanen.")
            
        elif text == '2': # SIMPAN
            sukses = self.google.tambah_config_notif(data['waktu'], data['pesan'], data['target'])
            if sukses:
                await update.message.reply_text("✅ Berhasil disimpan ke Excel!")
                # Auto reload scheduler (Otomatis)
                await self.reload_scheduler(context.application)
                await self.menu_config_notif(update, session)
            else:
                await update.message.reply_text("❌ Gagal simpan ke Excel.")
        else:
            await update.message.reply_text("Pilih 1 atau 2.")

    async def config_delete(self, update, context, text, session):
        sukses = self.google.hapus_config_notif(text)
        if sukses:
            await update.message.reply_text(f"✅ Jadwal {text} dihapus.")
            # Auto reload scheduler (Otomatis)
            await self.reload_scheduler(context.application)
        else:
            await update.message.reply_text("❌ Jam tidak ditemukan.")
        await self.menu_config_notif(update, session)

    # --- BROADCAST MANUAL ---
    async def broadcast_process(self, update, text, session):
        if text.lower() == 'batal':
            await self.menu_config_notif(update, session)
            return

        await update.message.reply_text("⏳ Mengirim pesan ke semua pegawai...")
        
        db_pegawai = self.google.ambil_data(TAB_PEGAWAI)
        count = 0
        
        for p in db_pegawai:
            chat_id = p.get('Chat_ID')
            if chat_id:
                try:
                    msg = f"📢 **PENGUMUMAN DARI ADMIN**\n\n{text}"
                    await update.get_bot().send_message(chat_id=chat_id, text=msg)
                    count += 1
                except: pass
        
        await update.message.reply_text(f"✅ Broadcast Selesai.\nTerkirim ke {count} orang.")
        await self.menu_config_notif(update, session)

    # --- RELOAD SCHEDULER (Helper) ---
    async def reload_scheduler(self, application):
        """Memuat ulang job dari Excel tanpa restart bot"""
        job_queue = application.job_queue
        
        # Hapus job lama
        for job in job_queue.jobs():
            if job.name and job.name.startswith('notif_'):
                job.schedule_removal()
        
        # Pasang ulang dari Excel
        items = self.google.ambil_config_notif()
        wib = pytz.timezone('Asia/Jakarta')
        count = 0
        
        for item in items:
            if item.get('Status') == 'ON':
                try:
                    waktu_str = str(item['Waktu'])
                    h, m = map(int, waktu_str.split(':'))
                    t = time(hour=h, minute=m, tzinfo=wib)
                    
                    target_val = item.get('Target', 'ALL')
                    
                    job_queue.run_daily(
                        self.jalankan_notifikasi_pagi, 
                        t,
                        name=f"notif_{waktu_str}",
                        data={'pesan': item['Pesan'], 'target': target_val}
                    )
                    count += 1
                except: pass
        print(f"🔄 Scheduler Reloaded: {count} active jobs.")