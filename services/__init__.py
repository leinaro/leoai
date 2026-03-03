"""Handles the main business logic by orchestrating calls to various services."""

import logging
import json
from datetime import datetime
from typing import Optional, Tuple

from . import ai_service
from . import google_service
from . import whatsapp_service
from . import app_service

from utils.errors import UnAuthorizedUserException
from utils.errors import AIProccesingException

def handle_whatsapp_message(data: dict):
    """Main handler for incoming WhatsApp messages."""
    try:
        message_data = data['entry'][0]['changes'][0]['value']['messages'][0]
        sender_phone = message_data['from']
        
        logging.debug(f"Validando usuario {sender_phone}" )
        app_service.validate_allowed_users(sender_phone)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message_type = message_data.get('type')

        file_bytes = None
        mimetype = None
        ai_response = None

        if message_type == 'text':
            ai_response = app_service.handle_text_message(message_data)

        elif message_type in ['image', 'document']:
            ai_response, file_bytes = app_service.handle_message_with_attachement(message_data, message_type)
    
        else:
            logging.warning(f"Unsupported message type: {message_type}")

        handle_ai_response(timestamp, sender_phone, ai_response, file_bytes, mimetype)

    except UnAuthorizedUserException as e:
        whatsapp_service.send_whatsapp_message(sender_phone, "Lo siento, no eres un usuario autorizado para usar este chat.")
    except AIProccesingException as e:
        whatsapp_service.send_whatsapp_message(sender_phone, "Lo siento, no pude procesar tu mensaje.")
    except (KeyError, IndexError) as e:
        logging.error(f"Could not parse WhatsApp webhook payload: {e}")
        logging.error(f"Received data: {data}")
        whatsapp_service.send_whatsapp_message(sender_phone, "❌ Could not parse WhatsApp webhook payload.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        whatsapp_service.send_whatsapp_message(sender_phone, "❌ Lo siento, al raro paso.")

def handle_ai_response(
    timestamp: str, 
    sender_phone: str, 
    ai_response: Optional[str], 
    file_bytes: Optional[bytes] = None,
    mimetype: Optional[str] = None
):
    """Handles the response from the AI service, saving data and images."""
    if not ai_response:
        logging.warning("AI response was empty. Cannot process further.")
        whatsapp_service.send_whatsapp_message(sender_phone, "❌ AI response was empty. Cannot process further.")
        return

    try:
        logging.info(f"AI response: {ai_response}")
        print(f"AI response: {ai_response}")

        expense_data = json.loads(ai_response)

        logging.info("expense_data")

        valid_expense = expense_data.get('valid_expense') or False
        if not valid_expense:
            logging.warning("Invalid expense. Not saving to Google Sheets.")
            error_message = expense_data.get('message') or "❌ Invalid expense. Not saving to Google Sheets."
            whatsapp_service.send_whatsapp_message(sender_number, error_message)

        format_date = datetime.now().strftime("%Y-%m-%d")
        date_for_drive = expense_data.get('date') or format_date
        folder = expense_data.get('folder', 'Unknown')
        concept = expense_data.get('concept', '')
    
        link_drive = ""

            
        if file_bytes and mimetype:
            ext = ".pdf" if "pdf" in mimetype else ".jpg"
            
            clean_concept = str(concept).replace(" ", "_")[:20] # Limitamos largo
            file_name = f"{folder}_{clean_concept}_{str(timestamp).replace(' ', '_').replace(':', '-')}{ext}"

            link_drive = google_service.save_file(file_bytes, timestamp, file_name, mimetype)

        # Prepare the row for Google Sheets
        # Date	Concept	Amount	Currency	Category	Subcategory	Sender	Timestamp
        
        row_to_add = [
            date_for_drive,         # C: Fecha de la factura (extraída por IA)
            concept,                # D: Concepto
            expense_data.get('amount', ''),
            expense_data.get('currency', ''),
            expense_data.get('category', ''),
            expense_data.get('subcategory', ''),
            sender_phone,           # B: Quién lo envió
            timestamp,              # A: Cuándo se envió el mensaje
            link_drive              # I: Link directo al archivo
        ]
        logging.info(f"row_to_add {row_to_add}")

        
        google_service.add_row_to_sheet(row_to_add)
        
        # Optionally, send a success message via WhatsApp
        logging.info(f"✅ Transacción registrada: {concept} - {folder}")
        print(f"✅ Transacción registrada: {concept} - {folder}")

        mensaje = (
                f"📝 ¡Listo! Se creó exitosamente una entrada con concepto '{concept}', "
                f"fecha {date_for_drive}, "
                f"valor {expense_data.get('amount', 0.0)} {expense_data.get('currency', '')}, "
                f"categoría '{expense_data.get('category', '')}', "
                f"subcategoría '{expense_data.get('subcategory', '')}'. "
                )

        whatsapp_service.send_whatsapp_message(sender_phone, mensaje)

    except json.JSONDecodeError:
        logging.error(f"Could not parse AI response as JSON: {ai_response}")
        whatsapp_service.send_whatsapp_message(sender_phone, "❌ Could not parse AI response as JSON")
    except Exception as e:
        logging.error(f"An error occurred during data preparation: {e}")
        whatsapp_service.send_whatsapp_message(sender_phone, "❌ An error occurred during data preparation:")