"""Handles interactions with the WhatsApp Cloud API."""

import logging
import os
import requests
from typing import Optional


def get_media_url(media_id: str) -> Optional[str]:
    """Retrieves the media URL from Meta's servers.

    Args:
        media_id: The ID of the media to retrieve.

    Returns:
        The media URL, or None if an error occurs.
    """
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    url = f"https://graph.facebook.com/v19.0/{media_id}"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("url")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting media URL: {e}")
        return None


def download_media(media_url: str) -> Optional[bytes]:
    """Downloads the media file from the given URL.

    Args:
        media_url: The URL of the media to download.

    Returns:
        The binary content of the media file, or None if an error occurs.
    """
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.get(media_url, headers=headers)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading media: {e}")
        return None


def send_whatsapp_message(to: str, message: str) -> None:
    """Sends a message to a WhatsApp user.

    Args:
        to: The recipient's phone number.
        message: The message to send.
    """
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": message},
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending WhatsApp message: {e}")
