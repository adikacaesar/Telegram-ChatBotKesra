from telegram.ext import CommandHandler, MessageHandler, filters
from datetime import time
import pytz

def daftar_handlers(app, bot_logic):
    """
    Tugas: Mendaftarkan rute pesan (siapa menangani apa).
    """
    # 1. Command /start (Menu Awal)
    app.add_handler(CommandHandler('start', bot_logic.start))
    
    # 2. Pesan Teks (Menu & Inputan Wizard)
    # filters.TEXT & (~filters.COMMAND) artinya: Terima teks apa saja KECUALI perintah berawalan /
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), bot_logic.proses_pesan))
    
    # 3. Pesan Foto (Laporan Kehadiran / Upload Surat berupa Gambar)
    app.add_handler(MessageHandler(filters.PHOTO, bot_logic.handle_photo))

    # 4. Pesan Dokumen (Upload Surat berupa PDF) <-- NEW
    # Ini penting agar fitur Upload Surat Resmi bisa menerima file PDF
    app.add_handler(MessageHandler(filters.Document.ALL, bot_logic.handle_document))
    
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
    # Bot akan memanggil fungsi 'jalankan_notifikasi_pagi' setiap hari jam 07.00
    job_queue.run_daily(bot_logic.jalankan_notifikasi_pagi, jam_notif)
    
    print(f"⏰ Scheduler aktif: Notifikasi harian set pukul {jam_notif}")