from telegram.ext import ContextTypes
from datetime import datetime
import pytz 
from core.config import TAB_RKM
from core.utils import parse_tanggal_indo

class NotificationMixin:
    """Khusus menangani Notifikasi Otomatis (Cron Jobs)"""

    async def jalankan_notifikasi_pagi(self, context: ContextTypes.DEFAULT_TYPE):
        print("⏰ MENJALANKAN NOTIFIKASI OTOMATIS...")
        
        # 1. Refresh Data Terbaru
        self.db_rkm = self.google.ambil_data(TAB_RKM)
        
        # 2. Cek Tanggal Hari Ini (WIB)
        zona_wib = pytz.timezone('Asia/Jakarta')
        sekarang = datetime.now(zona_wib).date()

        if not self.sessions:
            print("⚠️ Tidak ada user yang login saat ini.")
            return

        for chat_id, data_session in self.sessions.items():
            nama_user = data_session['nama']
            
            # Cari jadwal user tersebut untuk HARI INI
            jadwal_hari_ini = []
            for baris in self.db_rkm:
                if baris.get('Peserta') == nama_user:
                    tgl_obj = parse_tanggal_indo(baris['Tanggal'])
                    if tgl_obj and tgl_obj.date() == sekarang:
                        status = "✅" if baris.get('Bukti Kehadiran') else "⏳"
                        jadwal_hari_ini.append(f"- {baris['Kegiatan']} ({status})")

            # Kirim Pesan
            if jadwal_hari_ini:
                pesan = (
                    f"☀️ **Selamat Pagi, {nama_user}!**\n"
                    f"Agenda hari ini ({sekarang.strftime('%d-%m-%Y')}):\n\n"
                    + "\n".join(jadwal_hari_ini)
                    + "\n\nSemangat! 💪"
                )
            else:
                pesan = (
                    f"☀️ **Selamat Pagi, {nama_user}!**\n"
                    f"Hari ini ({sekarang.strftime('%d-%m-%Y')}) **TIDAK ADA JADWAL** kegiatan.\n\n"
                    "Bisa fokus mengerjakan laporan lain atau istirahat sejenak. 👍"
                )

            try:
                await context.bot.send_message(chat_id=chat_id, text=pesan)
                print(f"✅ Notif terkirim ke {nama_user}")
            except Exception as e:
                print(f"❌ Gagal kirim ke {nama_user}: {e}")