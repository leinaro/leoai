"""Handles all interactions with Google services like Sheets and Drive."""

import os
import logging
import gspread
import io
import json
import datetime
from typing import Optional, Tuple

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from google.auth import default

from .secrets import get_secret # Import our secret helper

# --- Helper for Authentication ---

def _get_google_creds() -> Optional[Tuple[Credentials, str, str]]:
    """Retrieves Google credentials and configuration from Secret Manager."""
        
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets", 
            "https://www.googleapis.com/auth/drive"
        ]
        creds, project_id = default(scopes=scopes)
        
        sheet_id = get_secret("GOOGLE_SHEET_ID")
        drive_folder_id = get_secret("GOOGLE_DRIVE_FOLDER_ID")

        if not all([sheet_id, drive_folder_id]):
            logging.error("One or more Google secrets are missing from Secret Manager.")
            return None, None, None

        return creds, sheet_id, drive_folder_id
    
    except (json.JSONDecodeError, TypeError) as e:
        logging.error(f"Failed to parse Google credentials JSON: {e}")
        return None, None, None

# --- Google Sheets Service ---

def add_row_to_sheet(data_row: list):
    """Appends a new row to the configured Google Sheet."""
    creds, sheet_id, _ = _get_google_creds()
    if not creds:
        logging.error("Google Sheet ID or Credentials Path not found in environment variables.")
        return

    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds, project_id = default(scopes=scopes)
        gs_client = gspread.authorize(creds)
        sheet = gs_client.open_by_key(sheet_id).sheet1
        sheet.append_row(data_row)
        logging.info(f"Successfully added row to Google Sheet: {data_row}")
    except FileNotFoundError:
        logging.error(f"Credentials file not found at path: {creds_path}. Make sure the file exists.")
    except Exception as e:
        logging.error(f"An error occurred while writing to Google Sheets: {e}")

# --- Google Drive Service ---

def save_file(file_bytes: bytes, date: str, file_name: str, mimetype: str):
    """Saves image bytes to a specified local folder."""
    try:
        
        folder_id = get_secret("GOOGLE_DRIVE_FOLDER_ID")
        target_folder_id = get_folder_id_by_date(folder_id, date)
        #subfolder_id = get_or_create_subfolder(folder_name, folder_id)
        #link_drive = upload_image_to_drive(image_bytes, file_name, target_folder_id)
        link_drive = upload_file_to_drive(file_bytes, file_name, target_folder_id, mimetype)
        return link_drive
    except Exception as e:
        logging.error(f"Error saving file to Drive: {e}")
        return None


def get_folder_id_by_date(root_id, full_date):
    """
    Obtiene la ruta Año/Mes (ej: 2025/01).
    Retorna el ID de la carpeta del mes final.
    """
    date = datetime.strptime(full_date, "%Y-%m-%d %H:%M:%S")
    year = date.strftime("%Y")  # "2025"
    month = dare.strftime("%m")   # "01"

    # 1. Buscar/Crear carpeta del Año
    year_id = get_or_create_subfolder(year, root_id)
    
    # 2. Buscar/Crear carpeta del Mes dentro del Año
    month_id = get_or_create_subfolder(month, year_id_id)
    
    return month_id

def get_or_create_subfolder(folder_name: str, parent_id: str):
    """Busca una subcarpeta por nombre dentro de una carpeta padre. Si no existe, la crea."""
    
    try:
        scopes = ["https://www.googleapis.com/auth/drive"]
        creds, project_id = default(scopes=scopes)

        service = build('drive', 'v3', credentials=creds)

        query = (f"name = '{folder_name}' and "
                 f"'{parent_id}' in parents and "
                 f"mimeType = 'application/vnd.google-apps.folder' and "
                 f"trashed = false")
        
        results = service.files().list(
            q=query, 
            fields="files(id)",
            supportsAllDrives=True,  # Added for Shared Drive compatibility
            includeItemsFromAllDrives=True  # Added for Shared Drive compatibility
        ).execute()
        
        items = results.get('files', [])
    

        if items:
            logging.info(f"Subcarpeta encontrada: {folder_name} (ID: {items[0]['id']})")
            return items[0]['id']
       
        logging.info(f"Subcarpeta no encontrada: {folder_name}, usando padre (ID: {parent_id})")
        return parent_id

    except Exception as e:
        logging.error(f"Error al gestionar la subcarpeta en Drive: {e}")
        return parent_id

def upload_image_to_drive(image_bytes: bytes, filename: str, folder_id: str):
    
    try:
        scopes = ["https://www.googleapis.com/auth/drive"]
        creds, project_id = default(scopes=scopes)
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        media = MediaIoBaseUpload(
            io.BytesIO(image_bytes), 
            mimetype='image/jpeg', 
            resumable=False
        )

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink',
            # Esto ayuda a que Google entienda que se sube a un recurso compartido
            supportsAllDrives=True 
        ).execute()

        # Si quieres que Leo pueda leerlo luego, esto está bien
        service.permissions().create(
            fileId=file.get('id'),
            body={'type': 'anyone', 'role': 'viewer'}
        ).execute()

        return file.get('webViewLink')

    except Exception as e:
        logging.error(f"Error subiendo a Google Drive: {e}")
        return None

def upload_file_to_drive(file_bytes: bytes, filename: str, folder_id: str, mimetype: str):
    """
    Sube cualquier tipo de archivo (imagen, PDF, etc.) a Drive.
    """

    try:
        scopes = ["https://www.googleapis.com/auth/drive"]
        creds, project_id = default(scopes=scopes)
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        # Usamos el mimetype que viene de WhatsApp (ej: 'application/pdf' o 'image/png')
        media = MediaIoBaseUpload(
            io.BytesIO(file_bytes), 
            mimetype=mimetype, 
            resumable=False
        )

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink',
            supportsAllDrives=True 
        ).execute()

        # Permisos para que sea consultable
        service.permissions().create(
            fileId=file.get('id'),
            body={'type': 'anyone', 'role': 'viewer'}
        ).execute()

        logging.info(f"Archivo subido correctamente: {filename} ({mimetype})")
        return file.get('webViewLink')

    except Exception as e:
        logging.error(f"Error subiendo a Google Drive: {e}")
        return None
