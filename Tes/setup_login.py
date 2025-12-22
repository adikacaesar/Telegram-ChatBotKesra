import os
from google_auth_oauthlib.flow import InstalledAppFlow

# --- KONFIGURASI LOKASI FILE (SUPAYA TIDAK NYASAR) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SECRETS_DIR = os.path.join(BASE_DIR, 'secrets')

# Target Lokasi File
FILE_CLIENT_SECRET = os.path.join(SECRETS_DIR, 'client_secret.json')
FILE_TOKEN = os.path.join(SECRETS_DIR, 'token.json')

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

def login_google():
    # 1. Cek apakah client_secret.json ada di dalam folder secrets?
    if not os.path.exists(FILE_CLIENT_SECRET):
        print(f"❌ ERROR: File KTP tidak ditemukan!")
        print(f"👉 Sistem mencari di: {FILE_CLIENT_SECRET}")
        print("Pastikan kamu sudah memindahkan 'client_secret.json' ke dalam folder 'secrets'.")
        return

    print("🌍 Membuka Browser untuk Login ulang...")
    
    # 2. Proses Login
    try:
        flow = InstalledAppFlow.from_client_secrets_file(FILE_CLIENT_SECRET, SCOPES)
        creds = flow.run_local_server(port=0)
        
        # 3. Simpan Token LANGSUNG ke folder secrets
        with open(FILE_TOKEN, 'w') as token:
            token.write(creds.to_json())
        
        print(f"\n✅ LOGIN SUKSES!")
        print(f"📄 Token baru berhasil disimpan di: {FILE_TOKEN}")
        print("🚀 Sekarang coba jalankan main.py lagi!")
        
    except Exception as e:
        print(f"❌ Gagal Login: {e}")

if __name__ == '__main__':
    login_google()