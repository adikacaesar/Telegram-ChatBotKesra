from telegram import Update
from telegram.ext import ContextTypes

# --- Import Config ---
from core.config import TAB_PEGAWAI, TAB_RKM

# --- Import Logika (Mixin) ---
from .auth import AuthMixin
from .schedule import ScheduleMixin
from .report import ReportMixin
from .notification import NotificationMixin # Hasil Refactoring
from .common import CommonMixin             # Hasil Refactoring

class BotHandler(AuthMixin, ScheduleMixin, ReportMixin, NotificationMixin, CommonMixin):
    """
    Kelas Utama (Router) yang mengatur lalu lintas pesan.
    Semua logika inti (Otak) dipecah ke dalam Mixin agar kode lebih rapi.
    """
    
    def __init__(self, google_service):
        self.google = google_service
        self.sessions = {} # Memori Sesi User (RAM)
        
        print("🔄 Memuat Database...")
        self.db_pegawai = self.google.ambil_data(TAB_PEGAWAI)
        self.db_rkm = self.google.ambil_data(TAB_RKM)
        print("✅ Database Siap!")

    # --- ROUTER PESAN (TRAFFIC POLICE) ---
    async def proses_pesan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text.strip() if update.message.text else ""
        chat_id = update.message.chat_id

        # 1. Cek Login
        if chat_id not in self.sessions:
            await self.proses_login(update, context, text, chat_id)
            return

        # 2. Ambil Status User
        session = self.sessions[chat_id]
        state = session['state']
        
        # --- GLOBAL CANCEL (BATAL) ---
        # Agar user bisa membatalkan proses apapun (kecuali di menu utama)
        if text.lower() == 'batal' and state != 'MAIN_MENU':
             await self.tampilkan_menu_utama(update, session['nama'], "❌ Aksi dibatalkan.")
             return

        # --- ROUTING BERDASARKAN STATE ---
        
        # A. MENU UTAMA
        if state == 'MAIN_MENU':
            if text == '1':
                session['state'] = 'SUBMENU_JADWAL'
                await update.message.reply_text("📅 **MENU JADWAL**\n1️⃣ Hari Ini\n2️⃣ Minggu Ini\n3️⃣ Bulan Ini\n4️⃣ Semua\n5️⃣ Cari Tanggal\n❌ 'batal'")
            elif text == '2':
                # Masuk ke alur Laporan/Update Status
                await self.menu_upload_init(update, session)
            elif text.lower() == 'logout':
                await self.proses_logout(update, chat_id)
            else:
                await update.message.reply_text("Ketik 1, 2, atau 'logout'.")

        # B. MENU JADWAL
        elif state == 'SUBMENU_JADWAL':
            await self.menu_jadwal_handler(update, context, text, chat_id, session)

        elif state == 'SEARCHING_DATE':
            await self.cari_tanggal_manual(update, text, session)

        # C. ALUR LAPORAN / STATUS (Fitur Multi-Upload & Izin/Sakit)
        elif state == 'SELECTING_RAPAT':
            await self.proses_pilih_rapat(update, text, session)

        elif state == 'SELECTING_STATUS':
            # Memilih 1. Hadir, 2. Izin, 3. Sakit
            await self.proses_pilih_status(update, text, session)

        elif state == 'AWAITING_REASON_IZIN':
            # Menangkap teks alasan izin
            await self.proses_terima_alasan_izin(update, session)

        # PENANGANAN TEXT SAAT FASE UPLOAD FOTO (Multi-Upload)
        elif state in ['AWAITING_PHOTO', 'AWAITING_PHOTO_SAKIT']:
            if text.upper() == 'SELESAI':
                # User selesai kirim banyak foto, lanjut ke tahap caption akhir
                await self.proses_selesai_upload_foto(update, session)
            else:
                # Jika user kirim teks biasa saat diminta foto
                await update.message.reply_text("⚠️ Sedang mode terima foto.\nKirim foto lagi (bisa banyak) atau ketik **SELESAI** jika sudah.")

        # PENANGANAN CAPTION AKHIR (Setelah ketik SELESAI)
        elif state == 'AWAITING_FINAL_CAPTION':
            await self.proses_simpan_akhir(update, session)

    # --- HANDLER FOTO ---
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        if chat_id in self.sessions:
            state = self.sessions[chat_id]['state']
            
            # Logic sama untuk Hadir maupun Sakit (karena sekarang pakai Multi-Upload)
            if state == 'AWAITING_PHOTO':
                await self.proses_terima_foto(update, self.sessions[chat_id])
            
            elif state == 'AWAITING_PHOTO_SAKIT':
                await self.proses_terima_foto(update, self.sessions[chat_id])
            
            else:
                await update.message.reply_text("⚠️ Pilih menu dulu sebelum kirim foto.")
        else:
            await update.message.reply_text("⚠️ Silakan Login dulu.")