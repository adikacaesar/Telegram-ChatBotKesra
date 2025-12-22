import os
import json
import gspread
import io
from datetime import datetime
from google.oauth2.credentials import Credentials as UserCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from .config import *

class GoogleService:
    def __init__(self):
        self.creds = self.get_creds()
        self.drive_service = build('drive', 'v3', credentials=self.creds)
        self.sheet_client = gspread.authorize(self.creds)
        self.NAMA_SPREADSHEET = NAMA_SPREADSHEET

    def get_creds(self):
        if os.path.exists(FILE_TOKEN):
            with open(FILE_TOKEN, 'r') as token:
                info = json.load(token)
                return UserCredentials.from_authorized_user_info(info)
        else:
            print("❌ ERROR: token.json hilang!")
            return None

    def ambil_data(self, nama_tab):
        try:
            sheet = self.sheet_client.open(NAMA_SPREADSHEET)
            worksheet = sheet.worksheet(nama_tab)
            return worksheet.get_all_records()
        except Exception as e:
            print(f"❌ Error ambil data {nama_tab}: {e}")
            return []

    def simpan_chat_id(self, id_pegawai, chat_id):
        try:
            sheet = self.sheet_client.open(NAMA_SPREADSHEET)
            worksheet = sheet.worksheet(TAB_PEGAWAI)
            cell = worksheet.find(str(id_pegawai))
            if cell:
                header = worksheet.row_values(1)
                if 'Chat_ID' in header:
                    col_index = header.index('Chat_ID') + 1 
                    worksheet.update_cell(cell.row, col_index, str(chat_id))
                    return True
            return False
        except Exception as e:
            print(f"❌ Error Simpan Chat ID: {e}")
            return False

    def upload_ke_drive(self, filepath, nama_file_baru):
        print(f"📤 Uploading Foto: {nama_file_baru}...")
        try:
            file_metadata = {'name': nama_file_baru, 'parents': [ID_FOLDER_DRIVE]}
            media = MediaFileUpload(filepath, mimetype='image/jpeg', resumable=True)
            file = self.drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
            return file.get('webViewLink')
        except Exception as e:
            print(f"❌ GAGAL UPLOAD: {e}")
            return None

    def upload_text_ke_drive(self, nama_file, isi_teks):
        print(f"📤 Uploading Catatan: {nama_file}...")
        try:
            file_metadata = {'name': nama_file, 'parents': [ID_FOLDER_DRIVE]}
            fh = io.BytesIO(isi_teks.encode('utf-8'))
            media = MediaIoBaseUpload(fh, mimetype='text/plain')
            file = self.drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
            return file.get('webViewLink')
        except Exception as e:
            print(f"❌ GAGAL UPLOAD TEXT: {e}")
            return None

    def update_bukti(self, nama_user, kegiatan, tanggal, link_bukti, jenis_laporan="HADIR"):
        """
        Update Excel RKM.
        REVISI: Menyesuaikan dengan struktur kolom baru user.
        """
        try:
            sheet = self.sheet_client.open(NAMA_SPREADSHEET)
            worksheet = sheet.worksheet(TAB_RKM)
            all_values = worksheet.get_all_values()
            header = all_values[0]
            
            # Mapping Index Kolom (Dinamis cari nama kolomnya)
            try:
                idx_peserta = header.index('Peserta')
                idx_kegiatan = header.index('Kegiatan')
                idx_tanggal = header.index('Tanggal')
                
                # Target Kolom Update
                col_bukti = header.index('Bukti Kehadiran') + 1
                col_timestamp = header.index('Timestamp') + 1
            except ValueError as ve:
                return False, f"Kolom tidak ditemukan di Excel: {ve}"
            
            # Cek Kolom Izin (Opsional, kalau belum dibuat user kita skip errornya)
            col_ket_izin = None
            if 'Keterangan Izin' in header:
                col_ket_izin = header.index('Keterangan Izin') + 1

            row_found = -1
            for i, row in enumerate(all_values):
                if i == 0: continue
                # Logic pencocokan (Peserta + Kegiatan + Tanggal)
                # Note: 'Tanggal' di excel user dipisah dengan jam, jadi aman dicocokkan stringnya
                if row[idx_peserta] == nama_user and row[idx_kegiatan] == kegiatan and row[idx_tanggal] == tanggal:
                    row_found = i + 1
                    break
            
            if row_found != -1:
                waktu_sekarang = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                
                if jenis_laporan == "HADIR":
                    worksheet.update_cell(row_found, col_bukti, link_bukti)
                    if col_ket_izin:
                        worksheet.update_cell(row_found, col_ket_izin, "-")
                else:
                    # Izin/Sakit
                    worksheet.update_cell(row_found, col_bukti, jenis_laporan)
                    if col_ket_izin:
                        worksheet.update_cell(row_found, col_ket_izin, link_bukti)

                worksheet.update_cell(row_found, col_timestamp, waktu_sekarang)
                return True, "Sukses"
            
            return False, "Data tidak ditemukan. Cek kesesuaian Nama/Kegiatan/Tanggal."
        except Exception as e:
            return False, str(e)