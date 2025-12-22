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
        # Service untuk Google Drive
        self.drive_service = build('drive', 'v3', credentials=self.creds)
        # Service untuk Google Sheets (Gspread)
        self.sheet_client = gspread.authorize(self.creds)

    def get_creds(self):
        # Menggunakan FILE_TOKEN dari config.py yang sudah path-nya benar
        if os.path.exists(FILE_TOKEN):
            with open(FILE_TOKEN, 'r') as token:
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

    def simpan_chat_id(self, id_pegawai, chat_id):
        """Menyimpan ID Telegram user ke Tab Pegawai (Fitur Baru)"""
        print(f"💾 Menyimpan Chat ID: {chat_id} untuk Pegawai: {id_pegawai}...")
        try:
            sheet = self.sheet_client.open(NAMA_SPREADSHEET)
            worksheet = sheet.worksheet(TAB_PEGAWAI)
            
            # 1. Cari Baris Pegawai berdasarkan ID (Harus string agar cocok)
            cell = worksheet.find(str(id_pegawai))
            
            if cell:
                # 2. Cari Kolom 'Chat_ID' secara otomatis di baris header (baris 1)
                header = worksheet.row_values(1) 
                try:
                    # Tambah +1 karena gspread index mulai dari 1, sedangkan list python dari 0
                    col_index = header.index('Chat_ID') + 1 
                except ValueError:
                    print("❌ Kolom 'Chat_ID' tidak ditemukan di Excel! Pastikan nama kolomnya benar.")
                    return False

                # 3. Update Cell
                # cell.row adalah baris pegawai, col_index adalah kolom Chat_ID
                worksheet.update_cell(cell.row, col_index, str(chat_id))
                print(f"✅ Berhasil menyimpan Chat ID {chat_id} untuk ID {id_pegawai}")
                return True
            else:
                print(f"❌ ID Pegawai {id_pegawai} tidak ditemukan di Excel.")
                return False
                
        except Exception as e:
            print(f"❌ Error Simpan Chat ID: {e}")
            return False

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
            
            # Index target (ditambah 1 karena gspread start from 1)
            col_bukti = header.index('Bukti Kehadiran') + 1
            col_timestamp = header.index('Timestamp') + 1

            # Cari Baris
            row_found = -1
            for i, row in enumerate(all_values):
                if i == 0: continue # Skip header
                # Logika pencocokan baris
                if row[idx_peserta] == nama_user and row[idx_kegiatan] == kegiatan and row[idx_tanggal] == tanggal:
                    row_found = i + 1 # +1 karena index python mulai 0, spreadsheet mulai 1
                    break
            
            if row_found != -1:
                waktu_sekarang = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                
                # Update 2 cell sekaligus
                worksheet.update_cell(row_found, col_bukti, link_bukti)
                worksheet.update_cell(row_found, col_timestamp, waktu_sekarang)
                return True, "Sukses"
            
            return False, "Baris data tidak ditemukan (Mungkin salah tanggal/kegiatan)"
        except Exception as e:
            return False, str(e)