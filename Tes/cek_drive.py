from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# --- KONFIGURASI ---
FILE_KUNCI = 'credentials.json'

try:
    # 1. Login sebagai Bot
    creds = Credentials.from_service_account_file(
        FILE_KUNCI, 
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build('drive', 'v3', credentials=creds)
    
    # 2. Cek Siapa Saya?
    about = service.about().get(fields="user").execute()
    print(f"🤖 SAYA LOGIN SEBAGAI: {about['user']['emailAddress']}")
    print("-" * 30)

    # 3. Coba Cari Folder 'Bukti Rapat' Spesifik
    ID_TARGET = "1CUbPoloof5lqYT7J02Vsj4yOBXBYdF7I"
    try:
        folder = service.files().get(fileId=ID_TARGET, fields="name").execute()
        print(f"✅ Folder Target DITEMUKAN: {folder['name']}")
    except Exception as e:
        print(f"❌ Folder Target TIDAK KETEMU (Error 404).")
        print("   Artinya bot ini belum melihat folder tersebut.")

    print("-" * 30)
    # 4. List Semua Folder yang Bisa Dilihat Bot
    print("📂 DAFTAR SEMUA FOLDER YANG SAYA LIHAT:")
    results = service.files().list(
        q="mimeType = 'application/vnd.google-apps.folder'",
        fields="files(id, name)"
    ).execute()
    
    items = results.get('files', [])
    if not items:
        print("(Kosong. Bot tidak melihat folder apapun)")
    else:
        for item in items:
            print(f"- {item['name']} (ID: {item['id']})")

except Exception as e:
    print(f"ERROR FATAL: {e}")