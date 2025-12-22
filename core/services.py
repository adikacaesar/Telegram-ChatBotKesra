# services.py
import os
import json
import gspread
from datetime import datetime
from google.oauth2.credentials import Credentials as UserCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from .config import *

class GoogleService:
    def __init__(self):
        self.creds = self.get_creds()
        self.drive_service = build('drive', 'v3', credentials=self.creds)
        self.sheet_client = gspread.authorize(self.creds)

    def get_creds(self):
        if os.path.exists('token.json'):
            with open('token.json', 'r') as token:
                info = json.load(token)
                return UserCredentials.from_authorized_user_info(info)
        else:
            print("❌ ERROR: token.json hilang!")
            return None

    def ambil_data(self, nama_tab):
        """Mengambil semua data dari sheet tertentu"""
        try:
            sheet = self.sheet_client.open(NAMA_SPREADSHEET)
            worksheet = sheet.worksheet(nama_tab)
            return worksheet.get_all_records()
        except Exception as e:
            print(f"❌ Error ambil data {nama_tab}: {e}")
            return []

    def upload_ke_drive(self, filepath, nama_file_baru):
        """Upload file ke Google Drive"""
        print(f"📤 Uploading: {nama_file_baru}...")
        try:
            file_metadata = {'name': nama_file_baru, 'parents': [ID_FOLDER_DRIVE]}
            media = MediaFileUpload(filepath, mimetype='image/jpeg', resumable=True)
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            link = file.get('webViewLink')
            print(f"✅ SUKSES! Link: {link}")
            return link
        except Exception as e:
            print(f"❌ GAGAL UPLOAD: {e}")
            return None

    def update_bukti(self, nama_user, kegiatan, tanggal, link_bukti):
        """Update Link Bukti & Timestamp di Excel"""
        try:
            sheet = self.sheet_client.open(NAMA_SPREADSHEET)
            worksheet = sheet.worksheet(TAB_RKM)
            
            all_values = worksheet.get_all_values()
            header = all_values[0]
            
            # Cari Index Kolom
            idx_peserta = header.index('Peserta')
            idx_kegiatan = header.index('Kegiatan')
            idx_tanggal = header.index('Tanggal')
            col_bukti = header.index('Bukti Kehadiran') + 1
            col_timestamp = header.index('Timestamp') + 1

            # Cari Baris
            row_found = -1
            for i, row in enumerate(all_values):
                if i == 0: continue
                if row[idx_peserta] == nama_user and row[idx_kegiatan] == kegiatan and row[idx_tanggal] == tanggal:
                    row_found = i + 1
                    break
            
            if row_found != -1:
                waktu_sekarang = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                worksheet.update_cell(row_found, col_bukti, link_bukti)
                worksheet.update_cell(row_found, col_timestamp, waktu_sekarang)
                return True, "Sukses"
            return False, "Baris tidak ketemu"
        except Exception as e:
            return False, str(e)