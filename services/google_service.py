"""Handles interactions with Google Sheets and Google Drive."""

import logging
import os
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from io import BytesIO
from typing import Dict, Any, Optional


def get_google_credentials():
    """Authenticates with Google using service account credentials."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    # The service account file is expected to be in the root directory
    return Credentials.from_service_account_file(
        "service_account.json", scopes=scopes
    )


def append_to_sheet(data: Dict[str, Any]) -> None:
    """Appends a new row to the Google Sheet.

    Args:
        data: The data to append to the sheet.
    """
    creds = get_google_credentials()
    client = gspread.authorize(creds)
    sheet_name = os.getenv("GOOGLE_SHEET_NAME")
    sheet = client.open(sheet_name).sheet1

    try:
        sheet.append_row([data.get("Concept"), data.get("Amount"), data.get("Category")])
    except Exception as e:
        logging.error(f"Error appending to Google Sheet: {e}")


def upload_to_drive(file_content: bytes, filename: str) -> Optional[str]:
    """Uploads a file to a specific Google Drive folder.

    Args:
        file_content: The binary content of the file to upload.
        filename: The name of the file.

    Returns:
        The URL of the uploaded file, or None if an error occurs.
    """
    creds = get_google_credentials()
    service = build("drive", "v3", credentials=creds)
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

    file_metadata = {"name": filename, "parents": [folder_id]}
    media = MediaIoBaseUpload(
        BytesIO(file_content), mimetype="application/octet-stream", resumable=True
    )

    try:
        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="webViewLink")
            .execute()
        )
        return file.get("webViewLink")
    except Exception as e:
        logging.error(f"Error uploading to Google Drive: {e}")
        return None


def log_drive_url(drive_url: str) -> None:
    """Logs the Google Drive URL in the Google Sheet.

    Args:
        drive_url: The URL of the file in Google Drive.
    """
    creds = get_google_credentials()
    client = gspread.authorize(creds)
    sheet_name = os.getenv("GOOGLE_SHEET_NAME")
    sheet = client.open(sheet_name).sheet1

    try:
        sheet.append_row(["Image", "", "", drive_url])
    except Exception as e:
        logging.error(f"Error logging Drive URL to Google Sheet: {e}")
