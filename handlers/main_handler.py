from telegram import Update
from telegram.ext import ContextTypes

# --- Import Config ---
from core.config import TAB_PEGAWAI, TAB_RKM

# --- Import Logika (Mixin) ---
from .auth import AuthMixin
from .schedule import ScheduleMixin
from .report import ReportMixin
from .notification import NotificationMixin
from .common import CommonMixin
from .admin import AdminMixin # <-- FITUR ADMIN

class BotHandler(AuthMixin, ScheduleMixin, ReportMixin, NotificationMixin, CommonMixin, AdminMixin):
    """
    Kelas Utama (Router) yang mengatur lalu lintas pesan.
    
    Fitur:
    1. User: Login, Cek Jadwal, Lapor (Hadir/Izin/Sakit + Multi Upload).
    2. Admin: Tambah Jadwal via Wizard (Tanya-Jawab).
    3. System: Notifikasi Otomatis.
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
            elif text == '3':
                # Masuk Menu Admin (Wizard Tambah Jadwal)
                await self.admin_menu_init(update, session)
            elif text.lower() == 'logout':
                await self.proses_logout(update, chat_id)
            else:
                await update.message.reply_text("Ketik angka menu yang tersedia.")

        # B. SUBMENU JADWAL (USER)
        elif state == 'SUBMENU_JADWAL':
            await self.menu_jadwal_handler(update, context, text, chat_id, session)

        elif state == 'SEARCHING_DATE':
            await self.cari_tanggal_manual(update, text, session)

        # C. ALUR LAPORAN / STATUS (USER - MULTI UPLOAD)
        elif state == 'SELECTING_RAPAT':
            await self.proses_pilih_rapat(update, text, session)

        elif state == 'SELECTING_STATUS':
            await self.proses_pilih_status(update, text, session)

        elif state == 'AWAITING_REASON_IZIN':
            await self.proses_terima_alasan_izin(update, session)

        elif state in ['AWAITING_PHOTO', 'AWAITING_PHOTO_SAKIT']:
            if text.upper() == 'SELESAI':
                await self.proses_selesai_upload_foto(update, session)
            else:
                await update.message.reply_text("⚠️ Sedang mode terima foto.\nKirim foto (bisa banyak) atau ketik **SELESAI**.")

        elif state == 'AWAITING_FINAL_CAPTION':
            await self.proses_simpan_akhir(update, session)

        # D. ALUR ADMIN (WIZARD TAMBAH JADWAL)
        elif state == 'ADMIN_INPUT_TANGGAL':
            await self.admin_terima_tanggal(update, text, session)
            
        elif state == 'ADMIN_INPUT_JAM':
            await self.admin_terima_jam(update, text, session)
            
        elif state == 'ADMIN_INPUT_ID':
            await self.admin_terima_id(update, text, session)
            
        elif state == 'ADMIN_INPUT_NAMA_KEGIATAN':
            await self.admin_terima_nama(update, text, session)
            
        elif state == 'ADMIN_INPUT_LOKASI':
            await self.admin_terima_lokasi(update, text, session)
            
        elif state == 'ADMIN_INPUT_PESERTA':
            # Input nama/jabatan peserta, atau ketik 'SELESAI'
            await self.admin_terima_peserta(update, text, session)
            
        elif state == 'ADMIN_INPUT_STATUS_PESERTA':
            # Input status (Peserta/Tamu/dll)
            await self.admin_terima_status(update, text, session)

    # --- HANDLER FOTO ---
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        if chat_id in self.sessions:
            state = self.sessions[chat_id]['state']
            
            if state in ['AWAITING_PHOTO', 'AWAITING_PHOTO_SAKIT']:
                await self.proses_terima_foto(update, self.sessions[chat_id])
            else:
                await update.message.reply_text("⚠️ Pilih menu dulu sebelum kirim foto.")
        else:
            await update.message.reply_text("⚠️ Silakan Login dulu.")