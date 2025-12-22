from datetime import datetime, timedelta
# UPDATE IMPORT
from core.config import TAB_RKM
from core.utils import parse_tanggal_indo

class ScheduleMixin:
    """Bagian Otak untuk Jadwal & Filter Tanggal"""

    async def menu_jadwal_handler(self, update, context, text, chat_id, session):
        # === A. SUB-MENU JADWAL ===
        if text == '1': # HARI INI
            await self.filter_jadwal(update, session['nama'], 'hari_ini')
        
        elif text == '2': # MINGGU INI
            await self.filter_jadwal(update, session['nama'], 'minggu_ini')
        
        elif text == '3': # BULAN INI
            await self.filter_jadwal(update, session['nama'], 'bulan_ini')
        
        elif text == '4': # SEMUA
            await self.filter_jadwal(update, session['nama'], 'semua')
        
        elif text == '5': # CARI MANUAL
            session['state'] = 'SEARCHING_DATE'
            await update.message.reply_text("🔍 **CARI TANGGAL**\nKetik tanggal (Cth: 10 November 2025):")
        
        elif text.lower() == 'batal':
            await self.tampilkan_menu_utama(update, session['nama'], "🔙 Kembali ke Menu.")
        
        else:
            await update.message.reply_text("Pilih angka 1-5 atau 'batal'.")

    async def filter_jadwal(self, update, nama_user, mode):
        # Refresh Data
        self.db_rkm = self.google.ambil_data(TAB_RKM)
        semua_jadwal = [r for r in self.db_rkm if r.get('Peserta') == nama_user]
        
        sekarang = datetime.now()
        hasil = []
        judul = ""

        if mode == 'hari_ini':
            judul = "HARI INI"
            for j in semua_jadwal:
                t = parse_tanggal_indo(j['Tanggal'])
                if t and t.date() == sekarang.date(): hasil.append(j)
        
        elif mode == 'minggu_ini':
            judul = "MINGGU INI"
            start = sekarang - timedelta(days=sekarang.weekday())
            end = start + timedelta(days=6)
            for j in semua_jadwal:
                t = parse_tanggal_indo(j['Tanggal'])
                if t and start.date() <= t.date() <= end.date(): hasil.append(j)

        elif mode == 'bulan_ini':
            judul = "BULAN INI"
            for j in semua_jadwal:
                t = parse_tanggal_indo(j['Tanggal'])
                if t and t.month == sekarang.month and t.year == sekarang.year: hasil.append(j)
        
        elif mode == 'semua':
            judul = "SELURUH WAKTU"
            hasil = semua_jadwal

        # Tampilkan
        if hasil:
            pesan = f"📅 **JADWAL {judul}:**\n"
            for j in hasil:
                status = "✅ Selesai" if j.get('Bukti Kehadiran') else "⏳ Belum Lapor"
                pesan += f"- {j['Kegiatan']}\n  🕒 {j['Tanggal']} ({status})\n\n"
            await update.message.reply_text(pesan)
        else:
            await update.message.reply_text(f"✅ Tidak ada jadwal untuk **{judul}**.")
        
        # Balik ke Menu Utama
        session = self.sessions[update.message.chat_id]
        await self.tampilkan_menu_utama(update, nama_user, "👇 Menu Utama:")

    async def cari_tanggal_manual(self, update, text, session):
        self.db_rkm = self.google.ambil_data(TAB_RKM)
        keyword = text.lower()
        hasil = [r for r in self.db_rkm if r.get('Peserta') == session['nama'] and keyword in r['Tanggal'].lower()]
        
        if hasil:
            pesan = f"🔍 **HASIL PENCARIAN '{text}':**\n"
            for j in hasil:
                status = "✅ Selesai" if j.get('Bukti Kehadiran') else "⏳"
                pesan += f"- {j['Kegiatan']} ({status})\n"
            await update.message.reply_text(pesan)
        else:
            await update.message.reply_text("❌ Tidak ditemukan.")
        
        await self.tampilkan_menu_utama(update, session['nama'])