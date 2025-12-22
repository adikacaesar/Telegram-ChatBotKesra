import os
import socket

# Settingan Jaringan
socket.setdefaulttimeout(600)

# Telegram
TOKEN_TELEGRAM = "8219719062:AAH0CQnAIreirhk19dwG4SVgorwYy5vquz0"

# --- NAVIGASI FILE (VERSI SIMPEL) ---
# 1. Lokasi file ini (core/config.py)
CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Mundur satu langkah ke folder Project Utama (BotKesra/)
PROJECT_ROOT = os.path.dirname(CURRENT_FILE_DIR)

# 3. Cari file JSON langsung di folder Project Utama
FILE_TOKEN = os.path.join(PROJECT_ROOT, 'token.json')
FILE_CLIENT_SECRET = os.path.join(PROJECT_ROOT, 'client_secret.json')

print(f"📂 Config: Mencari Token di -> {FILE_TOKEN}")

# Google Drive & Sheets
NAMA_SPREADSHEET = 'DB_Kesra'
ID_FOLDER_DRIVE = "1CUbPoloof5IqYT7J02Vsj4yOBXBYdF7l" 

# Nama Tab
TAB_PEGAWAI = 'ID_Pegawai'
TAB_RKM = 'RKM'