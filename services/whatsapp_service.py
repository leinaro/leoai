"""Handles all interactions with the WhatsApp Business API."""

import os
import logging
import requests
from typing import Optional

# --- WhatsApp Business API Functions ---

def send_whatsapp_message(to: str, message: str):
    """Sends a WhatsApp message using the Meta Graph API."""
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    
    if not all([access_token, phone_number_id]):
        logging.error("WhatsApp API credentials not found in environment variables.")
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

def get_image_url(image_id: str) -> Optional[str]:
    """Retrieves the media URL of an image from the WhatsApp API."""
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    if not access_token:
        logging.error("WHATSAPP_ACCESS_TOKEN not found.")
        return None
    url = f"https://graph.facebook.com/v20.0/{image_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        media_data = response.json()
        return media_data.get("url")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting image URL: {e}")
        return None

def download_image_content(media_url: str) -> Optional[bytes]:
    """Downloads the content of an image from its media URL."""
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    if not access_token:
        logging.error("WHATSAPP_ACCESS_TOKEN not found.")
        return None
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(media_url, headers=headers)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading image content: {e}")
        return None
