import gspread
from google.oauth2.service_account import Credentials

# --- KONFIGURASI SESUAI SCREENSHOT ---
FILE_KUNCI = 'credentials.json'
NAMA_FILE_SPREADSHEET = 'DB_Kesra'  # Nama File di pojok kiri atas
NAMA_TAB_WORKSHEET = 'ID_Pegawai'   # Nama Tab di bawah

print("Sedang mencoba membuka gerbang Google Sheet...")

try:
    # 1. Setup Izin
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # 2. Login
    creds = Credentials.from_service_account_file(FILE_KUNCI, scopes=scopes)
    client = gspread.authorize(creds)
    
    # 3. Buka File "DB_Kesra"
    sheet = client.open(NAMA_FILE_SPREADSHEET)
    
    # 4. Ambil Tab Spesifik "ID_Pegawai"
    worksheet = sheet.worksheet(NAMA_TAB_WORKSHEET)
    
    # 5. Baca Semua Data
    data_semua = worksheet.get_all_records()
    
    print("✅ BERHASIL TERHUBUNG!")
    print(f"Total Pegawai ditemukan: {len(data_semua)} orang.")
    
    # Cek Data Baris Pertama (Harusnya Adika / ID 101)
    if len(data_semua) > 0:
        pegawai_pertama = data_semua[0]
        print("\n--- Contoh Data Baris Pertama ---")
        print(f"Nama : {pegawai_pertama.get('Nama')}")
        print(f"ID   : {pegawai_pertama.get('ID_Pegawai')}")
        print(f"Jabatan: {pegawai_pertama.get('Jabatan 1')}")
        
except Exception as e:
    print(f"\n❌ GAGAL: {e}")
    print("\n⚠️ PENTING: Sudahkah kamu klik tombol SHARE di file 'DB_Kesra'?")
    print("Pastikan email bot (dari credentials.json) sudah dijadikan EDITOR di file tersebut.")