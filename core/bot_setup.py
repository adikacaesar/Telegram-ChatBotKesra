from telegram.ext import CommandHandler, MessageHandler, filters
from datetime import time
import pytz

def daftar_handlers(app, bot_logic):
    """
    Tugas: Mendaftarkan rute pesan (siapa menangani apa).
    """
    # 1. Command /start
    app.add_handler(CommandHandler('start', bot_logic.proses_pesan))
    
    # 2. Pesan Teks (Menu & Inputan Wizard)
    # filters.TEXT & (~filters.COMMAND) artinya: Terima teks apa saja KECUALI perintah
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), bot_logic.proses_pesan))
    
    # 3. Pesan Foto (Laporan Kehadiran / Upload Surat)
    app.add_handler(MessageHandler(filters.PHOTO, bot_logic.handle_photo))

    # 4. Pesan Dokumen (Upload Surat PDF)
    app.add_handler(MessageHandler(filters.Document.ALL, bot_logic.handle_document))
    
    print("✅ Handlers terdaftar.")

def daftar_jobs(app, bot_logic):
    """
    Tugas: Mengatur jadwal otomatis (Cron Job) yang DINAMIS dari Excel.
    """
    if not app.job_queue:
        print("⚠️ JobQueue tidak aktif. Lewati setup jadwal.")
        return

    job_queue = app.job_queue
    wib = pytz.timezone('Asia/Jakarta')
    
    print("⏰ Memuat Konfigurasi Notifikasi dari Excel...")

    # Kita gunakan akses ke Google Service yang sudah ada di bot_logic
    # Jadi tidak perlu bikin koneksi baru (Hemat Resource)
    try:
        items = bot_logic.google.ambil_config_notif()
    except Exception as e:
        print(f"❌ Gagal baca config notif: {e}")
        items = []
    
    count = 0
    for item in items:
        # Cek Status ON/OFF
        if item.get('Status') == 'ON':
            try:
                waktu_str = str(item['Waktu'])
                h, m = map(int, waktu_str.split(':'))
                jam_notif = time(hour=h, minute=m, second=0, tzinfo=wib)
                
                # Ambil Pesan & Target
                pesan = item.get('Pesan', 'Cek Jadwal')
                target = item.get('Target', 'ALL')

                # Pasang Alarm
                job_queue.run_daily(
                    bot_logic.jalankan_notifikasi_pagi, 
                    jam_notif,
                    name=f"notif_{waktu_str}", # ID Unik untuk fitur hapus nanti
                    data={'pesan': pesan, 'target': target} # Data dikirim ke notification.py
                )
                count += 1
                print(f"   ✅ Terjadwal: {waktu_str} WIB [{target}]")
                
            except Exception as e:
                print(f"   ⚠️ Skip jadwal {item.get('Waktu')}: {e}")

    print(f"✅ Total {count} jadwal notifikasi aktif!")