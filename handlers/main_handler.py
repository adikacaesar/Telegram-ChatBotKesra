from telegram import Update
from telegram.ext import ContextTypes

# --- UPDATE: Import Config dari folder 'core' ---
from core.config import *

# --- Import Logika (Mixin) dari folder yang sama ---
from .auth import AuthMixin
from .schedule import ScheduleMixin
from .report import ReportMixin

class BotHandler(AuthMixin, ScheduleMixin, ReportMixin):
    """
    Kelas Utama yang mewarisi kemampuan:
    1. AuthMixin (Login/Logout)
    2. ScheduleMixin (Jadwal)
    3. ReportMixin (Laporan)
    """
    
    def __init__(self, google_service):
        self.google = google_service
        self.sessions = {}
        
        print("🔄 Memuat Database...")
        self.db_pegawai = self.google.ambil_data(TAB_PEGAWAI)
        self.db_rkm = self.google.ambil_data(TAB_RKM)
        print("✅ Database Siap!")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user.first_name
        await update.message.reply_text(f"Halo {user}! (Versi Modular)\nSilakan Login ID Pegawai.")

    # --- FUNGSI HELPER (Dipakai Bersama) ---
    async def tampilkan_menu_utama(self, update, nama_user, pesan_tambahan=""):
        self.sessions[update.message.chat_id]['state'] = 'MAIN_MENU'
        self.sessions[update.message.chat_id]['selected_rapat'] = None # Reset pilihan
        
        text = (f"{pesan_tambahan}\n\n" if pesan_tambahan else "")
        text += f"✅ Halo **{nama_user}**!\n1️⃣ Cek Jadwal\n2️⃣ Upload Laporan"
        await update.message.reply_text(text)

    # --- ROUTER UTAMA (Pengarah Lalu Lintas) ---
    async def proses_pesan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text.strip() if update.message.text else ""
        chat_id = update.message.chat_id

        # 1. JIKA BELUM LOGIN
        if chat_id not in self.sessions:
            await self.proses_login(update, context, text, chat_id)
            return

        # 2. JIKA SUDAH LOGIN
        session = self.sessions[chat_id]
        state = session['state']

        # -- MENU UTAMA --
        if state == 'MAIN_MENU':
            if text == '1': # Masuk Submenu Jadwal
                session['state'] = 'SUBMENU_JADWAL'
                await update.message.reply_text(
                    "📅 **MENU JADWAL**\n1️⃣ Hari Ini\n2️⃣ Minggu Ini\n3️⃣ Bulan Ini\n4️⃣ Semua\n5️⃣ Cari Tanggal\n❌ 'batal'"
                )
            elif text == '2': # Masuk Menu Upload
                await self.menu_upload_init(update, session)
            elif text.lower() == 'logout':
                await self.proses_logout(update, chat_id)
            else:
                await update.message.reply_text("Ketik 1, 2, atau 'logout'.")

        # -- SUBMENU JADWAL --
        elif state == 'SUBMENU_JADWAL':
            await self.menu_jadwal_handler(update, context, text, chat_id, session)

        # -- CARI TANGGAL --
        elif state == 'SEARCHING_DATE':
            await self.cari_tanggal_manual(update, text, session)

        # -- PILIH RAPAT (UPLOAD) --
        elif state == 'SELECTING_RAPAT':
            await self.proses_pilih_rapat(update, text, session)

        # -- MENUNGGU FOTO --
        elif state == 'AWAITING_PHOTO':
            if text.lower() == 'batal':
                await self.tampilkan_menu_utama(update, session['nama'], "❌ Batal.")
            else:
                await update.message.reply_text("⚠️ Kirim FOTO ya.")

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        if chat_id in self.sessions and self.sessions[chat_id]['state'] == 'AWAITING_PHOTO':
            await self.proses_terima_foto(update, self.sessions[chat_id])
        else:
            await update.message.reply_text("⚠️ Pilih menu dulu.")