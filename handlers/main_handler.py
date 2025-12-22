from telegram import Update
from telegram.ext import ContextTypes

# --- Import Config ---
from core.config import TAB_PEGAWAI, TAB_RKM

# --- Import Logika (Mixin) ---
from .auth import AuthMixin
from .schedule import ScheduleMixin
from .report import ReportMixin
from .notification import NotificationMixin # <-- File Baru
from .common import CommonMixin             # <-- File Baru

class BotHandler(AuthMixin, ScheduleMixin, ReportMixin, NotificationMixin, CommonMixin):
    """
    Kelas Utama (Router).
    Mewarisi kemampuan dari:
    - Auth (Login/Logout)
    - Schedule (Cek Jadwal)
    - Report (Izin/Sakit/Laporan)
    - Notification (Cron Job Pagi)
    - Common (Start/Menu)
    """
    
    def __init__(self, google_service):
        self.google = google_service
        self.sessions = {} # Memori Sesi User
        
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

        # 3. Arahkan ke Handler yang Tepat
        if state == 'MAIN_MENU':
            if text == '1':
                session['state'] = 'SUBMENU_JADWAL'
                await update.message.reply_text("📅 **MENU JADWAL**\n1️⃣ Hari Ini\n2️⃣ Minggu Ini\n3️⃣ Bulan Ini\n4️⃣ Semua\n5️⃣ Cari Tanggal\n❌ 'batal'")
            elif text == '2':
                await self.menu_upload_init(update, session)
            elif text.lower() == 'logout':
                await self.proses_logout(update, chat_id)
            else:
                await update.message.reply_text("Ketik 1, 2, atau 'logout'.")

        elif state == 'SUBMENU_JADWAL':
            await self.menu_jadwal_handler(update, context, text, chat_id, session)

        elif state == 'SEARCHING_DATE':
            await self.cari_tanggal_manual(update, text, session)

        # --- FLOW LAPORAN / IZIN / SAKIT (Checkpoint 3) ---
        elif state == 'SELECTING_RAPAT':
            await self.proses_pilih_rapat(update, text, session)

        elif state == 'SELECTING_STATUS':
            await self.proses_pilih_status(update, text, session)

        elif state == 'AWAITING_REASON_IZIN':
            await self.proses_terima_alasan_izin(update, session)

        elif state in ['AWAITING_PHOTO', 'AWAITING_PHOTO_SAKIT']:
            if text.lower() == 'batal':
                await self.tampilkan_menu_utama(update, session['nama'], "❌ Batal.")
            else:
                await update.message.reply_text("⚠️ Kirim FOTO ya (Surat Sakit/Bukti Kegiatan).")

    # --- HANDLER FOTO ---
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        if chat_id in self.sessions:
            state = self.sessions[chat_id]['state']
            
            if state == 'AWAITING_PHOTO':
                await self.proses_terima_foto(update, self.sessions[chat_id])
            elif state == 'AWAITING_PHOTO_SAKIT':
                await self.proses_terima_foto_sakit(update, self.sessions[chat_id])
            else:
                await update.message.reply_text("⚠️ Pilih menu dulu sebelum kirim foto.")
        else:
            await update.message.reply_text("⚠️ Silakan Login dulu.")