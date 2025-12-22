from telegram.ext import CommandHandler, MessageHandler, filters
from datetime import time
import pytz

def daftar_handlers(app, bot_logic):
    """
    Tugas: Mendaftarkan rute pesan (siapa menangani apa).
    """
    # 1. Command /start
    app.add_handler(CommandHandler('start', bot_logic.start))
    
    # 2. Pesan Teks (Menu & Inputan)
    # filters.TEXT & (~filters.COMMAND) artinya: Terima teks apa saja KECUALI perintah berawalan /
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), bot_logic.proses_pesan))
    
    # 3. Pesan Foto (Laporan/Bukti)
    app.add_handler(MessageHandler(filters.PHOTO, bot_logic.handle_photo))
    
    print("✅ Handlers terdaftar.")

def daftar_jobs(app, bot_logic):
    """
    Tugas: Mengatur jadwal otomatis (Cron Job).
    """
    if not app.job_queue:
        print("⚠️ JobQueue tidak aktif. Lewati setup jadwal.")
        return

    job_queue = app.job_queue
    wib = pytz.timezone('Asia/Jakarta')
    
    # --- SETUP WAKTU NOTIFIKASI ---
    # Jam 07:00 WIB Pagi
    jam_notif = time(hour=7, minute=0, second=0, tzinfo=wib)
    
    # Daftarkan tugas ke mesin waktu
    job_queue.run_daily(bot_logic.jalankan_notifikasi_pagi, jam_notif)
    
    print(f"⏰ Scheduler aktif: Notifikasi harian set pukul {jam_notif}")