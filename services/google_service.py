"""Handles all interactions with Google services like Sheets and Drive."""

import os
import logging
import gspread
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# --- Google Sheets Service ---
def add_row_to_sheet(data_row: list):
    """Appends a new row to the configured Google Sheet."""
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    if not sheet_id or not creds_path:
        logging.error("Google Sheet ID or Credentials Path not found in environment variables.")
        return

    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        gs_client = gspread.authorize(creds)
        
        sheet = gs_client.open_by_key(sheet_id).sheet1
        sheet.append_row(data_row)
        logging.info(f"Successfully added row to Google Sheet: {data_row}")
    except FileNotFoundError:
        logging.error(f"Credentials file not found at path: {creds_path}. Make sure the file exists.")
    except Exception as e:
        logging.error(f"An error occurred while writing to Google Sheets: {e}")

# --- Google Drive Service ---

def save_image(image_bytes: bytes, folder_name: str, file_name: str):
    """Saves image bytes to a specified local folder."""
    try:
        folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        subfolder_id = get_or_create_subfolder(folder_name, folder_id)
        link_drive = upload_image_to_drive(image_bytes, file_name, subfolder_id)
        return link_drive
    except Exception as e:
        logging.error(f"Error saving image: {e}")
        return None

def get_or_create_subfolder(folder_name: str, parent_id: str):
    """Busca una subcarpeta por nombre dentro de una carpeta padre. Si no existe, la crea."""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    try:
        scopes = ["https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        service = build('drive', 'v3', credentials=creds)

        query = (f"name = '{folder_name}' and "
                 f"'{parent_id}' in parents and "
                 f"mimeType = 'application/vnd.google-apps.folder' and "
                 f"trashed = false")
        
        results = service.files().list(q=query, fields="files(id)").execute()
        items = results.get('files', [])

        if items:
            logging.info(f"Subcarpeta encontrada: {folder_name} (ID: {items[0]['id']})")
            return items[0]['id']

        folder_metadata = {
            'name': folder_name,
            'parents': [parent_id],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        new_folder = service.files().create(body=folder_metadata, fields='id').execute()
        logging.info(f"Nueva subcarpeta creada: {folder_name} (ID: {new_folder['id']})")
        return new_folder.get('id')

    except Exception as e:
        logging.error(f"Error al gestionar la subcarpeta en Drive: {e}")
        return parent_id

def upload_image_to_drive(image_bytes: bytes, filename: str, folder_id: str):
    """Subes bytes de imagen a una carpeta de Drive y devuelve el link público."""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    try:
        scopes = ["https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        media = MediaIoBaseUpload(io.BytesIO(image_bytes), mimetype='image/jpeg', resumable=True)

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        service.permissions().create(
            fileId=file.get('id'),
            body={'type': 'anyone', 'role': 'viewer'}
        ).execute()

        logging.info(f"Archivo subido a Drive: {file.get('id')}")
        return file.get('webViewLink')

    except Exception as e:
        logging.error(f"Error subiendo a Google Drive: {e}")
        return None
