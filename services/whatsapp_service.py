"""Handles all interactions with the WhatsApp Business API."""

import logging
import requests
from typing import Optional

from .secrets import get_secret

# --- WhatsApp Business API Functions ---

def send_whatsapp_message(to: str, message: str):
    """Sends a WhatsApp message using the Meta Graph API."""
    access_token = get_secret("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = get_secret("WHATSAPP_PHONE_NUMBER_ID")
    
    if not all([access_token, phone_number_id]):
        logging.error("WhatsApp API credentials could not be retrieved from Secret Manager.")
        return

    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": message}
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
        logging.info(f"WhatsApp message sent to {to}. Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending WhatsApp message: {e}")

def get_media_url(media_id: str) -> Optional[str]:
    """Sirve para cualquier archivo: imagen, PDF, video, etc."""
    access_token = get_secret("WHATSAPP_ACCESS_TOKEN")
    if not access_token:
        logging.error("WHATSAPP_ACCESS_TOKEN could not be retrieved from Secret Manager.")
        return None
    
    # El endpoint es el mismo para todos los tipos de media
    url = f"https://graph.facebook.com/v20.0/{media_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("url")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting media URL ({media_id}): {e}")
        return None

def download_media_content(media_url: str) -> Optional[bytes]:
    """Downloads the raw bytes of a media file from the given URL."""
    access_token = get_secret("WHATSAPP_ACCESS_TOKEN")
    if not access_token:
        logging.error("WHATSAPP_ACCESS_TOKEN could not be retrieved for media download.")
        return None
        
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        # Importante: WhatsApp requiere el token incluso para la descarga del binario
        response = requests.get(media_url, headers=headers)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading media content: {e}")
        return None
