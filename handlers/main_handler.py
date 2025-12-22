from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
import pytz # <-- IMPORT BARU

# --- Import Config & Utils ---
from core.config import *
from core.utils import parse_tanggal_indo # <-- IMPORT BARU

# --- Import Logika (Mixin) ---
from .auth import AuthMixin
from .schedule import ScheduleMixin
from .report import ReportMixin

class BotHandler(AuthMixin, ScheduleMixin, ReportMixin):
    def __init__(self, google_service):
        self.google = google_service
        self.sessions = {} # Mengingat user yang login
        
        print("🔄 Memuat Database...")
        self.db_pegawai = self.google.ambil_data(TAB_PEGAWAI)
        self.db_rkm = self.google.ambil_data(TAB_RKM)
        print("✅ Database Siap!")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user.first_name
        await update.message.reply_text(f"Halo {user}!\nSilakan ketik **ID Pegawai** untuk Login.")

    # --- JOB QUEUE: NOTIFIKASI PAGI (FITUR BARU) ---
    async def jalankan_notifikasi_pagi(self, context: ContextTypes.DEFAULT_TYPE):
        """
        Fungsi ini akan dipanggil otomatis oleh JobQueue setiap pagi.
        """
        print("⏰ MENJALANKAN NOTIFIKASI OTOMATIS...")
        
        # 1. Refresh Data Terbaru dari Spreadsheet
        self.db_rkm = self.google.ambil_data(TAB_RKM)
        
        # 2. Cek Tanggal Hari Ini
        zona_wib = pytz.timezone('Asia/Jakarta')
        sekarang = datetime.now(zona_wib).date()

        # 3. Loop ke semua User yang sedang LOGIN
        # (Catatan: Jika bot direstart, user harus login ulang agar masuk list ini)
        if not self.sessions:
            print("⚠️ Tidak ada user yang login saat ini.")
            return

        for chat_id, data_session in self.sessions.items():
            nama_user = data_session['nama']
            
            # Cari jadwal user tersebut untuk HARI INI
            jadwal_hari_ini = []
            for baris in self.db_rkm:
                # Cek Nama
                if baris.get('Peserta') == nama_user:
                    # Cek Tanggal
                    tgl_obj = parse_tanggal_indo(baris['Tanggal'])
                    if tgl_obj and tgl_obj.date() == sekarang:
                        # Cek apakah sudah selesai/belum
                        status = "✅" if baris.get('Bukti Kehadiran') else "⏳"
                        jadwal_hari_ini.append(f"- {baris['Kegiatan']} ({status})")

# 4. Kirim Pesan (LOGIKA DIPERBARUI)
            if jadwal_hari_ini:
                # Kalo ada jadwal
                pesan = (
                    f"☀️ **Selamat Pagi, {nama_user}!**\n"
                    f"Jangan lupa agenda hari ini ({sekarang.strftime('%d-%m-%Y')}):\n\n"
                    + "\n".join(jadwal_hari_ini)
                    + "\n\nSemangat Magangnya! 💪"
                )
            else:
                # Kalo TIDAK ADA jadwal (Else baru)
                pesan = (
                    f"☀️ **Selamat Pagi, {nama_user}!**\n"
                    f"Hari ini ({sekarang.strftime('%d-%m-%Y')}) **TIDAK ADA JADWAL** kegiatan.\n\n"
                    "Bisa fokus mengerjakan laporan yang belum selesai atau istirahat sejenak. 👍"
                )

            # Kirim Pesan (Berlaku untuk ada jadwal maupun kosong)
            try:
                await context.bot.send_message(chat_id=chat_id, text=pesan)
                print(f"✅ Notif terkirim ke {nama_user}")
            except Exception as e:
                print(f"❌ Gagal kirim ke {nama_user}: {e}")

    # --- FUNGSI HELPER ---
    async def tampilkan_menu_utama(self, update, nama_user, pesan_tambahan=""):
        self.sessions[update.message.chat_id]['state'] = 'MAIN_MENU'
        self.sessions[update.message.chat_id]['selected_rapat'] = None
        
        text = (f"{pesan_tambahan}\n\n" if pesan_tambahan else "")
        text += f"✅ Halo **{nama_user}**!\n1️⃣ Cek Jadwal\n2️⃣ Upload Laporan"
        await update.message.reply_text(text)

    # --- ROUTER PESAN ---
    async def proses_pesan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text.strip() if update.message.text else ""
        chat_id = update.message.chat_id

        if chat_id not in self.sessions:
            await self.proses_login(update, context, text, chat_id)
            return

        session = self.sessions[chat_id]
        state = session['state']

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

        elif state == 'SELECTING_RAPAT':
            await self.proses_pilih_rapat(update, text, session)

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