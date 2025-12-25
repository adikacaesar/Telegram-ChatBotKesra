from telegram import Update
from telegram.ext import ContextTypes

# --- Import Config ---
from core.config import TAB_PEGAWAI, TAB_RKM

# --- Import Semua Logika (Mixin) ---
from .auth import AuthMixin
from .schedule import ScheduleMixin
from .notification import NotificationMixin
from .common import CommonMixin

# Pecahan Report (User)
from .report_menu import ReportMenuMixin
from .report_action import ReportActionMixin

# Pecahan Admin (Manajemen)
from .admin_wizard import AdminWizardMixin
from .admin_action import AdminActionMixin
from .admin_config import AdminConfigMixin 

class BotHandler(
    AuthMixin, 
    ScheduleMixin, 
    NotificationMixin, 
    CommonMixin, 
    ReportMenuMixin,
    ReportActionMixin,
    AdminWizardMixin,
    AdminActionMixin,
    AdminConfigMixin 
):
    """
    Router Utama Bot Kesra.
    """
    
    def __init__(self, google_service):
        self.google = google_service
        self.sessions = {} 
        
        print("🔄 Memuat Database...")
        self.db_pegawai = self.google.ambil_data(TAB_PEGAWAI)
        self.db_rkm = self.google.ambil_data(TAB_RKM)
        print("✅ Database Siap!")

    # --- ROUTER PESAN TEKS ---
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
        
        # --- GLOBAL CANCEL ---
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
                await self.menu_upload_init(update, session)
            elif text == '3':
                await self.admin_menu_init(update, session)
            elif text == '4':
                await self.admin_upload_surat_init(update, session)
            
            # --- MENU 5 ---
            elif text == '5':
                await self.menu_config_notif(update, session)

            elif text.lower() == 'logout':
                await self.proses_logout(update, chat_id)
            else:
                await update.message.reply_text("Ketik angka menu yang tersedia.")

        # B. SUBMENU JADWAL
        elif state == 'SUBMENU_JADWAL':
            await self.menu_jadwal_handler(update, context, text, chat_id, session)
        elif state == 'SEARCHING_DATE':
            await self.cari_tanggal_manual(update, text, session)

        # C. ALUR LAPORAN
        elif state == 'SELECTING_RAPAT':
            await self.proses_pilih_rapat(update, text, session)
        elif state == 'SELECTING_STATUS':
            await self.proses_pilih_status(update, text, session)
        elif state == 'AWAITING_REASON_IZIN':
            await self.proses_terima_alasan_izin(update, session)
        elif state == 'AWAITING_PHOTO' or state == 'AWAITING_PHOTO_SAKIT':
            if text.upper() == 'SELESAI':
                await self.proses_selesai_upload_foto(update, session)
            else:
                await update.message.reply_text("⚠️ Sedang mode terima foto. Kirim foto atau ketik **SELESAI**.")
        elif state == 'AWAITING_FINAL_CAPTION':
            await self.proses_simpan_akhir(update, session)

        # D. ALUR ADMIN: TAMBAH JADWAL
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
            await self.admin_terima_peserta(update, text, session)
        elif state == 'ADMIN_INPUT_STATUS_PESERTA':
            await self.admin_terima_status(update, text, session)

        # E. ALUR ADMIN: UPLOAD SURAT
        elif state == 'ADMIN_SELECT_EVENT_FOR_LETTER':
            await self.admin_terima_pilihan_surat(update, text, session)

        # F. [BARU] ALUR ADMIN: CONFIG NOTIFIKASI
        # PERHATIKAN: Saya menambahkan 'context' di 3 baris di bawah ini
        elif state == 'CONFIG_MENU':
            await self.config_process_menu(update, context, text, session) # <--- TAMBAH CONTEXT
        elif state == 'CONFIG_ADD_TIME':
            await self.config_add_time(update, text, session)
        elif state == 'CONFIG_SELECT_TARGET':
            await self.config_select_target(update, text, session)
        elif state == 'CONFIG_ADD_MSG':
            await self.config_add_msg(update, text, session)
        elif state == 'CONFIG_CONFIRM_TEST':
            await self.config_confirm_test(update, context, text, session) # <--- TAMBAH CONTEXT
        elif state == 'CONFIG_DELETE':
            await self.config_delete(update, context, text, session)       # <--- TAMBAH CONTEXT
        elif state == 'BROADCAST_INPUT':
            await self.broadcast_process(update, text, session)


    # --- HANDLER FOTO ---
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        if chat_id in self.sessions:
            state = self.sessions[chat_id]['state']
            
            if state in ['AWAITING_PHOTO', 'AWAITING_PHOTO_SAKIT']:
                await self.proses_terima_foto(update, self.sessions[chat_id])
            elif state == 'ADMIN_UPLOAD_LETTER_FILE':
                await self.admin_proses_file_surat(update, self.sessions[chat_id])
            else:
                await update.message.reply_text("⚠️ Pilih menu dulu sebelum kirim foto.")
        else:
            await update.message.reply_text("⚠️ Silakan Login dulu.")

    # --- HANDLER DOKUMEN ---
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        if chat_id in self.sessions:
            state = self.sessions[chat_id]['state']
            
            if state == 'ADMIN_UPLOAD_LETTER_FILE':
                await self.admin_proses_file_surat(update, self.sessions[chat_id])
            else:
                await update.message.reply_text("⚠️ Kirim dokumen hanya saat diminta.")
        else:
            await update.message.reply_text("⚠️ Silakan Login dulu.")