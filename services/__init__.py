"""Handles the main business logic by orchestrating calls to various services."""

import logging
import json
from datetime import datetime
from typing import Optional, Tuple

# Import service modules
from . import ai_service
from . import google_service
from . import whatsapp_service

# Initialize the AI client once
client = ai_service.initialize_gemini()

def handle_whatsapp_message(data: dict):
    """Main handler for incoming WhatsApp messages."""
    try:
        message_data = data['entry'][0]['changes'][0]['value']['messages'][0]
        sender_phone = message_data['from']
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message_type = message_data.get('type')

        image_bytes = None
        ai_response = None

        if message_type == 'text':
            message_text = message_data['text']['body']
            logging.info(f"Received text message: '{message_text}' from {sender_phone}")
            ai_response = ai_service.process_with_gemini(client, message_text)
        elif message_type == 'image':
            image_id = message_data['image']['id']
            caption = message_data['image'].get('caption', '')
            logging.info(f"Received image with caption: '{caption}' from {sender_phone}")
            ai_response, image_bytes = process_image_message(sender_phone, image_id, caption, timestamp)
        else:
            logging.warning(f"Unsupported message type: {message_type}")

        handle_ai_response(timestamp, sender_phone, ai_response, image_bytes)

    except (KeyError, IndexError) as e:
        logging.error(f"Could not parse WhatsApp webhook payload: {e}")
        logging.error(f"Received data: {data}")

def process_image_message(sender_phone: str, image_id: str, caption: str, timestamp: str) -> Tuple[Optional[str], Optional[bytes]]:
    """Processes an image message by coordinating WhatsApp and AI services."""
    media_url = whatsapp_service.get_image_url(image_id)
    if not media_url:
        # Consider sending a WhatsApp message back to the user
        return None, None

    image_bytes = whatsapp_service.download_image_content(media_url)
    if not image_bytes:
        # Consider sending a WhatsApp message back to the user
        return None, None
        
    return ai_service.process_with_gemini(client, text=caption, image_bytes=image_bytes), image_bytes

def handle_ai_response(timestamp: str, sender_phone: str, ai_response: Optional[str], image_bytes: Optional[bytes] = None):
    """Handles the response from the AI service, saving data and images."""
    if not ai_response:
        logging.warning("AI response was empty. Cannot process further.")
        # Optionally, send a failure message via WhatsApp
        return

    try:
        expense_data = json.loads(ai_response)
        folder = expense_data.get('folder', 'Unknown')
        link_drive = ""

        if image_bytes:
            # The image_id is not available here, generate a filename
            file_name = f"upload_{timestamp.replace(' ', '_').replace(':', '-')}.jpg"
            link_drive = google_service.save_image(image_bytes, folder, file_name)

        # Prepare the row for Google Sheets
        row_to_add = [
            timestamp,
            sender_phone,
            expense_data.get('date', ''),
            expense_data.get('concept', ''),
            expense_data.get('amount', ''),
            expense_data.get('category', ''),
            expense_data.get('currency', ''),
            folder,
            link_drive
        ]
        
        google_service.add_row_to_sheet(row_to_add)
        
        # Optionally, send a success message via WhatsApp
        # whatsapp_service.send_whatsapp_message(to=sender_phone, message="Data processed successfully.")

    except json.JSONDecodeError:
        logging.error(f"Could not parse AI response as JSON: {ai_response}")
    except Exception as e:
        logging.error(f"An error occurred during data preparation: {e}")
